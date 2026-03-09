import numpy as np
import torch
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from ..config import BASE_DIR, SHARED_ASSETS_DIR, logger
from ..utils import AudioPostProcessor, prune_dict_cache
from pydub import AudioSegment

class PodcastPatcher:
    def __init__(self, bgm_cache, bgm_dir, shared_assets_dir):
        self.bgm_cache = bgm_cache
        self.bgm_dir = bgm_dir
        self.shared_assets_dir = shared_assets_dir

    def load_bgm(self, bgm_mood: str, sample_rate: int, max_sample: int, ducking_level: float, is_stereo: bool, speech_segments: list) -> Optional[np.ndarray]:
        try:
            if bgm_mood in self.bgm_cache:
                bgm_samples = self.bgm_cache[bgm_mood]
                if ducking_level > 0:
                    bgm_samples = bgm_samples.copy()
            else:
                bgm_full_path = (self.bgm_dir / f"{bgm_mood}.mp3").resolve()
                if not bgm_full_path.exists():
                    bgm_full_path = Path(bgm_mood).resolve()
                    if not bgm_full_path.exists():
                        bgm_full_path = (self.shared_assets_dir / bgm_mood).resolve()

                if bgm_full_path.exists() and bgm_full_path.is_file():
                    prune_dict_cache(self.bgm_cache, limit=50, count=5)
                    bgm_audio = AudioSegment.from_file(bgm_full_path).set_frame_rate(sample_rate).set_channels(1)
                    bgm_samples = np.array(bgm_audio.get_array_of_samples(), dtype=np.float32) / 32768.0 * 0.1
                    bgm_samples = np.squeeze(bgm_samples)
                    self.bgm_cache[bgm_mood] = bgm_samples.copy()
                else:
                    return None

            if bgm_samples is not None:
                if len(bgm_samples) < (max_sample + int(2.0 * sample_rate)):
                    bgm_samples = np.tile(bgm_samples, int(np.ceil((max_sample + int(2.0 * sample_rate))/len(bgm_samples))))
                bgm_samples = bgm_samples[:(max_sample + int(2.0 * sample_rate))]
                
                if ducking_level > 0:
                    duck_factor = 10 ** (-(ducking_level * 25) / 20.0)
                    for seg in speech_segments: 
                        # To support both 1D (mono bgm) and 2D (stereo bgm), handle shapes explicitly
                        if len(bgm_samples.shape) == 1:
                            bgm_samples[seg["start"]:seg["end"]] *= duck_factor
                        else:
                            bgm_samples[:, seg["start"]:seg["end"]] *= duck_factor
                
                return bgm_samples
        except Exception as e:
            logger.error(f"Failed to apply BGM: {e}")
            return None

    def construct_timeline(self, script: List[Dict[str, Any]], waveforms: List[np.ndarray], srs: List[int], sample_rate: int, is_stereo_required: bool = False) -> tuple[np.ndarray, int, list]:
        speech_segments = []
        max_sample = 0
        current_sample_offset = 0
        for i, item in enumerate(script):
            if waveforms[i] is None: continue
            wav, sr = waveforms[i], srs[i]
            start_sample = current_sample_offset
            end_sample = start_sample + len(wav)
            speech_segments.append({"wav": wav, "start": start_sample, "end": end_sample, "index": i})
            current_sample_offset = end_sample + int(item.get("pause_after", 0.5) * sr)
            if end_sample > max_sample: max_sample = end_sample

        is_stereo = any(s.get("pan", 0) != 0 for s in script) or is_stereo_required
        
        if is_stereo:
            final_wav = np.zeros((2, max_sample + int(2.0 * sample_rate)), dtype=np.float32)
        else:
            final_wav = np.zeros(max_sample + int(2.0 * sample_rate), dtype=np.float32)

        for seg in speech_segments:
            wav = seg["wav"]
            pan = script[seg["index"]].get("pan", 0.0)
            if is_stereo:
                segment_stereo = AudioPostProcessor.apply_panning(wav, pan)
                final_wav[:, seg["start"]:seg["end"]] = segment_stereo
            else:
                final_wav[seg["start"]:seg["end"]] = wav

        return final_wav, max_sample, speech_segments

    def apply_mastering(self, final_wav: np.ndarray, sample_rate: int, eq_preset: str, reverb_level: float, master_acx: bool) -> np.ndarray:
        # 1. Initial peak normalization if needed
        max_val = max(np.max(final_wav), -np.min(final_wav))
        if max_val > 1.0: final_wav /= max_val

        # 2. Cleanup & Effects
        final_wav = AudioPostProcessor.apply_declick(final_wav, sample_rate)
        final_wav = AudioPostProcessor.apply_eq(final_wav, sample_rate, preset=eq_preset)
        final_wav = AudioPostProcessor.apply_reverb(final_wav, sample_rate, intensity=reverb_level)
        
        # 3. Final Dynamics & Loudness
        if master_acx:
            # ACX specific path (RMS focused)
            final_wav = AudioPostProcessor.apply_compressor(final_wav, sample_rate, threshold_db=-20.0, ratio=4.0)
            final_wav = AudioPostProcessor.normalize_acx(final_wav)
        else:
            # Modern standard path (LUFS focused)
            # Normalize to podcast standard -16 LUFS
            final_wav = AudioPostProcessor.normalize_lufs(final_wav, sample_rate, target_lufs=-16.0)
            # Final limiter at -1dB
            final_wav = AudioPostProcessor.apply_limiter(final_wav, threshold=0.89)

        return final_wav
