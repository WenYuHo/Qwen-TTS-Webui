import torch
import numpy as np
from typing import List, Dict, Any, Optional
import uuid
import uuid
from pathlib import Path
from ..qwen_tts.inference.qwen3_tts_model import VoiceClonePromptItem
from ..model_loader import get_model
from ..video_engine import VideoEngine
from ..utils import phoneme_manager, prune_dict_cache, audit_manager

import logging
logger = logging.getLogger("qwen_tts")

class VoiceSynthesizer:
    def __init__(self, upload_dir: Path, transcription_cache, translation_cache, prompt_cache, clone_embedding_cache, preset_embeddings, mix_embedding_cache, video_audio_cache, resolve_paths_func, extract_audio_func):
        self.upload_dir = upload_dir
        self.transcription_cache = transcription_cache
        self.translation_cache = translation_cache
        self.prompt_cache = prompt_cache
        self.clone_embedding_cache = clone_embedding_cache
        self.preset_embeddings = preset_embeddings
        self.mix_embedding_cache = mix_embedding_cache
        self.video_audio_cache = video_audio_cache
        
        self._resolve_paths = resolve_paths_func
        self._extract_audio_with_cache = extract_audio_func

    @staticmethod
    def _validate_ref_audio(audio_path: str) -> None:
        import soundfile as sf
        try:
            info = sf.info(audio_path)
            duration = info.duration
            if duration < 3.0:
                raise ValueError(f"Reference audio too short ({duration:.1f}s). Minimum 3 seconds required.")
            if duration > 30.0:
                raise ValueError(f"Reference audio too long ({duration:.1f}s). Maximum 30 seconds recommended for best quality.")
            
            audio_data, sr = sf.read(audio_path)
            # ⚡ Bolt: Memory-efficient RMS calculation avoids a temporary O(N) array for audio_data**2
            rms = np.sqrt(np.vdot(audio_data, audio_data) / audio_data.size)
            if rms < 0.001:
                raise ValueError("Reference audio appears to be silent. Please provide audio with speech.")
        except sf.SoundFileError as e:
            raise ValueError(f"Invalid audio file: {e}")

    @staticmethod
    def _compute_quality_score(wav: np.ndarray, sr: int) -> Dict[str, Any]:
        duration = len(wav) / sr
        # ⚡ Bolt: Memory-efficient RMS and peak calculation avoids O(N) temporary arrays for wav**2 and abs(wav)
        rms = float(np.sqrt(np.vdot(wav, wav) / wav.size))
        peak = float(max(np.max(wav), -np.min(wav)))
        tail = wav[-int(sr * 0.1):] if len(wav) > int(sr * 0.1) else wav
        noise_rms = float(np.sqrt(np.vdot(tail, tail) / tail.size)) + 1e-10
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

            prune_dict_cache(self.prompt_cache, limit=200, count=20)
            prune_dict_cache(self.clone_embedding_cache, limit=200, count=20)

            self.prompt_cache[cache_key] = prompt
            self.clone_embedding_cache[cache_key] = emb
            return emb
        return None

    def compute_mixed_embedding(self, mix_configs: List[Dict[str, Any]], model: Optional[Any] = None) -> Optional[torch.Tensor]:
        import json
        cache_key = json.dumps(sorted(mix_configs, key=lambda x: str(x["profile"])), sort_keys=True)
        if cache_key in self.mix_embedding_cache: return self.mix_embedding_cache[cache_key]

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

    def generate_segment(self, text: str, profile: Dict[str, Any], language: str = "auto", model: Optional[Any] = None, instruct: Optional[str] = None, temperature: Optional[float] = None, watermark_func=None, **gen_kwargs) -> tuple[np.ndarray, int]:
        try:
            import json
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
                    
                    self._validate_ref_audio(ref_audio)

                    if use_icl:
                        import soundfile as sf
                        audio_data, audio_sr = sf.read(ref_audio)
                        silence = np.zeros(int(audio_sr * 0.5), dtype=audio_data.dtype)
                        padded = np.concatenate([audio_data, silence])
                        padded_path = str(self.upload_dir / f"padded_{uuid.uuid4()}.wav")
                        sf.write(padded_path, padded, audio_sr)
                        ref_audio = padded_path

                    prompt = model.create_voice_clone_prompt(
                        ref_audio,
                        ref_text=ref_text if use_icl else None,
                        x_vector_only_mode=not use_icl
                    )
                    prune_dict_cache(self.prompt_cache, limit=200, count=20)
                    self.prompt_cache[icl_cache_key] = prompt
                if model is None: model = get_model("Base")
                wavs, sr = model.generate_voice_clone(text=text, language=language, voice_clone_prompt=prompt, instruct=final_instruct, temperature=temperature, **gen_kwargs)
            elif ptype == "mix":
                cache_key = f"mix:{profile['value']}"
                if cache_key in self.prompt_cache: prompt = self.prompt_cache[cache_key]
                else:
                    prune_dict_cache(self.prompt_cache, limit=200, count=20)
                    mix_configs = json.loads(profile["value"])
                    mixed_emb = self.compute_mixed_embedding(mix_configs)
                    prompt = [VoiceClonePromptItem(ref_code=None, ref_spk_embedding=mixed_emb, x_vector_only_mode=True, icl_mode=False, ref_text=None)]
                    self.prompt_cache[cache_key] = prompt
                if model is None: model = get_model("Base")
                wavs, sr = model.generate_voice_clone(text=text, language=language, voice_clone_prompt=prompt, instruct=final_instruct, temperature=temperature, **gen_kwargs)
            else:
                raise RuntimeError(f"Unknown speaker type: {ptype}")

            if not wavs: raise RuntimeError("No waveforms generated")
            
            wav_out = watermark_func(wavs[0], sr) if watermark_func else wavs[0]
            quality = self._compute_quality_score(wav_out, sr)
            logger.info(f"Segment quality: {quality}")
            audit_manager.log_event("synthesis", {"quality": quality, "profile_type": ptype}, quality["quality"])

            if quality["quality"] == "warning" and not gen_kwargs.get("_is_retry"):
                logger.warning(f"Low quality detected (SNR={quality['snr_db']}dB), retrying with lower temperature")
                retry_kwargs = {**gen_kwargs, "temperature": 0.3, "top_k": 20, "_is_retry": True}
                return self.generate_segment(text, profile, language, model, instruct, watermark_func=watermark_func, **retry_kwargs)

            return wav_out, sr
        except Exception as e:
            if not isinstance(e, RuntimeError):
                logger.error(f"Synthesis failed: {e}")
                raise RuntimeError(f"Synthesis failed: {e}") from e
            raise
