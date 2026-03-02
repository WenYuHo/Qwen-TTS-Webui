import os
import json
import uuid
import torch
import numpy as np
import soundfile as sf
import librosa
import logging
import threading
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydub import AudioSegment
from deep_translator import GoogleTranslator

from .qwen_tts.inference.qwen3_tts_model import VoiceClonePromptItem
from .model_loader import get_model
from .config import BASE_DIR, logger
from .video_engine import VideoEngine
from .utils import phoneme_manager, AudioPostProcessor, Profiler

from concurrent.futures import ThreadPoolExecutor
import queue

class PodcastEngine:
    def __init__(self):
        self.upload_dir = Path("uploads").resolve()
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.executor = ThreadPoolExecutor(max_workers=4)
        # Caches
        self.preset_embeddings = {}
        self.clone_embedding_cache = {}
        self.mix_embedding_cache = {}
        self.bgm_cache = {}
        self.prompt_cache = {}
        self.transcription_cache = {}
        self.translation_cache = {}
        self.video_audio_cache = {}

        self._whisper_model = None # Lazy load

    def _resolve_paths(self, relative_path: str) -> List[Path]:
        """Resolve one or more relative paths against upload_dir and ensure safety."""
        if not relative_path:
            return []
        paths = relative_path.split("|")
        resolved = []
        for p in paths:
            path_obj = Path(p)
            if not path_obj.is_absolute():
                path_obj = (self.upload_dir / path_obj).resolve()
            else:
                path_obj = path_obj.resolve()

            is_safe = path_obj.is_relative_to(self.upload_dir)
            if not is_safe:
                bgm_dir = (Path(BASE_DIR) / "bgm").resolve()
                is_safe = path_obj.is_relative_to(bgm_dir)
            if not is_safe:
                video_dir = (Path(BASE_DIR) / "projects" / "videos").resolve()
                is_safe = path_obj.is_relative_to(video_dir)
            if not is_safe:
                from .config import SHARED_ASSETS_DIR
                is_safe = path_obj.is_relative_to(SHARED_ASSETS_DIR.resolve())

            if not is_safe:
                logger.error(f"Access denied to path: {path_obj}")
                raise PermissionError(f"Access denied to path outside allowed directories")
            resolved.append(path_obj)
        return resolved

    def _get_model_type_for_profile(self, profile: Dict[str, Any]) -> str:
        ptype = profile.get("type")
        if ptype == "preset": return "CustomVoice"
        if ptype == "design": return "VoiceDesign"
        return "Base"

    def get_system_status(self) -> Dict[str, Any]:
        return {
            "status": "ready",
            "device": "cuda" if torch.cuda.is_available() else "cpu",
            "models_loaded": list(self.prompt_cache.keys())
        }

    def _extract_audio_with_cache(self, video_path: str) -> str:
        if video_path in self.video_audio_cache:
            cached_path = self.video_audio_cache[video_path]
            if Path(cached_path).exists():
                return cached_path
        extracted_path = VideoEngine.extract_audio(video_path)
        self.video_audio_cache[video_path] = extracted_path
        return extracted_path

    def stream_podcast(self, script: List[Dict[str, Any]], profiles: Dict[str, Dict[str, Any]], eq_preset: str = "flat", reverb_level: float = 0.0):
        """Yields synthesized audio blocks sequentially for low-latency podcast playback."""
        for item in script:
            try:
                role = item["role"]
                profile = profiles.get(role, {"type": "preset", "value": "Ryan"})
                text = phoneme_manager.apply(item["text"])
                wav, sr = self.generate_segment(text, profile, language=item.get("language", "auto"), instruct=item.get("instruct"))
                wav = AudioPostProcessor.apply_eq(wav, sr, preset=eq_preset)
                wav = AudioPostProcessor.apply_reverb(wav, sr, intensity=reverb_level)
                yield wav, sr, item
            except Exception as e:
                logger.error(f"Streaming podcast block failed: {e}")
                continue

    def transcribe_audio(self, audio_path: str) -> str:
        resolved = self._resolve_paths(audio_path)
        actual_path = str(resolved[0])
        if VideoEngine.is_video(actual_path):
            actual_path = self._extract_audio_with_cache(actual_path)
        try:
            path_obj = Path(actual_path)
            if path_obj.exists():
                stat = path_obj.stat()
                cache_key = f"{actual_path}:{stat.st_size}:{stat.st_mtime}"
                if cache_key in self.transcription_cache:
                    return self.transcription_cache[cache_key]
        except Exception: pass
        if self._whisper_model is None:
            import whisper
            self._whisper_model = whisper.load_model("base")
        result = self._whisper_model.transcribe(actual_path)
        text = result["text"]
        return text

    def get_speaker_embedding(self, profile: Dict[str, str], model: Optional[Any] = None) -> Optional[torch.Tensor]:
        ptype = profile.get("type")
        if ptype == "preset":
            name = profile["value"].lower()
            if name in self.preset_embeddings: return self.preset_embeddings[name]
        elif ptype == "clone":
            cache_key = profile["value"]
            if cache_key in self.prompt_cache: return self.prompt_cache[cache_key][0].ref_spk_embedding
            if cache_key in self.clone_embedding_cache: return self.clone_embedding_cache[cache_key]
        if model is None:
            mtype = "Base" if ptype == "clone" else "CustomVoice"
            model = get_model(mtype)
        if ptype == "preset":
            emb = model.get_speaker_embedding(profile["value"])
            self.preset_embeddings[profile["value"].lower()] = emb
            return emb
        elif ptype == "clone":
            cache_key = profile["value"]
            resolved = self._resolve_paths(cache_key)
            clone_path = str(resolved[0])
            if VideoEngine.is_video(clone_path): clone_path = self._extract_audio_with_cache(clone_path)
            prompt = model.create_voice_clone_prompt(ref_audio=clone_path, x_vector_only_mode=True)
            emb = prompt[0].ref_spk_embedding
            self.prompt_cache[cache_key] = prompt
            self.clone_embedding_cache[cache_key] = emb
            return emb
        return None

    def _apply_audio_watermark(self, wav: np.ndarray, sr: int) -> np.ndarray:
        try:
            from .api.system import _settings
            if not _settings.watermark_audio: return wav
            duration = 0.1
            t = np.linspace(0, duration, int(sr * duration), False)
            tone = 0.05 * np.sin(2 * np.pi * 20000 * t)
            fade = int(sr * 0.01)
            tone[:fade] *= np.linspace(0, 1, fade)
            tone[-fade:] *= np.linspace(1, 0, fade)
            return np.concatenate([wav, tone])
        except Exception: return wav

    def generate_segment(self, text: str, profile: Dict[str, Any], language: str = "auto", model: Optional[Any] = None, instruct: Optional[str] = None) -> tuple[np.ndarray, int]:
        try:
            text = phoneme_manager.apply(text)
            final_instruct = instruct or profile.get("instruct")
            if profile["type"] == "preset":
                if model is None: model = get_model("CustomVoice")
                wavs, sr = model.generate_custom_voice(text=text, speaker=profile["value"], language=language, instruct=final_instruct)
            elif profile["type"] == "design":
                if model is None: model = get_model("VoiceDesign")
                design_instruct = profile["value"]
                if final_instruct: design_instruct = f"{design_instruct}, {final_instruct}"
                wavs, sr = model.generate_voice_design(text=text, instruct=design_instruct, language=language, non_streaming_mode=True)
            elif profile.get("type") == "clone":
                cache_key = profile["value"]
                if cache_key in self.prompt_cache: prompt = self.prompt_cache[cache_key]
                else:
                    resolved_paths = self._resolve_paths(profile["value"])
                    if model is None: model = get_model("Base")
                    ref_audio = str(resolved_paths[0])
                    if VideoEngine.is_video(ref_audio): ref_audio = self._extract_audio_with_cache(ref_audio)
                    prompt = model.create_voice_clone_prompt(ref_audio=ref_audio, x_vector_only_mode=True)
                    self.prompt_cache[cache_key] = prompt
                if model is None: model = get_model("Base")
                wavs, sr = model.generate_voice_clone(text=text, language=language, voice_clone_prompt=prompt, instruct=final_instruct)
            elif profile.get("type") == "mix":
                cache_key = f"mix:{profile['value']}"
                if cache_key in self.prompt_cache: prompt = self.prompt_cache[cache_key]
                else:
                    mix_configs = json.loads(profile["value"])
                    mixed_emb = self._compute_mixed_embedding(mix_configs)
                    prompt = [VoiceClonePromptItem(ref_code=None, ref_spk_embedding=mixed_emb, x_vector_only_mode=True, icl_mode=False, ref_text=None)]
                    self.prompt_cache[cache_key] = prompt
                if model is None: model = get_model("Base")
                wavs, sr = model.generate_voice_clone(text=text, language=language, voice_clone_prompt=prompt, instruct=final_instruct)
            if not wavs: raise RuntimeError("No waveforms")
            return self._apply_audio_watermark(wavs[0], sr), sr
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            raise

    def _compute_mixed_embedding(self, mix_configs: List[Dict[str, Any]], model: Optional[Any] = None) -> Optional[torch.Tensor]:
        cache_key = json.dumps(sorted(mix_configs, key=lambda x: str(x["profile"])), sort_keys=True)
        if cache_key in self.mix_embedding_cache: return self.mix_embedding_cache[cache_key]
        total_weight = sum(c["weight"] for c in mix_configs)
        if total_weight == 0: return None
        mixed_emb = None
        for config in mix_configs:
            emb = self.get_speaker_embedding(config["profile"], model=model)
            weight = config["weight"] / total_weight
            if mixed_emb is None: mixed_emb = emb * weight
            else: mixed_emb += emb * weight
        self.mix_embedding_cache[cache_key] = mixed_emb
        return mixed_emb

    def stream_synthesize(self, text: str, profile: Dict[str, Any], language: str = "auto", instruct: Optional[str] = None):
        import re
        chunks = re.split(r'([.!?。！？\n]+)', text)
        processed_chunks = []
        for i in range(0, len(chunks)-1, 2):
            c = chunks[i] + chunks[i+1]
            if c.strip(): processed_chunks.append(c.strip())
        if len(chunks) % 2 == 1 and chunks[-1].strip(): processed_chunks.append(chunks[-1].strip())
        if not processed_chunks: processed_chunks = [text]
        futures = [self.executor.submit(self.generate_segment, chunk_text, profile, language, None, instruct) for chunk_text in processed_chunks]
        for f in futures:
            try:
                wav, sr = f.result()
                yield wav, sr
            except Exception: continue

    def generate_voice_changer(self, source_audio: str, target_profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        text = self.transcribe_audio(source_audio)
        resolved = self._resolve_paths(source_audio)
        source_path = str(resolved[0])
        if VideoEngine.is_video(source_path): source_path = self._extract_audio_with_cache(source_path)
        model = get_model("Base")
        prompt_items = model.create_voice_clone_prompt(ref_audio=source_path, ref_text=text, x_vector_only_mode=False)
        target_emb = self.get_speaker_embedding(target_profile or {"type": "preset", "value": "Ryan"})
        voice_clone_prompt = {"ref_code": [prompt_items[0].ref_code], "ref_spk_embedding": [target_emb], "x_vector_only_mode": [False], "icl_mode": [True]}
        wavs, sr = model.generate_voice_clone(text=text, voice_clone_prompt=voice_clone_prompt)
        return {"waveform": wavs[0], "sample_rate": sr, "text": text}

    def generate_podcast(self, script: List[Dict[str, Any]], profiles: Dict[str, Dict[str, Any]], bgm_mood: Optional[str] = None, ducking_level: float = 0.0, eq_preset: str = "flat", reverb_level: float = 0.0) -> Optional[Dict[str, Any]]:
        with Profiler("Generate Podcast"):
            sample_rate = 24000
            waveforms = [None] * len(script)
            srs = [None] * len(script)
            for i, item in enumerate(script):
                try:
                    wav, sr = self.generate_segment(item["text"], profile=profiles.get(item["role"]), language=item.get("language", "auto"), instruct=item.get("instruct"))
                    waveforms[i], srs[i] = wav, sr
                except Exception: continue
            speech_segments = []
            max_sample = 0
            current_sample_offset = 0
            for i, item in enumerate(script):
                if waveforms[i] is None: continue
                wav, sr = waveforms[i], srs[i]
                start_sample = current_sample_offset
                end_sample = start_sample + len(wav)
                speech_segments.append({"wav": wav, "start": start_sample, "end": end_sample})
                current_sample_offset = end_sample + int(item.get("pause_after", 0.5) * sr)
                if end_sample > max_sample: max_sample = end_sample
            if not speech_segments: return None
            final_wav = np.zeros(max_sample + int(2.0 * sample_rate), dtype=np.float32)
            for seg in speech_segments: final_wav[seg["start"]:seg["end"]] = seg["wav"]
            if bgm_mood:
                try:
                    bgm_full_path = (Path(BASE_DIR) / "bgm" / f"{bgm_mood}.mp3").resolve()
                    if bgm_full_path.exists():
                        bgm_audio = AudioSegment.from_file(bgm_full_path).set_frame_rate(sample_rate).set_channels(1)
                        bgm_samples = np.array(bgm_audio.get_array_of_samples(), dtype=np.float32) / 32768.0 * 0.1
                        if len(bgm_samples) < len(final_wav): bgm_samples = np.tile(bgm_samples, int(np.ceil(len(final_wav)/len(bgm_samples))))
                        bgm_samples = bgm_samples[:len(final_wav)]
                        if ducking_level > 0:
                            duck_factor = 10 ** (-(ducking_level * 25) / 20.0)
                            for seg in speech_segments: bgm_samples[seg["start"]:seg["end"]] *= duck_factor
                        final_wav += bgm_samples
                except Exception: pass
            max_val = np.max(np.abs(final_wav))
            if max_val > 1.0: final_wav /= max_val
            final_wav = AudioPostProcessor.apply_eq(final_wav, sample_rate, preset=eq_preset)
            final_wav = AudioPostProcessor.apply_reverb(final_wav, sample_rate, intensity=reverb_level)
            return {"waveform": final_wav, "sample_rate": sample_rate}

    def dub_audio(self, audio_path: str, target_lang: str) -> Optional[Dict[str, Any]]:
        text = self.transcribe_audio(audio_path)
        trans_lang = 'zh-CN' if target_lang == 'zh' else target_lang
        translated_text = GoogleTranslator(source='auto', target=trans_lang).translate(text)
        wav, sr = self.generate_segment(translated_text, profile={"type": "clone", "value": audio_path}, language=target_lang)
        return {"waveform": wav, "sample_rate": sr, "text": translated_text}
