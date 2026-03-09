import os
import json
import uuid
import re
import hashlib
import torch
import numpy as np
import soundfile as sf
import librosa
import logging
import threading
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

from .config import BASE_DIR, SHARED_ASSETS_DIR, VIDEO_DIR, logger
from pydub import AudioSegment
from deep_translator import GoogleTranslator

from .qwen_tts.inference.qwen3_tts_model import VoiceClonePromptItem
from .model_loader import get_model
from .video_engine import VideoEngine
from .utils import phoneme_manager, AudioPostProcessor, Profiler, prune_dict_cache, audit_manager

from concurrent.futures import ThreadPoolExecutor
import queue

from .engine_modules.segmenter import TextSegmenter
from .engine_modules.synthesizer import VoiceSynthesizer
from .engine_modules.patcher import PodcastPatcher

# ⚡ Bolt: Global cache for audio watermark tone to avoid redundant math and allocations
_watermark_tone_cache = {}
# ⚡ Bolt: Reference to system settings to avoid redundant circular-import-safe lookups
_system_settings = None

class PodcastEngine:
    def __init__(self):
        self.upload_dir = Path("uploads").resolve()
        self.upload_dir.mkdir(parents=True, exist_ok=True)

        # ⚡ Bolt: Pre-resolve base directories once during init to avoid redundant filesystem I/O in _resolve_paths
        self._bgm_dir = (Path(BASE_DIR) / "bgm").resolve()
        self._video_dir = Path(VIDEO_DIR).resolve()
        self._shared_assets_dir = Path(SHARED_ASSETS_DIR).resolve()

        from .utils.cache import DiskCache, HybridCache
        from .config import CACHE_DIR

        self.executor = ThreadPoolExecutor(max_workers=4)
        # Caches
        self.preset_embeddings = HybridCache(DiskCache(CACHE_DIR, "preset_embeddings"))
        self.clone_embedding_cache = HybridCache(DiskCache(CACHE_DIR, "clone_embeddings"))
        self.mix_embedding_cache = HybridCache(DiskCache(CACHE_DIR, "mix_embeddings"))
        self.bgm_cache = {}
        self.prompt_cache = {}
        self.transcription_cache = HybridCache(DiskCache(CACHE_DIR, "transcriptions"))
        self.translation_cache = HybridCache(DiskCache(CACHE_DIR, "translations"))
        self.video_audio_cache = {}

        self.synthesizer = VoiceSynthesizer(
            self.upload_dir, self.transcription_cache, self.translation_cache,
            self.prompt_cache, self.clone_embedding_cache, self.preset_embeddings,
            self.mix_embedding_cache, self.video_audio_cache,
            self._resolve_paths, self._extract_audio_with_cache
        )
        self.patcher = PodcastPatcher(self.bgm_cache, self._bgm_dir, self._shared_assets_dir)

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

            # ⚡ Bolt: Use pre-resolved base directories for O(1) safety checks without further I/O
            is_safe = (
                path_obj.is_relative_to(self.upload_dir) or
                path_obj.is_relative_to(self._bgm_dir) or
                path_obj.is_relative_to(self._video_dir) or
                path_obj.is_relative_to(self._shared_assets_dir)
            )

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

        # ⚡ Bolt: Prevent unbounded growth of the video audio cache
        prune_dict_cache(self.video_audio_cache, limit=100, count=10)

        extracted_path = VideoEngine.extract_audio(video_path)
        self.video_audio_cache[video_path] = extracted_path
        return extracted_path

    def stream_podcast(self, script: List[Dict[str, Any]], profiles: Dict[str, Dict[str, Any]], eq_preset: str = "flat", reverb_level: float = 0.0, temperature: Optional[float] = None):
        """Yields synthesized audio blocks sequentially for low-latency podcast playback."""
        for item in script:
            try:
                role = item["role"]
                profile = profiles.get(role, {"type": "preset", "value": "Ryan"})
                text = phoneme_manager.apply(item["text"])
                # Priority: item temperature > global temperature
                current_temp = item.get("temperature") if item.get("temperature") is not None else temperature
                wav, sr = self.generate_segment(text, profile, language=item.get("language", "auto"), instruct=item.get("instruct"), temperature=current_temp)
                wav = AudioPostProcessor.apply_eq(wav, sr, preset=eq_preset)
                wav = AudioPostProcessor.apply_reverb(wav, sr, intensity=reverb_level)
                yield wav, sr, item
            except Exception as e:
                logger.error(f"Streaming podcast block failed: {e}")
                continue

    def transcribe_audio(self, audio_path: str) -> Dict[str, Any]:
        """Transcribe audio and return text, detected language, and segments."""
        resolved = self._resolve_paths(audio_path)
        actual_path = str(resolved[0])
        if VideoEngine.is_video(actual_path):
            actual_path = self._extract_audio_with_cache(actual_path)

        path_obj = Path(actual_path)
        cache_key = None
        if path_obj.exists():
            try:
                stat = path_obj.stat()
                cache_key = f"{actual_path}:{stat.st_size}:{stat.st_mtime}"
                if cache_key in self.transcription_cache:
                    return self.transcription_cache[cache_key]
            except Exception: pass
        if self._whisper_model is None:
            import whisper
            self._whisper_model = whisper.load_model("base")
        
        # Whisper returns {"text": ..., "language": ..., "segments": ...}
        result = self._whisper_model.transcribe(actual_path)
        
        output = {
            "text": result.get("text", ""),
            "language": result.get("language", "unknown"),
            "segments": result.get("segments", [])
        }
        
        if cache_key:
            try:
                # ⚡ Bolt: Gradual cache pruning instead of drastic clear()
                prune_dict_cache(self.transcription_cache, limit=1000, count=100)
                self.transcription_cache[cache_key] = output
            except Exception: pass
        return output

    def get_speaker_embedding(self, profile: Dict[str, str], model: Optional[Any] = None) -> Optional[torch.Tensor]:
        return self.synthesizer.get_speaker_embedding(profile, model)

    def _apply_audio_watermark(self, wav: np.ndarray, sr: int) -> np.ndarray:
        try:
            global _system_settings
            if _system_settings is None:
                # ⚡ Bolt: Circular-safe import for settings
                from .api import system as system_api
                _system_settings = system_api._settings

            if not _system_settings.watermark_audio:
                return wav

            # ⚡ Bolt: Use a multi-channel cache for the watermark tone to avoid redundant np.stack calls.
            # Keyed by (sample_rate, num_channels)
            is_stereo = len(wav.shape) == 2
            channels = 2 if is_stereo else 1
            cache_key = (sr, channels)

            if cache_key in _watermark_tone_cache:
                tone_to_use = _watermark_tone_cache[cache_key]
            else:
                # First ensure mono tone for this SR is cached
                if (sr, 1) not in _watermark_tone_cache:
                    duration = 0.1
                    t = np.linspace(0, duration, int(sr * duration), False)
                    tone = 0.05 * np.sin(2 * np.pi * 20000 * t)
                    fade = int(sr * 0.01)
                    tone[:fade] *= np.linspace(0, 1, fade)
                    tone[-fade:] *= np.linspace(1, 0, fade)
                    _watermark_tone_cache[(sr, 1)] = tone

                if channels == 2:
                    mono_tone = _watermark_tone_cache[(sr, 1)]
                    tone_to_use = np.stack([mono_tone, mono_tone])
                    _watermark_tone_cache[cache_key] = tone_to_use
                else:
                    tone_to_use = _watermark_tone_cache[(sr, 1)]

            if is_stereo:
                return np.concatenate([wav, tone_to_use], axis=1)
            else:
                return np.concatenate([wav, tone_to_use])
        except Exception:
            return wav

    def _validate_ref_audio(self, audio_path: str) -> None:
        """Validate reference audio for cloning: duration, silence, format."""
        import soundfile as sf
        try:
            info = sf.info(audio_path)
            duration = info.duration
            if duration < 3.0:
                raise ValueError(f"Reference audio too short ({duration:.1f}s). Minimum 3 seconds required.")
            if duration > 30.0:
                raise ValueError(f"Reference audio too long ({duration:.1f}s). Maximum 30 seconds recommended for best quality.")
            
            # Check for silence-only input
            audio_data, sr = sf.read(audio_path)
            rms = np.sqrt(np.mean(audio_data ** 2))
            if rms < 0.001:  # Effectively silent
                raise ValueError("Reference audio appears to be silent. Please provide audio with speech.")
        except sf.SoundFileError as e:
            raise ValueError(f"Invalid audio file: {e}")

    @staticmethod
    def _compute_quality_score(wav: np.ndarray, sr: int) -> Dict[str, Any]:
        return VoiceSynthesizer._compute_quality_score(wav, sr)

    def generate_segment(self, text: str, profile: Dict[str, Any], language: str = "auto", model: Optional[Any] = None, instruct: Optional[str] = None, temperature: Optional[float] = None, **gen_kwargs) -> tuple[np.ndarray, int]:
        return self.synthesizer.generate_segment(text, profile, language, model, instruct, temperature, watermark_func=self._apply_audio_watermark, **gen_kwargs)

    def _compute_mixed_embedding(self, mix_configs: List[Dict[str, Any]], model: Optional[Any] = None) -> Optional[torch.Tensor]:
        cache_key = json.dumps(sorted(mix_configs, key=lambda x: str(x["profile"])), sort_keys=True)
        if cache_key in self.mix_embedding_cache: return self.mix_embedding_cache[cache_key]

        # ⚡ Bolt: Prevent unbounded growth of mixed embedding cache
        prune_dict_cache(self.mix_embedding_cache, limit=200, count=20)

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

    def stream_synthesize(self, text: str, profile: Dict[str, Any], language: str = "auto", instruct: Optional[str] = None, temperature: Optional[float] = None):
        # 1. First split by major punctuation to create sentences
        # Matches periods, exclamation, question marks, and newlines
        initial_chunks = re.split(r'([.!?。！？\n\r]+)', text)
        sentences = []
        for i in range(0, len(initial_chunks)-1, 2):
            s = initial_chunks[i] + initial_chunks[i+1]
            if s.strip(): sentences.append(s.strip())
        if len(initial_chunks) % 2 == 1 and initial_chunks[-1].strip():
            sentences.append(initial_chunks[-1].strip())
            
        # 2. Recursive split for long sentences (> 150 chars) to prevent drift
        # This prevents the attention mechanism from getting lost in extremely long clauses
        final_chunks = []
        for s in sentences:
            if len(s) > 150:
                # Try to split by commas or semi-colons
                sub = re.split(r'([,;，；])', s)
                current = ""
                for part in sub:
                    if len(current) + len(part) < 150:
                        current += part
                    else:
                        if current: final_chunks.append(current.strip())
                        current = part
                if current: final_chunks.append(current.strip())
            else:
                final_chunks.append(s)

        if not final_chunks: final_chunks = [text]
        
        # 3. Process sequentially or in small batches to maintain stability
        # Processing too many chunks in parallel can cause VRAM spikes and OOM
        # Using a generator here allows for true streaming response
        for chunk_text in final_chunks:
            try:
                # ⚡ Bolt Stability: Add a small pause or reset context if needed here
                # For now, generating segment-by-segment is safer than one huge prompt
                wav, sr = self.generate_segment(chunk_text, profile, language, None, instruct, temperature=temperature)
                yield wav, sr
            except Exception as e:
                logger.error(f"Chunk synthesis failed for '{chunk_text[:20]}...': {e}")
                continue

    def stream_voice_changer(self, source_audio: str, target_profile: Optional[Dict[str, Any]] = None, preserve_prosody: bool = True, instruct: Optional[str] = None):
        """Yields synthesized audio blocks sequentially for low-latency S2S."""
        # 1. Transcribe with segments
        result = self.transcribe_audio(source_audio)
        segments = result.get("segments", [])
        if not segments:
            # Fallback to entire text if no segments
            res = self.generate_voice_changer(source_audio, target_profile, preserve_prosody, instruct)
            yield res["waveform"], res["sample_rate"]
            return

        resolved = self._resolve_paths(source_audio)
        source_path = str(resolved[0])
        if VideoEngine.is_video(source_path):
            source_path = self._extract_audio_with_cache(source_path)

        # Load source audio once for slicing
        full_wav, sr_source = sf.read(source_path)
        if full_wav.ndim > 1:
            full_wav = np.mean(full_wav, axis=-1)

        model = get_model("Base")
        target_emb = self.get_speaker_embedding(target_profile or {"type": "preset", "value": "Ryan"})

        for seg in segments:
            try:
                text = seg["text"].strip()
                if not text: continue
                
                start_s = seg["start"]
                end_s = seg["end"]
                
                # Extract chunk for prosody reference
                # We aim for a ~3s-10s window around the segment for best prosody preservation
                # while satisfying Qwen3TTS's 3s minimum requirement.
                duration_seg = end_s - start_s
                if duration_seg < 3.0:
                    # Pad symmetrically to reach 3s
                    needed = 3.0 - duration_seg
                    start_s = max(0, start_s - needed / 2)
                    end_s = min(len(full_wav) / sr_source, start_s + 3.0)
                    # If end_s hit the boundary, adjust start_s again
                    if end_s - start_s < 3.0:
                        start_s = max(0, end_s - 3.0)
                
                start_idx = int(start_s * sr_source)
                end_idx = int(end_s * sr_source)
                chunk = full_wav[start_idx:end_idx]
                
                duration = len(chunk) / sr_source
                
                if preserve_prosody and 3.0 <= duration <= 30.0:
                    # ICL mode captures prosody via ref_code
                    prompt_items = model.create_voice_clone_prompt(ref_audio=(chunk, sr_source), ref_text=text, x_vector_only_mode=False)
                    voice_clone_prompt = {
                        "ref_code": [prompt_items[0].ref_code],
                        "ref_spk_embedding": [target_emb],
                        "x_vector_only_mode": [False],
                        "icl_mode": [True]
                    }
                else:
                    # Fallback to speaker embedding only
                    voice_clone_prompt = {
                        "ref_spk_embedding": [target_emb],
                        "x_vector_only_mode": [True],
                        "icl_mode": [False]
                    }

                wavs, sr = model.generate_voice_clone(text=text, voice_clone_prompt=voice_clone_prompt, instruct=instruct)
                yield wavs[0], sr
            except Exception as e:
                logger.error(f"S2S streaming chunk failed: {e}")
                continue

    def generate_voice_changer(self, source_audio: str, target_profile: Optional[Dict[str, Any]] = None, preserve_prosody: bool = True, instruct: Optional[str] = None) -> Dict[str, Any]:
        result = self.transcribe_audio(source_audio)
        text = result["text"]
        resolved = self._resolve_paths(source_audio)
        source_path = str(resolved[0])
        if VideoEngine.is_video(source_path): source_path = self._extract_audio_with_cache(source_path)
        model = get_model("Base")
        
        target_emb = self.get_speaker_embedding(target_profile or {"type": "preset", "value": "Ryan"})
        
        if preserve_prosody:
            # ICL mode captures prosody via ref_code
            prompt_items = model.create_voice_clone_prompt(ref_audio=source_path, ref_text=text, x_vector_only_mode=False)
            voice_clone_prompt = {
                "ref_code": [prompt_items[0].ref_code],
                "ref_spk_embedding": [target_emb],
                "x_vector_only_mode": [False],
                "icl_mode": [True]
            }
        else:
            # Standard cloning: just the voice embedding
            voice_clone_prompt = {
                "ref_spk_embedding": [target_emb],
                "x_vector_only_mode": [True],
                "icl_mode": [False]
            }
            
        wavs, sr = model.generate_voice_clone(text=text, voice_clone_prompt=voice_clone_prompt, instruct=instruct)
        return {"waveform": wavs[0], "sample_rate": sr, "text": text}

    def generate_podcast(self, script: List[Dict[str, Any]], profiles: Dict[str, Dict[str, Any]], bgm_mood: Optional[str] = None, ducking_level: float = 0.0, eq_preset: str = "flat", reverb_level: float = 0.0, master_acx: bool = False, temperature: Optional[float] = None, **gen_kwargs) -> Optional[Dict[str, Any]]:
        with Profiler("Generate Podcast"):
            sample_rate = 24000
            waveforms = [None] * len(script)
            srs = [None] * len(script)

            # ⚡ Bolt: Group segments by model type and temperature for batched synthesis
            # Note: Batching currently only works for identical generation parameters.
            # If segments have different temperatures, we might need more complex grouping or fall back to serial.
            groups = {"CustomVoice": [], "VoiceDesign": [], "Base": []}
            for i, item in enumerate(script):
                role = item.get("role")
                profile = profiles.get(role)
                if profile is None:
                    continue
                mtype = self._get_model_type_for_profile(profile)
                if profile.get("type") == "preset":
                    mtype = "CustomVoice"
                groups[mtype].append(i)

            for mtype, indices in groups.items():
                if not indices:
                    continue
                try:
                    # Check if all segments in this group share the same temperature
                    # If not, we fall back to serial synthesis for safety
                    group_temps = [script[idx].get("temperature") if script[idx].get("temperature") is not None else temperature for idx in indices]
                    if len(set(group_temps)) > 1:
                         raise ValueError("Heterogeneous temperatures in batch; falling back to serial.")

                    target_temp = group_temps[0]
                    model = get_model(mtype)
                    batch_texts = [phoneme_manager.apply(script[i]["text"]) for i in indices]
                    batch_langs = [script[i].get("language", "auto") for i in indices]
                    batch_instructs = [script[i].get("instruct") or profiles[script[i]["role"]].get("instruct") for i in indices]

                    if mtype == "CustomVoice":
                        speakers = [profiles[script[i]["role"]]["value"] for i in indices]
                        wavs, sr = model.generate_custom_voice(text=batch_texts, speaker=speakers, language=batch_langs, instruct=batch_instructs, temperature=target_temp, **gen_kwargs)
                    elif mtype == "VoiceDesign":
                        design_instructs = []
                        for i, idx in enumerate(indices):
                            p = profiles[script[idx]["role"]]
                            ins = p["value"]
                            if batch_instructs[i]: ins = f"{ins}, {batch_instructs[i]}"
                            design_instructs.append(ins)
                        wavs, sr = model.generate_voice_design(text=batch_texts, instruct=design_instructs, language=batch_langs, non_streaming_mode=True, temperature=target_temp, **gen_kwargs)
                    elif mtype == "Base":
                        batch_prompts = []
                        for i, idx in enumerate(indices):
                            p = profiles[script[idx]["role"]]
                            cache_key = p["value"] if p["type"] == "clone" else f"mix:{p['value']}"
                            if cache_key in self.prompt_cache:
                                prompt = self.prompt_cache[cache_key]
                            else:
                                if p["type"] == "clone":
                                    resolved = self._resolve_paths(p["value"])
                                    ref_audio = str(resolved[0])
                                    if VideoEngine.is_video(ref_audio): ref_audio = self._extract_audio_with_cache(ref_audio)
                                    prompt = model.create_voice_clone_prompt(ref_audio=ref_audio, x_vector_only_mode=True)
                                elif p["type"] == "mix":
                                    mix_configs = json.loads(p["value"])
                                    mixed_emb = self._compute_mixed_embedding(mix_configs, model=model)
                                    prompt = [VoiceClonePromptItem(ref_code=None, ref_spk_embedding=mixed_emb, x_vector_only_mode=True, icl_mode=False, ref_text=None)]
                                else:
                                    raise ValueError(f"Profile type {p['type']} not compatible with Base model batching")
                                # ⚡ Bolt: Prevent unbounded growth of prompt cache
                                prune_dict_cache(self.prompt_cache, limit=200, count=20)
                                self.prompt_cache[cache_key] = prompt
                            batch_prompts.append(prompt[0])
                        wavs, sr = model.generate_voice_clone(text=batch_texts, language=batch_langs, voice_clone_prompt=batch_prompts, instruct=batch_instructs, temperature=target_temp, **gen_kwargs)

                    for j, idx in enumerate(indices):
                        waveforms[idx], srs[idx] = wavs[j], sr
                except Exception as e:
                    logger.warning(f"⚡ Bolt: Batch synthesis failed for {mtype}, falling back to serial: {e}")
                    for idx in indices:
                        try:
                            item = script[idx]
                            current_temp = item.get("temperature") if item.get("temperature") is not None else temperature
                            wav, sr = self.generate_segment(item["text"], profile=profiles.get(item["role"]), language=item.get("language", "auto"), instruct=item.get("instruct"), temperature=current_temp, **gen_kwargs)
                            waveforms[idx], srs[idx] = wav, sr
                        except Exception: continue

            # ⚡ Bolt: Check speaker embedding consistency across segments (Task 4.3)
            speaker_first_emb = {}  # role -> embedding of first segment
            for i, item in enumerate(script):
                if waveforms[i] is None: continue
                role = item.get("role")
                profile = profiles.get(role)
                if profile is None: continue
                try:
                    emb = self.get_speaker_embedding(profile)
                    if emb is not None:
                        if role not in speaker_first_emb:
                            speaker_first_emb[role] = emb
                        else:
                            # Cosine similarity
                            if torch is not None:
                                cos_sim = float(torch.nn.functional.cosine_similarity(
                                    speaker_first_emb[role].unsqueeze(0), emb.unsqueeze(0)
                                ))
                                if cos_sim < 0.85:  # 15% drift threshold
                                    logger.warning(f"Voice drift detected for speaker '{role}' at segment {i}: "
                                                   f"similarity={cos_sim:.2f} (threshold=0.85)")
                except Exception:
                    pass  # Don't block generation for embedding comparison failures

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
            if not speech_segments: return None

            # ⚡ Bolt: Multi-track mixing buffer (Mono by default, Stereo if panning/BGM)
            # ACX/Audible prefers mono for voice, but 2026 trends favor spatial 3D audio.
            is_stereo_req = bgm_mood is not None
            final_wav, max_sample, speech_segments = self.patcher.construct_timeline(script, waveforms, srs, sample_rate, is_stereo_req)

            if bgm_mood:
                is_stereo = any(s.get("pan", 0) != 0 for s in script) or bgm_mood is not None
                bgm_samples = self.patcher.load_bgm(bgm_mood, sample_rate, max_sample, ducking_level, is_stereo, speech_segments)
                if bgm_samples is not None:
                    if is_stereo:
                        final_wav += bgm_samples[None, :]
                    else:
                        final_wav += bgm_samples

            # ⚡ Bolt: Post-Processing Pipeline (Task 4.4)
            final_wav = self.patcher.apply_mastering(final_wav, sample_rate, eq_preset, reverb_level, master_acx)

            # ⚡ Bolt: Apply watermark once at the very end of the podcast project.
            final_wav = self._apply_audio_watermark(final_wav, sample_rate)

            return {"waveform": final_wav, "sample_rate": sample_rate}

    def dub_audio(self, audio_path: str, target_lang: str) -> Optional[Dict[str, Any]]:
        result = self.transcribe_audio(audio_path)
        text = result["text"]
        trans_lang = 'zh-CN' if target_lang == 'zh' else target_lang

        # ⚡ Bolt: Cache translation results with hashed keys to avoid redundant API calls and save memory
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        cache_key = f"{text_hash}:{trans_lang}"

        if cache_key in self.translation_cache:
            translated_text = self.translation_cache[cache_key]
        else:
            # ⚡ Bolt: Gradual cache pruning instead of drastic clear()
            prune_dict_cache(self.translation_cache, limit=1000, count=100)
            translated_text = GoogleTranslator(source='auto', target=trans_lang).translate(text)
            self.translation_cache[cache_key] = translated_text

        wav, sr = self.generate_segment(translated_text, profile={"type": "clone", "value": audio_path}, language=target_lang)
        return {"waveform": wav, "sample_rate": sr, "text": translated_text}
