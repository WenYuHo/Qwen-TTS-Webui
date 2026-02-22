import torch
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
import io
import soundfile as sf
from .model_loader import get_model, manager
from .config import verify_system_paths, logger, BASE_DIR

# Constants for presets
PRESET_SPEAKERS = ["aiden", "dylan", "eric", "ono_anna", "ryan", "serena", "sohee", "uncle_fu", "vivian"]

class PodcastEngine:
    def __init__(self):
        self.speaker_profiles = {}  # Map "Role Name" -> {type: "preset"|"design"|"clone", value: "Ryan"|"Description"|"filename"}
        self._whisper_model = None
        self.upload_dir = Path(BASE_DIR) / "uploads"
        if not self.upload_dir.exists():
            self.upload_dir.mkdir(parents=True)

    def _resolve_path(self, relative_path: str) -> Path:
        """Resolve a relative path against upload_dir and ensure it's safe."""
        # Handle multiple paths for pro cloning (separated by |)
        paths = relative_path.split("|")
        resolved = []
        for p in paths:
            # If it's already an absolute path and inside upload_dir, it's okay (for internal calls)
            # But we prefer filenames.
            path_obj = Path(p)
            if not path_obj.is_absolute():
                path_obj = (self.upload_dir / path_obj).resolve()
            else:
                path_obj = path_obj.resolve()

            if not str(path_obj).startswith(str(self.upload_dir.resolve())):
                # Also allow bgm directory
                bgm_dir = (Path(BASE_DIR) / "bgm").resolve()
                if not str(path_obj).startswith(str(bgm_dir)):
                     raise ValueError(f"Access denied to path: {p}")

            if not path_obj.exists():
                raise FileNotFoundError(f"File not found: {p}")
            resolved.append(path_obj)

        return resolved

    def get_system_status(self) -> Dict[str, Any]:
        try:
            import psutil
            paths = verify_system_paths()
            perf = {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent
            }
            return {
                "status": "ok",
                "models": paths,
                "device": {
                    "type": manager.device,
                    "cuda_available": torch.cuda.is_available()
                },
                "loaded_model": manager.current_model_type,
                "performance": perf
            }
        except Exception as e:
            logger.error(f"Health check diagnostics failed: {e}")
            return {"status": "error", "message": str(e)}

    def set_speaker_profile(self, role: str, config: Dict[str, str]):
        self.speaker_profiles[role] = config

    def transcribe_audio(self, audio_path: str) -> str:
        """Transcribe audio using Whisper."""
        try:
            import whisper
            if self._whisper_model is None:
                logger.info("Loading Whisper model (base)...")
                self._whisper_model = whisper.load_model("base", device=manager.device)

            # Resolve path if it's relative
            resolved_paths = self._resolve_path(audio_path)
            safe_path = str(resolved_paths[0])

            logger.info(f"Transcribing audio: {safe_path}")
            result = self._whisper_model.transcribe(safe_path)
            text = result["text"].strip()
            logger.info(f"Transcription complete: {text[:50]}...")
            return text
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise RuntimeError(f"Transcription failed: {e}")

    def generate_segment(self, role: str, text: str) -> tuple:
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
                    language="auto"
                )
            elif profile["type"] == "design":
                model = get_model("VoiceDesign")
                wavs, sr = model.generate_voice_design(
                    text=text,
                    instruct=profile["value"],
                    language="auto",
                    non_streaming_mode=True
                )
            elif profile["type"] == "clone":
                resolved_paths = self._resolve_path(profile["value"])

                if len(resolved_paths) > 1:
                    logger.info(f"Combining {len(resolved_paths)} reference audios for professional cloning")
                    combined_wav = []
                    target_sr = 24000
                    for path_obj in resolved_paths:
                        w, s = sf.read(str(path_obj))
                        if s != target_sr:
                            import librosa
                            w = librosa.resample(w, orig_sr=s, target_sr=target_sr)
                        combined_wav.append(w)
                    
                    concatenated = np.concatenate(combined_wav)
                    import uuid
                    temp_ref = self.upload_dir / f"combined_{uuid.uuid4()}.wav"
                    sf.write(str(temp_ref), concatenated, target_sr)
                    ref_audio = str(temp_ref)
                else:
                    ref_audio = str(resolved_paths[0])

                model = get_model("Base")
                wavs, sr = model.generate_voice_clone(
                    text=text,
                    language="auto",
                    ref_audio=ref_audio,
                    x_vector_only_mode=True,
                )
            else:
                raise ValueError(f"Unknown speaker type: {profile['type']}")
                
            if not wavs:
                raise RuntimeError("Engine returned no waveforms")

            return wavs[0], sr
            
        except Exception as e:
            logger.error(f"Synthesis failed for role '{role}': {e}", exc_info=True)
            raise RuntimeError(f"Synthesis failed for role '{role}': {str(e)}") from e

    def generate_podcast(self, script: List[Dict[str, Any]], bgm_mood: Optional[str] = None) -> Dict[str, Any]:
        from pydub import AudioSegment
        segments = []
        sample_rate = 24000
        max_duration_ms = 0
        current_offset_ms = 0
        
        for item in script:
            role = item["role"]
            text = item["text"]
            start_time = item.get("start_time", None) 
            
            try:
                wav, sr = self.generate_segment(role, text)
                sample_rate = sr
                wav_int16 = (wav * 32767).astype(np.int16)
                seg = AudioSegment(wav_int16.tobytes(), frame_rate=sr, sample_width=2, channels=1)
                
                position_ms = int(float(start_time) * 1000) if start_time is not None else current_offset_ms
                segments.append({"audio": seg, "position": position_ms})
                current_offset_ms = position_ms + len(seg) + 500
                
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
            # Transcribe will handle the path safety
            text = self.transcribe_audio(audio_path)

            # Translate
            from deep_translator import GoogleTranslator
            logger.info(f"Translating to {target_lang}...")
            translated_text = GoogleTranslator(source='auto', target=target_lang).translate(text)
            logger.info(f"Translated: {translated_text[:50]}...")

            # 3. Clone original voice for synthesis
            self.set_speaker_profile("original", {"type": "clone", "value": audio_path})

            # 4. Synthesize
            wav, sr = self.generate_segment("original", translated_text)

            return {"waveform": wav, "sample_rate": sr, "text": translated_text}
        except Exception as e:
            logger.error(f"Dubbing failed: {e}")
            raise RuntimeError(f"Dubbing failed: {e}")
