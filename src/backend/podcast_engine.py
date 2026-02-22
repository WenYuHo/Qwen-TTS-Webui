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

class PodcastEngine:
    def __init__(self):
        self.upload_dir = Path("uploads")
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.speaker_profiles = {}
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

            if not str(path_obj).startswith(str(self.upload_dir.resolve())):
                bgm_dir = (Path(BASE_DIR) / "bgm").resolve()
                if not str(path_obj).startswith(str(bgm_dir)):
                     raise ValueError(f"Access denied to path: {p}")

            if not path_obj.exists():
                raise FileNotFoundError(f"File not found: {p}")
            resolved.append(path_obj)
        return resolved

    def set_speaker_profile(self, role: str, profile: Dict[str, str]):
        self.speaker_profiles[role] = profile
        logger.info(f"Speaker profile set for '{role}': {profile['type']}")

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

            logger.info(f"Transcribing audio: {safe_path}")
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

        base_model = get_model("Base")

        if profile["type"] == "clone":
            resolved_paths = self._resolve_paths(profile["value"])
            ref_audio = str(resolved_paths[0])
            prompt = base_model.create_voice_clone_prompt(ref_audio=ref_audio, x_vector_only_mode=True)
            emb = prompt[0].ref_spk_embedding
            self.clone_embedding_cache[profile["value"]] = emb
            # Also populate prompt cache since we already have it
            self.prompt_cache[profile["value"]] = prompt
            return emb

        elif profile["type"] == "preset":
            name = profile["value"].lower()
            logger.info(f"Extracting embedding for preset: {name}")
            cv_model = get_model("CustomVoice")
            wavs, sr = cv_model.generate_custom_voice(text="Speaker reference sample.", speaker=name)

            base_model = get_model("Base") # Ensure Base is loaded back
            prompt = base_model.create_voice_clone_prompt(ref_audio=(wavs[0], sr), x_vector_only_mode=True)
            emb = prompt[0].ref_spk_embedding
            self.preset_embeddings[name] = emb
            return emb

        elif profile["type"] == "design":
            # Designs are usually processed per-segment but we can pre-extract
            # However, design depends on the prompt. For simplicity, we just return None
            # and let generate_segment handle it.
            return None
        elif profile["type"] == "mix":
            mix_configs = json.loads(profile["value"])
            return self._compute_mixed_embedding(mix_configs)
        return None

    def _compute_mixed_embedding(self, mix_configs: List[Dict[str, Any]]) -> torch.Tensor:
        total_emb = None
        total_weight = 0.0

        for item in mix_configs:
            weight = float(item.get("weight", 0.5))
            voice_profile = item["profile"]
            emb = self.get_speaker_embedding(voice_profile)
            if total_emb is None:
                total_emb = emb * weight
            else:
                total_emb += emb * weight
            total_weight += weight

        if total_emb is None:
            raise ValueError("No valid voices provided for mixing")

        return total_emb / total_weight

    def generate_segment(self, role: str, text: str, language: str = "auto") -> tuple:
        profile = self.speaker_profiles.get(role)
        if not profile:
            profile = {"type": "preset", "value": "Ryan"}
            
        logger.info(f"Synthesis starting for role '{role}' ({profile['type']}): {text[:30]}...")
            
        try:
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
            logger.error(f"Synthesis failed for role '{role}': {e}", exc_info=True)
            raise RuntimeError(f"Synthesis failed for role '{role}': {str(e)}") from e

    def generate_voice_changer(self, source_audio: str, target_role: str) -> Dict[str, Any]:
        """Preserve prosody of source while changing voice to target."""
        try:
            # 1. Transcribe source
            text = self.transcribe_audio(source_audio)

            # 2. Extract codes from source
            resolved = self._resolve_paths(source_audio)
            source_path = str(resolved[0])

            model = get_model("Base")
            # We want ICL mode (x_vector_only=False) to get codes
            prompt_items = model.create_voice_clone_prompt(ref_audio=source_path, ref_text=text, x_vector_only_mode=False)
            source_item = prompt_items[0]

            # 3. Get target embedding
            target_profile = self.speaker_profiles.get(target_role)
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

    def generate_podcast(self, script: List[Dict[str, Any]], bgm_mood: Optional[str] = None) -> Dict[str, Any]:
        segments = []
        sample_rate = 24000
        max_duration_ms = 0
        current_offset_ms = 0
        
        for item in script:
            role = item["role"]
            text = item["text"]
            lang = item.get("language", "auto")
            pause_after = item.get("pause_after", 0.5)
            start_time = item.get("start_time", None) 
            
            try:
                wav, sr = self.generate_segment(role, text, language=lang)
                sample_rate = sr
                wav_int16 = (wav * 32767).astype(np.int16)
                seg = AudioSegment(wav_int16.tobytes(), frame_rate=sr, sample_width=2, channels=1)
                
                position_ms = int(float(start_time) * 1000) if start_time is not None else current_offset_ms
                segments.append({"audio": seg, "position": position_ms})

                current_offset_ms = position_ms + len(seg) + int(pause_after * 1000)
                
                end_pos = position_ms + len(seg)
                if end_pos > max_duration_ms: max_duration_ms = end_pos
            except Exception as e:
                logger.error(f"Error generating segment for {role}: {e}")
                continue
                
        if not segments: return None
        final_mix = AudioSegment.silent(duration=max_duration_ms + 2000, frame_rate=sample_rate)
        for seg in segments:
            final_mix = final_mix.overlay(seg["audio"], position=seg["position"])

        if bgm_mood:
            try:
                bgm_dir = Path(BASE_DIR) / "bgm"
                bgm_file = bgm_dir / f"{bgm_mood}.mp3" 
                if bgm_file.exists():
                    bgm_segment = AudioSegment.from_file(bgm_file) - 20
                    if len(bgm_segment) < len(final_mix):
                        loops = int(len(final_mix) / len(bgm_segment)) + 1
                        bgm_segment = bgm_segment * loops
                    bgm_segment = bgm_segment[:len(final_mix)]
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
            # 1. Transcribe
            text = self.transcribe_audio(audio_path)

            # 2. Translate
            logger.info(f"Translating to {target_lang}...")
            trans_lang = 'zh-CN' if target_lang == 'zh' else target_lang
            translated_text = GoogleTranslator(source='auto', target=trans_lang).translate(text)
            logger.info(f"Translated: {translated_text[:50]}...")

            # 3. Clone original voice for synthesis
            self.set_speaker_profile("original", {"type": "clone", "value": audio_path})

            # 4. Synthesize with target language
            wav, sr = self.generate_segment("original", translated_text, language=target_lang)

            return {"waveform": wav, "sample_rate": sr, "text": translated_text}
        except Exception as e:
            logger.error(f"Dubbing failed: {e}")
            raise RuntimeError(f"Dubbing failed: {e}")
