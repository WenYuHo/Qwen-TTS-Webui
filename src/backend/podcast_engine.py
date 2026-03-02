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

from .qwen_tts.inference.qwen3_tts_model import VoiceClonePromptItem
from .model_loader import get_model
from .config import BASE_DIR, logger
from .video_engine import VideoEngine
from .utils import phoneme_manager

class PodcastEngine:
    def __init__(self):
        self.upload_dir = Path("uploads").resolve()
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        # Caches
        self.preset_embeddings = {}
        self.clone_embedding_cache = {}
        self.mix_embedding_cache = {}
        self.bgm_cache = {}
        self.prompt_cache = {}
        # ⚡ Bolt: Cache for extracted audio paths to avoid redundant Video-to-Audio processing
        # ⚡ Bolt: Caches for transcription and translation to avoid redundant processing
        self.transcription_cache = {}
        self.translation_cache = {}
        self.video_audio_cache = {}

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
                video_dir = (Path(BASE_DIR) / "projects" / "videos").resolve()
                is_safe = path_obj.is_relative_to(video_dir)

            if not is_safe:
                # Check shared assets
                from .config import SHARED_ASSETS_DIR
                is_safe = path_obj.is_relative_to(SHARED_ASSETS_DIR.resolve())

            if not is_safe:
                logger.error(f"Access denied to path: {path_obj}")
                raise PermissionError(f"Access denied to path outside allowed directories")
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

    def _extract_audio_with_cache(self, video_path: str) -> str:
        """Extracts audio from video or returns cached path if already extracted."""
        if video_path in self.video_audio_cache:
            cached_path = self.video_audio_cache[video_path]
            if Path(cached_path).exists():
                logger.debug(f"⚡ Bolt: Using cached audio for {video_path}")
                return cached_path

        extracted_path = VideoEngine.extract_audio(video_path)
        self.video_audio_cache[video_path] = extracted_path
        return extracted_path

    def transcribe_audio(self, audio_path: str) -> str:
        """Transcribe audio or video file with caching."""
        resolved = self._resolve_paths(audio_path)
        actual_path = str(resolved[0])

        if VideoEngine.is_video(actual_path):
            actual_path = self._extract_audio_with_cache(actual_path)

        # ⚡ Bolt: Cache transcription based on file path, size, and mtime to avoid redundant Whisper runs
        try:
            path_obj = Path(actual_path)
            if path_obj.exists():
                stat = path_obj.stat()
                cache_key = f"{actual_path}:{stat.st_size}:{stat.st_mtime}"
                if cache_key in self.transcription_cache:
                    logger.debug(f"⚡ Bolt: Using cached transcription for {actual_path}")
                    return self.transcription_cache[cache_key]
            else:
                cache_key = None
        except Exception:
            cache_key = None

        if self._whisper_model is None:
            import whisper
            logger.info("Loading Whisper model...")
            self._whisper_model = whisper.load_model("base")

        logger.info(f"Transcribing {actual_path}...")
        result = self._whisper_model.transcribe(actual_path)
        text = result["text"]
        if cache_key:
            self.transcription_cache[cache_key] = text
        return text
    def get_speaker_embedding(self, profile: Dict[str, str], model: Optional[Any] = None) -> Optional[torch.Tensor]:
        """Extract speaker embedding for any profile, with optional pre-loaded model."""
        # ⚡ Bolt: Check caches first to avoid expensive extraction and model switches
        # Unified cache check: prompt_cache and clone_embedding_cache should be in sync
        ptype = profile.get("type")
        if ptype == "preset":
            name = profile["value"].lower()
            if name in self.preset_embeddings:
                return self.preset_embeddings[name]
        elif ptype == "clone":
            cache_key = profile["value"]
            if cache_key in self.prompt_cache:
                return self.prompt_cache[cache_key][0].ref_spk_embedding
            if cache_key in self.clone_embedding_cache:
                return self.clone_embedding_cache[cache_key]

        # ⚡ Bolt: Reuse passed model to avoid redundant ModelManager lookups
        if model is None:
            # Preset lookups are fast even on CustomVoice model; Clones need Base model
            mtype = "Base" if ptype == "clone" else "CustomVoice"
            model = get_model(mtype)

        if ptype == "preset":
            emb = model.get_speaker_embedding(profile["value"])
            self.preset_embeddings[profile["value"].lower()] = emb
            return emb
        elif ptype == "clone":
            cache_key = profile["value"]
            resolved = self._resolve_paths(cache_key)
            # Handle Video for cloning if needed
            clone_path = str(resolved[0])
            if VideoEngine.is_video(clone_path):
                clone_path = self._extract_audio_with_cache(clone_path)

            logger.info(f"⚡ Bolt: Extracting embedding for {cache_key} (via get_speaker_embedding)")
            prompt = model.create_voice_clone_prompt(ref_audio=clone_path, x_vector_only_mode=True)
            emb = prompt[0].ref_spk_embedding

            # Sync unified caches
            self.prompt_cache[cache_key] = prompt
            self.clone_embedding_cache[cache_key] = emb
            return emb
        return None

    def generate_segment(self, text: str, profile: Dict[str, Any], language: str = "auto", model: Optional[Any] = None, instruct: Optional[str] = None) -> tuple[np.ndarray, int]:
        """Generates a single audio segment for a given speaker profile with optional emotional instructions."""
        try:
            # Priority: explicitly passed instruct > profile['instruct']
            final_instruct = instruct or profile.get("instruct")

            if profile["type"] == "preset":
                if model is None:
                    model = get_model("CustomVoice")
                wavs, sr = model.generate_custom_voice(
                    text=text,
                    speaker=profile["value"], 
                    language=language,
                    instruct=final_instruct
                )
            elif profile["type"] == "design":
                if model is None:
                    model = get_model("VoiceDesign")
                # VoiceDesign uses the value itself as the instruction, but we can append emotional cues
                design_instruct = profile["value"]
                if final_instruct:
                    design_instruct = f"{design_instruct}, {final_instruct}"
                
                wavs, sr = model.generate_voice_design(
                    text=text,
                    instruct=design_instruct,
                    language=language,
                    non_streaming_mode=True
                )
            elif profile.get("type") == "clone":
                cache_key = profile["value"]

                if cache_key in self.prompt_cache:
                    logger.debug(f"⚡ Bolt: Using cached prompt for {cache_key}")
                    prompt = self.prompt_cache[cache_key]
                else:
                    try:
                        resolved_paths = self._resolve_paths(profile["value"])
                    except FileNotFoundError as e:
                        raise RuntimeError(f"Cloning reference audio not found: {e}") from e

                    if model is None:
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
                            ref_audio = self._extract_audio_with_cache(ref_audio)

                    logger.info(f"⚡ Bolt: Extracting voice clone prompt for {cache_key} (via generate_segment)")
                    prompt = model.create_voice_clone_prompt(ref_audio=ref_audio, x_vector_only_mode=True)
                    self.prompt_cache[cache_key] = prompt

                if model is None:
                    model = get_model("Base")
                wavs, sr = model.generate_voice_clone(
                    text=text,
                    language=language,
                    voice_clone_prompt=prompt,
                    instruct=final_instruct
                )
            elif profile.get("type") == "mix":
                # ⚡ Bolt: Use unified prompt cache for mixed voices too
                cache_key = f"mix:{profile['value']}"
                if cache_key in self.prompt_cache:
                    logger.debug(f"⚡ Bolt: Using cached prompt for {cache_key}")
                    prompt = self.prompt_cache[cache_key]
                else:
                    mix_configs = json.loads(profile["value"])
                    mixed_emb = self._compute_mixed_embedding(mix_configs)
                    # Use list format for generate_voice_clone compat
                    prompt = [VoiceClonePromptItem(
                        ref_code=None,
                        ref_spk_embedding=mixed_emb,
                        x_vector_only_mode=True,
                        icl_mode=False,
                        ref_text=None
                    )]
                    self.prompt_cache[cache_key] = prompt

                if model is None:
                    model = get_model("Base")
                wavs, sr = model.generate_voice_clone(
                    text=text,
                    language=language,
                    voice_clone_prompt=prompt,
                    instruct=final_instruct
                )
            else:
                raise ValueError(f"Unknown speaker type: {profile['type']}")
                
            if not wavs:
                raise RuntimeError("Engine returned no waveforms")

            return wavs[0], sr
            
        except Exception as e:
            logger.error(f"Synthesis failed: {e}", exc_info=True)
            raise RuntimeError(f"Synthesis failed: {str(e)}") from e

    def _compute_mixed_embedding(self, mix_configs: List[Dict[str, Any]], model: Optional[Any] = None) -> Optional[torch.Tensor]:
        """Compute a weighted average of multiple speaker embeddings with caching and optional model reuse."""
        # ⚡ Bolt: Cache mix results to avoid redundant tensor ops and model switches
        # Sort by profile values to ensure identical mixes have the same key
        cache_key = json.dumps(sorted(mix_configs, key=lambda x: str(x["profile"])), sort_keys=True)
        if cache_key in self.mix_embedding_cache:
            return self.mix_embedding_cache[cache_key]

        total_weight = sum(c["weight"] for c in mix_configs)
        if total_weight == 0:
            return None

        mixed_emb = None
        for config in mix_configs:
            # ⚡ Bolt: Pass model down to avoid redundant lookups
            emb = self.get_speaker_embedding(config["profile"], model=model)
            weight = config["weight"] / total_weight
            if mixed_emb is None:
                mixed_emb = emb * weight
            else:
                mixed_emb += emb * weight

        self.mix_embedding_cache[cache_key] = mixed_emb
        return mixed_emb

    def stream_synthesize(self, text: str, profile: Dict[str, Any], language: str = "auto", instruct: Optional[str] = None):
        """
        Yields audio chunks for the given text and profile to support low-latency previews.
        Uses a simple sentence-based chunking strategy for the 'Dual-Track' streaming feel.
        """
        import re
        # Split text into small chunks (sentences or phrases)
        chunks = re.split(r'([.!?。！？\n]+)', text)
        processed_chunks = []
        for i in range(0, len(chunks)-1, 2):
            c = chunks[i] + chunks[i+1]
            if c.strip():
                processed_chunks.append(c.strip())
        if len(chunks) % 2 == 1 and chunks[-1].strip():
            processed_chunks.append(chunks[-1].strip())

        if not processed_chunks:
            processed_chunks = [text]

        for chunk_text in processed_chunks:
            try:
                wav, sr = self.generate_segment(chunk_text, profile, language=language, instruct=instruct)
                yield wav, sr
            except Exception as e:
                logger.error(f"Streaming chunk failed: {e}")
                continue

    def generate_voice_changer(self, source_audio: str, target_profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Preserve prosody of source while changing voice to target."""
        try:
            # 1. Transcribe source
            text = self.transcribe_audio(source_audio)

            # 2. Extract codes from source
            resolved = self._resolve_paths(source_audio)
            source_path = str(resolved[0])

            if VideoEngine.is_video(source_path):
                source_path = self._extract_audio_with_cache(source_path)

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

    def generate_podcast(self, script: List[Dict[str, Any]], profiles: Dict[str, Dict[str, Any]], bgm_mood: Optional[str] = None, ducking_level: float = 0.0) -> Optional[Dict[str, Any]]:
        sample_rate = 24000

        # 1. Pre-map indices to model types for grouping to prevent model thrashing
        model_groups = {} # model_type -> list of (index, item)
        clones_to_extract = {} # cache_key -> profile (for Base model batch extraction)

        for i, item in enumerate(script):
            role = item["role"]
            profile = profiles.get(role, {"type": "preset", "value": "Ryan"})
            ptype = profile.get("type")
            mtype = self._get_model_type_for_profile(profile)

            if mtype not in model_groups:
                model_groups[mtype] = []
            model_groups[mtype].append((i, item))

            # ⚡ Bolt: Identify missing cloned voices for batched extraction later
            if ptype == "clone":
                cache_key = profile["value"]
                if cache_key not in self.prompt_cache:
                    clones_to_extract[cache_key] = profile
            elif ptype == "mix":
                # For mixed voices, we might need to extract component clones
                mix_configs = json.loads(profile["value"])
                for config in mix_configs:
                    sub_profile = config["profile"]
                    if sub_profile.get("type") == "clone":
                        sub_cache_key = sub_profile["value"]
                        if sub_cache_key not in self.prompt_cache:
                            clones_to_extract[sub_cache_key] = sub_profile

        # ⚡ Bolt: Perform batched voice clone prompt extraction for all unique missing clones
        # This leverages the optimized batched extraction in Qwen3TTSModel
        if clones_to_extract:
            logger.info(f"⚡ Bolt: Batched prompt extraction for {len(clones_to_extract)} unique clones")
            base_model = get_model("Base")

            ref_audios = []
            cache_keys = []

            for cache_key, profile in clones_to_extract.items():
                resolved = self._resolve_paths(profile["value"])
                ref_audio = str(resolved[0])
                if VideoEngine.is_video(ref_audio):
                    ref_audio = self._extract_audio_with_cache(ref_audio)

                # Note: We don't handle multi-path pro-cloning in the batch extraction yet for simplicity
                # but single-path (most common) is fully batched.
                ref_audios.append(ref_audio)
                cache_keys.append(cache_key)

            try:
                # Optimized batched call
                prompts = base_model.create_voice_clone_prompt(ref_audio=ref_audios, x_vector_only_mode=True)
                for cache_key, prompt in zip(cache_keys, prompts):
                    self.prompt_cache[cache_key] = [prompt]
                    # Also sync embedding cache
                    self.clone_embedding_cache[cache_key] = prompt.ref_spk_embedding
            except Exception as e:
                logger.error(f"⚡ Bolt: Batched extraction failed, will fallback to individual: {e}")

        # 2. Batch synthesis by model type to minimize switches
        waveforms = [None] * len(script)
        srs = [None] * len(script)

        for mtype, group in model_groups.items():
            logger.info(f"⚡ Bolt: Batched synthesis for model '{mtype}' ({len(group)} segments)")
            # ⚡ Bolt: Fetch model once per group to reduce lock contention and redundant lookups
            group_model = get_model(mtype)

            # Collect batch parameters
            batch_texts = []
            batch_langs = []
            batch_indices = []

            # Model-specific collections
            batch_instructs = []   # Common for all

            for i, item in group:
                role = item["role"]
                profile = profiles.get(role, {"type": "preset", "value": "Ryan"})
                batch_texts.append(item["text"])
                batch_langs.append(item.get("language", "auto"))
                batch_indices.append(i)
                
                # Instruction priority: item['instruct'] > profile['instruct']
                instruct = item.get("instruct") or profile.get("instruct")
                
                if mtype == "VoiceDesign":
                    # For VoiceDesign, the 'instruct' IS the voice description
                    design_instruct = profile["value"]
                    if instruct:
                        design_instruct = f"{design_instruct}, {instruct}"
                    batch_instructs.append(design_instruct)
                else:
                    batch_instructs.append(instruct)

                if mtype == "CustomVoice":
                    batch_speakers.append(profile["value"])
                elif mtype == "Base":
                    # ⚡ Bolt: Use unified prompt cache for both Clone and Mix in batch mode
                    ptype = profile.get("type")
                    val = profile.get("value")
                    cache_key = val if ptype == "clone" else f"mix:{val}"

                    if val is not None and cache_key in self.prompt_cache:
                        batch_prompts.append(self.prompt_cache[cache_key][0])
                    else:
                        # Should mostly be handled by the pre-extraction step now, but fallback provided
                        if ptype == "clone":
                            # Extraction needed (similar to generate_segment logic)
                            resolved = self._resolve_paths(profile["value"])
                            ref_audio = str(resolved[0])
                            if VideoEngine.is_video(ref_audio):
                                ref_audio = self._extract_audio_with_cache(ref_audio)

                            logger.info(f"⚡ Bolt: Individual extraction for {cache_key} (batch synthesis fallback)")
                            prompt = group_model.create_voice_clone_prompt(ref_audio=ref_audio, x_vector_only_mode=True)
                            self.prompt_cache[cache_key] = prompt
                            batch_prompts.append(prompt[0])
                        elif ptype == "mix":
                            mix_configs = json.loads(profile["value"])
                            # ⚡ Bolt: Pass group_model to avoid redundant lookups
                            mixed_emb = self._compute_mixed_embedding(mix_configs, model=group_model)
                            # Create prompt item manually for Mix and cache it
                            prompt = [VoiceClonePromptItem(
                                ref_code=None,
                                ref_spk_embedding=mixed_emb,
                                x_vector_only_mode=True,
                                icl_mode=False,
                                ref_text=None
                            )]
                            self.prompt_cache[cache_key] = prompt
                            batch_prompts.append(prompt[0])

            try:
                # Execute batch synthesis
                if mtype == "CustomVoice":
                    batch_wavs, sr = group_model.generate_custom_voice(
                        text=batch_texts,
                        speaker=batch_speakers,
                        language=batch_langs,
                        instruct=batch_instructs
                    )
                elif mtype == "VoiceDesign":
                    batch_wavs, sr = group_model.generate_voice_design(
                        text=batch_texts,
                        instruct=batch_instructs,
                        language=batch_langs,
                        non_streaming_mode=True
                    )
                elif mtype == "Base":
                    batch_wavs, sr = group_model.generate_voice_clone(
                        text=batch_texts,
                        language=batch_langs,
                        voice_clone_prompt=batch_prompts,
                        instruct=batch_instructs
                    )
                else:
                    raise ValueError(f"Batching not implemented for model type: {mtype}")

                # Map results back
                for j, wav in enumerate(batch_wavs):
                    idx = batch_indices[j]
                    waveforms[idx] = wav
                    srs[idx] = sr

            except Exception as e:
                logger.error(f"⚡ Bolt: Batch synthesis failed for model '{mtype}': {e}", exc_info=True)
                # Fallback to serial generation if batching fails (safety first)
                for i, item in group:
                    if waveforms[i] is not None: continue
                    try:
                        wav, sr = self.generate_segment(item["text"], profile=profiles.get(item["role"]), language=item.get("language", "auto"), model=group_model)
                        waveforms[i] = wav
                        srs[i] = sr
                    except Exception as inner_e:
                        logger.error(f"Serial fallback failed for segment {i}: {inner_e}")

        # 3. Assemble chronological mix using vectorized NumPy operations
        # ⚡ Bolt: Vectorized assembly is ~10-100x faster than AudioSegment overlay for large projects
        # This replaces expensive AudioSegment slicing/overlay loops with O(N) NumPy slice assignment.
        speech_segments = []
        max_sample = 0
        current_sample_offset = 0

        for i, item in enumerate(script):
            if waveforms[i] is None:
                continue

            wav = waveforms[i]
            sr = srs[i]
            sample_rate = sr # Assume consistency
            pause_after = item.get("pause_after", 0.5)
            start_time = item.get("start_time", None)

            start_sample = int(float(start_time) * sr) if start_time is not None else current_sample_offset
            end_sample = start_sample + len(wav)

            speech_segments.append({"wav": wav, "start": start_sample, "end": end_sample})
            
            current_sample_offset = end_sample + int(pause_after * sr)
            if end_sample > max_sample:
                max_sample = end_sample

        if not speech_segments:
            return None

        # Pre-allocate final waveform with 2.0s tail padding
        final_length = max_sample + int(2.0 * sample_rate)
        speech_wav = np.zeros(final_length, dtype=np.float32)

        # Place speech segments into the pre-allocated array
        for seg in speech_segments:
            speech_wav[seg["start"]:seg["end"]] = seg["wav"]

        final_wav = speech_wav

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
                    bgm_full_path = (Path(BASE_DIR) / "bgm" / f"{bgm_mood}").resolve()
                    if not bgm_full_path.exists() and not (bgm_mood.endswith(".mp3") or bgm_mood.endswith(".wav")):
                         bgm_full_path = (Path(BASE_DIR) / "bgm" / f"{bgm_mood}.mp3").resolve()

                    if bgm_full_path.exists():
                        bgm_file = bgm_full_path

                if bgm_file:
                    # ⚡ Bolt: Cache processed BGM to avoid redundant loading/resampling/conversion
                    bgm_cache_key = f"{bgm_file}:{sample_rate}"
                    if bgm_cache_key in self.bgm_cache:
                        bgm_samples = self.bgm_cache[bgm_cache_key].copy()
                    else:
                        # Load BGM and ensure it matches the project sample rate
                        # We use AudioSegment for loading due to its broad format support
                        bgm_audio = AudioSegment.from_file(bgm_file).set_frame_rate(sample_rate).set_channels(1)
                        # Convert to float32 NumPy array and normalize to [-1, 1]
                        bgm_samples = np.array(bgm_audio.get_array_of_samples(), dtype=np.float32) / 32768.0

                        # Apply initial volume reduction (equivalent to -20dB in previous logic)
                        bgm_samples *= 0.1
                        self.bgm_cache[bgm_cache_key] = bgm_samples.copy()

                    # Tile BGM to match final project duration
                    if len(bgm_samples) < final_length:
                        repeats = int(np.ceil(final_length / len(bgm_samples)))
                        bgm_samples = np.tile(bgm_samples, repeats)
                    bgm_samples = bgm_samples[:final_length]

                    # Perform vectorized sidechain ducking
                    if ducking_level > 0:
                        # Convert target dB reduction to linear gain factor
                        # Original logic: ducking_db = - (ducking_level * 25)
                        duck_factor = 10 ** (-(ducking_level * 25) / 20.0)

                        # Apply ducking factor directly to slices where speech is active
                        for seg in speech_segments:
                            bgm_samples[seg["start"]:seg["end"]] *= duck_factor

                    # Mix speech and BGM arrays
                    final_wav = speech_wav + bgm_samples

            except Exception as e:
                logger.error(f"BGM mixing failed: {e}")

        # Final normalization to prevent clipping
        max_val = np.max(np.abs(final_wav))
        if max_val > 1.0:
            # ⚡ Bolt: Use in-place division to avoid extra array allocation
            final_wav /= max_val

        return {"waveform": final_wav, "sample_rate": sample_rate}

    def dub_audio(self, audio_path: str, target_lang: str) -> Optional[Dict[str, Any]]:
        """Dub audio by transcribing, translating, and synthesizing."""
        try:
            # 1. Transcribe (Handles Video automatically)
            text = self.transcribe_audio(audio_path)

            # 2. Translate with caching
            # ⚡ Bolt: Cache translation to avoid redundant API calls to Google Translator
            trans_lang = 'zh-CN' if target_lang == 'zh' else target_lang
            trans_cache_key = f"{text}:{trans_lang}"
            if trans_cache_key in self.translation_cache:
                logger.debug(f"⚡ Bolt: Using cached translation for {target_lang}")
                translated_text = self.translation_cache[trans_cache_key]
            else:
                logger.info(f"Translating to {target_lang}...")
                translated_text = GoogleTranslator(source='auto', target=trans_lang).translate(text)
                self.translation_cache[trans_cache_key] = translated_text
            logger.info(f"Translated: {translated_text[:50]}...")

            # 3. Clone original voice for synthesis (Handles Video automatically)
            original_profile = {"type": "clone", "value": audio_path}

            # 4. Synthesize with target language
            wav, sr = self.generate_segment(translated_text, profile=original_profile, language=target_lang)

            return {"waveform": wav, "sample_rate": sr, "text": translated_text}
        except Exception as e:
            logger.error(f"Dubbing failed: {e}")
            raise RuntimeError(f"Dubbing failed: {e}")
