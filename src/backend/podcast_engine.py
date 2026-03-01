import os
import json
import uuid
import torch
import numpy as np
import soundfile as sf
import librosa
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydub import AudioSegment
from deep_translator import GoogleTranslator

from .model_loader import get_model
from .config import BASE_DIR, logger
from .video_engine import VideoEngine

class PodcastEngine:
    def __init__(self):
        self.upload_dir = Path("uploads").resolve()
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        # Caches
        self.preset_embeddings = {}
        self.clone_embedding_cache = {}
        self.prompt_cache = {}

        self._whisper_model = None # Lazy load

    def _resolve_paths(self, relative_path: str) -> List[Path]:
        """Resolve one or more relative paths against upload_dir and ensure safety."""
        if not relative_path:
            return []
        # Handle multiple paths for pro cloning (separated by |)
        paths = relative_path.split("|")
        resolved = []
        for p in paths:
            path_obj = Path(p)
            if not path_obj.is_absolute():
                path_obj = (self.upload_dir / path_obj).resolve()
            else:
                path_obj = path_obj.resolve()

            # Security: Use is_relative_to for robust path validation (avoids partial path traversal)
            is_safe = path_obj.is_relative_to(self.upload_dir)
            if not is_safe:
                bgm_dir = (Path(BASE_DIR) / "bgm").resolve()
                is_safe = path_obj.is_relative_to(bgm_dir)

            if not is_safe:
                # Check video dir too
                from .config import VIDEO_DIR
                is_safe = path_obj.is_relative_to(VIDEO_DIR)

            if not is_safe:
                raise ValueError(f"Access denied to path: {p}")

            if not path_obj.exists():
                raise FileNotFoundError(f"File not found: {p}")
            resolved.append(path_obj)
        return resolved

    def _get_model_type_for_profile(self, profile: Dict[str, Any]) -> str:
        """Determines the required Qwen-TTS model type for a given speaker profile."""
        ptype = profile.get("type")
        if ptype == "preset":
            return "CustomVoice"
        if ptype == "design":
            return "VoiceDesign"
        # Clone and Mix both use the Base model
        return "Base"

    def get_system_status(self) -> Dict[str, Any]:
        return {
            "status": "ready",
            "device": "cuda" if torch.cuda.is_available() else "cpu",
            "models_loaded": list(self.prompt_cache.keys())
        }

    def transcribe_audio(self, audio_path: str) -> str:
        if self._whisper_model is None:
            import whisper
            logger.info("Loading Whisper model for transcription...")
            self._whisper_model = whisper.load_model("base")

        try:
            resolved_paths = self._resolve_paths(audio_path)
            safe_path = str(resolved_paths[0])

            # Handle Video
            if VideoEngine.is_video(safe_path):
                safe_path = VideoEngine.extract_audio(safe_path)

            logger.info(f"Transcribing: {safe_path}")
            result = self._whisper_model.transcribe(safe_path)
            text = result["text"].strip()
            return text
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise RuntimeError(f"Transcription failed: {e}")

    def get_speaker_embedding(self, profile: Dict[str, str]) -> torch.Tensor:
        """Extract speaker embedding for any profile."""
        # Check caches first to avoid expensive extraction and model switches
        if profile["type"] == "preset":
            name = profile["value"].lower()
            if name in self.preset_embeddings:
                return self.preset_embeddings[name]
        elif profile["type"] == "clone":
            if profile["value"] in self.clone_embedding_cache:
                return self.clone_embedding_cache[profile["value"]]

        model = get_model("Base")

        if profile["type"] == "preset":
            emb = model.get_speaker_embedding(profile["value"])
            self.preset_embeddings[profile["value"].lower()] = emb
            return emb
        elif profile["type"] == "clone":
            resolved = self._resolve_paths(profile["value"])
            # Handle Video for cloning if needed
            clone_path = str(resolved[0])
            if VideoEngine.is_video(clone_path):
                clone_path = VideoEngine.extract_audio(clone_path)

            prompt = model.create_voice_clone_prompt(ref_audio=clone_path, x_vector_only_mode=True)
            emb = prompt[0].ref_spk_embedding
            self.clone_embedding_cache[profile["value"]] = emb
            return emb
        return None

    def generate_segment(self, text: str, profile: Dict[str, Any], language: str = "auto") -> tuple:
        """Generates a single audio segment for a given speaker profile."""
        try:
            def get_model_wrapper(mtype):
                return get_model(mtype)

            if profile["type"] == "preset":
                model = get_model("CustomVoice")
                wavs, sr = model.generate_custom_voice(
                    text=text,
                    speaker=profile["value"], 
                    language=language
                )
            elif profile["type"] == "design":
                model = get_model("VoiceDesign")
                wavs, sr = model.generate_voice_design(
                    text=text,
                    instruct=profile["value"],
                    language=language,
                    non_streaming_mode=True
                )
            elif profile["type"] == "clone":
                cache_key = profile["value"]

                if cache_key in self.prompt_cache:
                    logger.debug(f"Using cached prompt for {cache_key}")
                    prompt = self.prompt_cache[cache_key]
                    model = get_model("Base")
                else:
                    try:
                        resolved_paths = self._resolve_paths(profile["value"])
                    except FileNotFoundError as e:
                        raise RuntimeError(f"Cloning reference audio not found: {e}") from e

                    model = get_model("Base")
                    if len(resolved_paths) > 1:
                        combined_wav = []
                        target_sr = 24000
                        for path_obj in resolved_paths:
                            w, s = sf.read(str(path_obj))
                            if s != target_sr:
                                w = librosa.resample(w.astype(np.float32), orig_sr=s, target_sr=target_sr)
                            combined_wav.append(w)
                        concatenated = np.concatenate(combined_wav)
                        ref_audio = (concatenated, target_sr)
                    else:
                        ref_audio = str(resolved_paths[0])
                        if VideoEngine.is_video(ref_audio):
                            ref_audio = VideoEngine.extract_audio(ref_audio)

                    logger.info(f"Extracting voice clone prompt for {cache_key}...")
                    prompt = model.create_voice_clone_prompt(ref_audio=ref_audio, x_vector_only_mode=True)
                    self.prompt_cache[cache_key] = prompt

                wavs, sr = model.generate_voice_clone(
                    text=text,
                    language=language,
                    voice_clone_prompt=prompt,
                )
            elif profile["type"] == "mix":
                mix_configs = json.loads(profile["value"])
                mixed_emb = self._compute_mixed_embedding(mix_configs)

                model = get_model("Base")
                voice_clone_prompt = {
                    "ref_spk_embedding": [mixed_emb],
                    "x_vector_only_mode": [True],
                    "icl_mode": [False],
                    "ref_code": [None]
                }
                wavs, sr = model.generate_voice_clone(
                    text=text,
                    language=language,
                    voice_clone_prompt=voice_clone_prompt
                )
            else:
                raise ValueError(f"Unknown speaker type: {profile['type']}")
                
            if not wavs:
                raise RuntimeError("Engine returned no waveforms")

            return wavs[0], sr
            
        except Exception as e:
            logger.error(f"Synthesis failed: {e}", exc_info=True)
            raise RuntimeError(f"Synthesis failed: {str(e)}") from e

    def _compute_mixed_embedding(self, mix_configs: List[Dict[str, Any]]) -> torch.Tensor:
        """Compute a weighted average of multiple speaker embeddings."""
        total_weight = sum(c["weight"] for c in mix_configs)
        if total_weight == 0:
            return None

        mixed_emb = None
        for config in mix_configs:
            emb = self.get_speaker_embedding(config["profile"])
            weight = config["weight"] / total_weight
            if mixed_emb is None:
                mixed_emb = emb * weight
            else:
                mixed_emb += emb * weight
        return mixed_emb

    def generate_voice_changer(self, source_audio: str, target_profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Preserve prosody of source while changing voice to target."""
        try:
            # 1. Transcribe source
            text = self.transcribe_audio(source_audio)

            # 2. Extract codes from source
            resolved = self._resolve_paths(source_audio)
            source_path = str(resolved[0])

            if VideoEngine.is_video(source_path):
                source_path = VideoEngine.extract_audio(source_path)

            model = get_model("Base")
            # We want ICL mode (x_vector_only=False) to get codes
            prompt_items = model.create_voice_clone_prompt(ref_audio=source_path, ref_text=text, x_vector_only_mode=False)
            source_item = prompt_items[0]

            # 3. Get target embedding
            if not target_profile:
                target_profile = {"type": "preset", "value": "Ryan"}

            target_emb = self.get_speaker_embedding(target_profile)

            # 4. Synthesize with swapped embedding
            voice_clone_prompt = {
                "ref_code": [source_item.ref_code],
                "ref_spk_embedding": [target_emb],
                "x_vector_only_mode": [False],
                "icl_mode": [True]
            }

            wavs, sr = model.generate_voice_clone(
                text=text, # target text is same as source text
                voice_clone_prompt=voice_clone_prompt
            )

            return {"waveform": wavs[0], "sample_rate": sr, "text": text}
        except Exception as e:
            logger.error(f"Voice changer failed: {e}")
            raise RuntimeError(f"Voice changer failed: {e}")

    def generate_podcast(self, script: List[Dict[str, Any]], profiles: Dict[str, Dict[str, Any]], bgm_mood: Optional[str] = None, ducking_level: float = 0.0) -> Dict[str, Any]:
        sample_rate = 24000

        # 1. Pre-map indices to model types for grouping to prevent model thrashing
        model_groups = {} # model_type -> list of (index, item)
        for i, item in enumerate(script):
            role = item["role"]
            profile = profiles.get(role, {"type": "preset", "value": "Ryan"})
            mtype = self._get_model_type_for_profile(profile)
            if mtype not in model_groups:
                model_groups[mtype] = []
            model_groups[mtype].append((i, item))

        # 2. Batch synthesis by model type to minimize switches
        waveforms = [None] * len(script)
        srs = [None] * len(script)

        for mtype, group in model_groups.items():
            logger.info(f"⚡ Bolt: Synthesizing group for model '{mtype}' ({len(group)} segments)")
            for i, item in group:
                role = item["role"]
                text = item["text"]
                lang = item.get("language", "auto")
                profile = profiles.get(role)
                try:
                    wav, sr = self.generate_segment(text, profile=profile, language=lang)
                    waveforms[i] = wav
                    srs[i] = sr
                except Exception as e:
                    logger.error(f"Error generating segment {i} for {role}: {e}")

        # 3. Assemble chronological mix
        segments = []
        max_duration_ms = 0
        current_offset_ms = 0
        
        for i, item in enumerate(script):
            if waveforms[i] is None:
                continue

            wav = waveforms[i]
            sr = srs[i]
            sample_rate = sr
            pause_after = item.get("pause_after", 0.5)
            start_time = item.get("start_time", None)

            wav_int16 = (wav * 32767).astype(np.int16)
            seg = AudioSegment(wav_int16.tobytes(), frame_rate=sr, sample_width=2, channels=1)
            
            position_ms = int(float(start_time) * 1000) if start_time is not None else current_offset_ms
            segments.append({"audio": seg, "position": position_ms})

            current_offset_ms = position_ms + len(seg) + int(pause_after * 1000)

            end_pos = position_ms + len(seg)
            if end_pos > max_duration_ms: max_duration_ms = end_pos
                
        if not segments: return None
        final_mix = AudioSegment.silent(duration=max_duration_ms + 2000, frame_rate=sample_rate)
        for seg in segments:
            final_mix = final_mix.overlay(seg["audio"], position=seg["position"])


        if bgm_mood:
            try:
                from .config import SHARED_ASSETS_DIR, BASE_DIR
                bgm_file = None

                # 1. Check shared assets
                shared_path = SHARED_ASSETS_DIR / bgm_mood
                if shared_path.exists():
                    bgm_file = shared_path
                else:
                    # 2. Fallback to preset bgm/ folder
                    bgm_full_path = (Path(BASE_DIR) / "bgm" / f"{bgm_mood}.mp3").resolve()
                    if bgm_full_path.exists():
                        bgm_file = bgm_full_path

                if bgm_file:
                    bgm_segment = AudioSegment.from_file(bgm_file) - 20
                    if len(bgm_segment) < len(final_mix):
                        loops = int(len(final_mix) / len(bgm_segment)) + 1
                        bgm_segment = bgm_segment * loops
                    bgm_segment = bgm_segment[:len(final_mix)]

                    if ducking_level > 0:
                        ducking_db = - (ducking_level * 25)
                        for seg in segments:
                            pos = seg["position"]
                            dur = len(seg["audio"])
                            if pos + dur > len(bgm_segment): continue

                            ducked_part = bgm_segment[pos:pos+dur] + ducking_db
                            bgm_segment = bgm_segment[:pos] + ducked_part + bgm_segment[pos+dur:]

                    final_mix = final_mix.overlay(bgm_segment)

            except Exception as e:
                logger.error(f"BGM mixing failed: {e}")


        samples = np.array(final_mix.get_array_of_samples())
        if final_mix.channels == 2:
            samples = samples.reshape((-1, 2)).mean(axis=1)
        final_wav = samples.astype(np.float32) / 32768.0
        max_val = np.max(np.abs(final_wav))
        if max_val > 1.0: final_wav = final_wav / max_val
        return {"waveform": final_wav, "sample_rate": sample_rate}

    def dub_audio(self, audio_path: str, target_lang: str) -> Dict[str, Any]:
        """Dub audio by transcribing, translating, and synthesizing."""
        try:
            # 1. Transcribe (Handles Video automatically)
            text = self.transcribe_audio(audio_path)

            # 2. Translate
            logger.info(f"Translating to {target_lang}...")
            trans_lang = 'zh-CN' if target_lang == 'zh' else target_lang
            translated_text = GoogleTranslator(source='auto', target=trans_lang).translate(text)
            logger.info(f"Translated: {translated_text[:50]}...")

            # 3. Clone original voice for synthesis (Handles Video automatically)
            original_profile = {"type": "clone", "value": audio_path}

            # 4. Synthesize with target language
            wav, sr = self.generate_segment(translated_text, profile=original_profile, language=target_lang)

            return {"waveform": wav, "sample_rate": sr, "text": translated_text}
        except Exception as e:
            logger.error(f"Dubbing failed: {e}")
            raise RuntimeError(f"Dubbing failed: {e}")
