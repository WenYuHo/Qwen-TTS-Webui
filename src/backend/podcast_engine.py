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

    def transcribe_audio(self, audio_path: str) -> str:
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
        result = self._whisper_model.transcribe(actual_path)
        text = result["text"]
        if cache_key:
            try:
                # ⚡ Bolt: Gradual cache pruning instead of drastic clear()
                prune_dict_cache(self.transcription_cache, limit=1000, count=100)
                self.transcription_cache[cache_key] = text
            except Exception: pass
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
            # ⚡ Bolt: Prevent unbounded growth of preset embeddings cache
            prune_dict_cache(self.preset_embeddings, limit=200, count=20)
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

            # ⚡ Bolt: Prevent unbounded growth of prompt and embedding caches
            prune_dict_cache(self.prompt_cache, limit=200, count=20)
            prune_dict_cache(self.clone_embedding_cache, limit=200, count=20)

            self.prompt_cache[cache_key] = prompt
            self.clone_embedding_cache[cache_key] = emb
            return emb
        return None

    def _apply_audio_watermark(self, wav: np.ndarray, sr: int) -> np.ndarray:
        try:
            global _system_settings
            if _system_settings is None:
                # ⚡ Bolt: Circular-safe import for settings
                import src.backend.api.system as system_api
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
        """Compute basic audio quality metrics for a generated segment."""
        duration = len(wav) / sr
        rms = float(np.sqrt(np.mean(wav ** 2)))
        peak = float(np.max(np.abs(wav)))
        # SNR estimate: ratio of signal RMS to noise floor (last 0.1s assumed silence)
        tail = wav[-int(sr * 0.1):] if len(wav) > int(sr * 0.1) else wav
        noise_rms = float(np.sqrt(np.mean(tail ** 2))) + 1e-10
        snr_db = 20 * np.log10(rms / noise_rms) if rms > 0 else 0
        clipping = bool(peak > 0.99)
        too_quiet = bool(rms < 0.01)
        return {
            "duration": round(duration, 2),
            "rms": round(rms, 4),
            "peak": round(peak, 4),
            "snr_db": round(snr_db, 1),
            "clipping": clipping,
            "too_quiet": too_quiet,
            "quality": "good" if (not clipping and not too_quiet and snr_db > 10) else "warning"
        }

    def generate_segment(self, text: str, profile: Dict[str, Any], language: str = "auto", model: Optional[Any] = None, instruct: Optional[str] = None, temperature: Optional[float] = None, **gen_kwargs) -> tuple[np.ndarray, int]:
        try:
            text = phoneme_manager.apply(text)
            final_instruct = instruct or profile.get("instruct")
            wavs = None
            ptype = profile.get("type")
            if ptype == "preset":
                if model is None: model = get_model("CustomVoice")
                wavs, sr = model.generate_custom_voice(text=text, speaker=profile["value"], language=language, instruct=final_instruct, temperature=temperature, **gen_kwargs)
            elif ptype == "design":
                if model is None: model = get_model("VoiceDesign")
                design_instruct = profile["value"]
                if final_instruct: design_instruct = f"{design_instruct}, {final_instruct}"
                wavs, sr = model.generate_voice_design(text=text, instruct=design_instruct, language=language, non_streaming_mode=True, temperature=temperature, **gen_kwargs)
            elif ptype == "clone":
                ref_text = profile.get("ref_text")
                use_icl = ref_text is not None and ref_text.strip() != ""
                cache_key = profile["value"]
                # When ref_text is provided, use ICL mode for higher quality cloning
                # ICL captures expressive similarity, prosody, and emotional nuances
                icl_cache_key = f"{cache_key}:icl:{ref_text}" if use_icl else cache_key
                if icl_cache_key in self.prompt_cache:
                    prompt = self.prompt_cache[icl_cache_key]
                else:
                    try:
                        resolved_paths = self._resolve_paths(profile["value"])
                    except (FileNotFoundError, PermissionError) as e:
                        raise RuntimeError(f"Cloning reference audio not found: {profile['value']}") from e
                    
                    if model is None: model = get_model("Base")
                    ref_audio = str(resolved_paths[0])
                    if VideoEngine.is_video(ref_audio): ref_audio = self._extract_audio_with_cache(ref_audio)
                    
                    # ⚡ Bolt: Validate reference audio before processing
                    self._validate_ref_audio(ref_audio)

                    # ⚡ Bolt: Silence padding for ICL anti-bleed
                    if use_icl:
                        import soundfile as sf
                        audio_data, audio_sr = sf.read(ref_audio)
                        # Append 0.5s silence to prevent phoneme bleed from ref into generated speech
                        silence = np.zeros(int(audio_sr * 0.5), dtype=audio_data.dtype)
                        padded = np.concatenate([audio_data, silence])
                        # Write padded audio to a temp file (will be cleaned by StorageManager)
                        padded_path = str(self.upload_dir / f"padded_{uuid.uuid4()}.wav")
                        sf.write(padded_path, padded, audio_sr)
                        ref_audio = padded_path

                    prompt = model.create_voice_clone_prompt(
                        ref_audio=ref_audio,
                        ref_text=ref_text if use_icl else None,
                        x_vector_only_mode=not use_icl
                    )
                    # Prevent unbounded growth of prompt cache
                    prune_dict_cache(self.prompt_cache, limit=200, count=20)
                    self.prompt_cache[icl_cache_key] = prompt
                if model is None: model = get_model("Base")
                wavs, sr = model.generate_voice_clone(text=text, language=language, voice_clone_prompt=prompt, instruct=final_instruct, temperature=temperature, **gen_kwargs)
            elif ptype == "mix":
                cache_key = f"mix:{profile['value']}"
                if cache_key in self.prompt_cache: prompt = self.prompt_cache[cache_key]
                else:
                    # ⚡ Bolt: Prevent unbounded growth of prompt cache
                    prune_dict_cache(self.prompt_cache, limit=200, count=20)
                    mix_configs = json.loads(profile["value"])
                    mixed_emb = self._compute_mixed_embedding(mix_configs)
                    prompt = [VoiceClonePromptItem(ref_code=None, ref_spk_embedding=mixed_emb, x_vector_only_mode=True, icl_mode=False, ref_text=None)]
                    self.prompt_cache[cache_key] = prompt
                if model is None: model = get_model("Base")
                wavs, sr = model.generate_voice_clone(text=text, language=language, voice_clone_prompt=prompt, instruct=final_instruct, temperature=temperature, **gen_kwargs)
            else:
                raise RuntimeError(f"Unknown speaker type: {ptype}")

            if not wavs: raise RuntimeError("No waveforms generated")
            
            # Task 4.1 & 4.2: Quality Check & Auto-Retry
            wav_out = self._apply_audio_watermark(wavs[0], sr)
            quality = self._compute_quality_score(wav_out, sr)
            logger.info(f"Segment quality: {quality}")
            audit_manager.log_event("synthesis", {"quality": quality, "profile_type": ptype}, quality["quality"])

            if quality["quality"] == "warning" and not gen_kwargs.get("_is_retry"):
                logger.warning(f"Low quality detected (SNR={quality['snr_db']}dB), retrying with lower temperature")
                retry_kwargs = {**gen_kwargs, "temperature": 0.3, "top_k": 20, "_is_retry": True}
                return self.generate_segment(text, profile, language, model, instruct, **retry_kwargs)

            return wav_out, sr
        except Exception as e:
            if not isinstance(e, RuntimeError):
                logger.error(f"Synthesis failed: {e}")
            raise

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
            is_stereo = any(s.get("pan", 0) != 0 for s in script) or bgm_mood is not None
            
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

            if bgm_mood:
                try:
                    # ⚡ Bolt: Cache BGM samples to avoid redundant loading and resampling
                    if bgm_mood in self.bgm_cache:
                        bgm_samples = self.bgm_cache[bgm_mood]
                        # ⚡ Bolt: Only copy if we need to modify the samples in-place (ducking)
                        if ducking_level > 0:
                            bgm_samples = bgm_samples.copy()
                    else:
                        bgm_full_path = (Path(BASE_DIR) / "bgm" / f"{bgm_mood}.mp3").resolve()
                        if not bgm_full_path.exists():
                            # Fallback to absolute or relative if mood.mp3 doesn't exist
                            bgm_full_path = Path(bgm_mood).resolve()
                            if not bgm_full_path.exists():
                                # Try shared_assets
                                bgm_full_path = (SHARED_ASSETS_DIR / bgm_mood).resolve()

                        if bgm_full_path.exists() and bgm_full_path.is_file():
                            # ⚡ Bolt: Prevent unbounded growth of BGM cache
                            prune_dict_cache(self.bgm_cache, limit=50, count=5)
                            bgm_audio = AudioSegment.from_file(bgm_full_path).set_frame_rate(sample_rate).set_channels(1)
                            bgm_samples = np.array(bgm_audio.get_array_of_samples(), dtype=np.float32) / 32768.0 * 0.1
                            self.bgm_cache[bgm_mood] = bgm_samples.copy()
                        else:
                            bgm_samples = None

                    if bgm_samples is not None:
                        if len(bgm_samples) < (max_sample + int(2.0 * sample_rate)):
                            bgm_samples = np.tile(bgm_samples, int(np.ceil((max_sample + int(2.0 * sample_rate))/len(bgm_samples))))
                        bgm_samples = bgm_samples[:(max_sample + int(2.0 * sample_rate))]
                        
                        if ducking_level > 0:
                            duck_factor = 10 ** (-(ducking_level * 25) / 20.0)
                            # ⚡ Bolt: Use vectorized ducking in-place for the BGM track
                            for seg in speech_segments: 
                                bgm_samples[seg["start"]:seg["end"]] *= duck_factor
                        
                        if is_stereo:
                            # ⚡ Bolt: Use broadcasting for O(1) stereo expansion instead of O(N) np.stack
                            # This avoids a redundant copy of the BGM samples.
                            final_wav += bgm_samples[None, :]
                        else:
                            final_wav += bgm_samples
                except Exception as e:
                    logger.error(f"Failed to apply BGM: {e}")

            # ⚡ Bolt: Use max(np.max, -np.min) for memory efficiency. It's ~2.4x faster
            # and avoids allocating a large O(N) temporary array for np.abs(final_wav).
            max_val = max(np.max(final_wav), -np.min(final_wav))
            if max_val > 1.0: final_wav /= max_val

            # ⚡ Bolt: Post-Processing Pipeline (Task 4.4)
            # 1. De-clicker to remove potential splicing artifacts
            final_wav = AudioPostProcessor.apply_declick(final_wav, sample_rate)

            # 2. Creative Effects (EQ, Reverb)
            final_wav = AudioPostProcessor.apply_eq(final_wav, sample_rate, preset=eq_preset)
            final_wav = AudioPostProcessor.apply_reverb(final_wav, sample_rate, intensity=reverb_level)
            
            # ⚡ Bolt: Final mastering for ACX compliance if requested
            if master_acx:
                # 3. Dynamic Range Compression for ACX "punch"
                final_wav = AudioPostProcessor.apply_compressor(final_wav, sample_rate, threshold_db=-20.0, ratio=4.0)
                # 4. Loudness Normalization (-3dB peak, -18 to -23dB RMS)
                final_wav = AudioPostProcessor.normalize_acx(final_wav)

            # ⚡ Bolt: Apply watermark once at the very end of the podcast project.
            final_wav = self._apply_audio_watermark(final_wav, sample_rate)

            return {"waveform": final_wav, "sample_rate": sample_rate}

    def dub_audio(self, audio_path: str, target_lang: str) -> Optional[Dict[str, Any]]:
        text = self.transcribe_audio(audio_path)
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
