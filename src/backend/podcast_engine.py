import torch
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
from .model_loader import get_model, manager
from .config import verify_system_paths, logger

# Constants for presets
PRESET_SPEAKERS = ["aiden", "dylan", "eric", "ono_anna", "ryan", "serena", "sohee", "uncle_fu", "vivian"]

class PodcastEngine:
    def __init__(self):
        self.speaker_profiles = {}  # Map "Role Name" -> {type: "preset"|"design"|"clone", value: "Ryan"|"Description"|"/path/to/ref.wav"}

    def get_system_status(self) -> Dict[str, Any]:
        """Diagnostic summary of the system.

        Queries the configuration and model manager to report the current
        health and capabilities of the backend.

        Returns:
            dict: A dictionary containing:
                - status (str): "ok" or "error".
                - models (dict): Result of verify_system_paths().
                - device (dict): Information about the compute device (CPU/CUDA).
                - loaded_model (str): The key of the currently loaded model, if any.
                - performance (dict): Current CPU and Memory utilization.
        """
        try:
            import psutil
            paths = verify_system_paths()
            
            # Simple performance metrics
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
        """
        Define a speaker.
        config: {"type": "preset", "value": "Ryan"} 
             or {"type": "design", "value": "A happy female voice"}
             or {"type": "clone", "value": "path/to/ref.wav"}
        """
        self.speaker_profiles[role] = config

    def generate_segment(self, role: str, text: str) -> np.ndarray:
        """
        Generate audio for a single segment logic.
        """
        profile = self.speaker_profiles.get(role)
        if not profile:
            # Default fallback
            profile = {"type": "preset", "value": "Ryan"}
            
        logger.info(f"Synthesis starting for role '{role}' ({profile['type']}): {text[:30]}...")
            
        try:
            wavs = []
            if profile["type"] == "preset":
                model = get_model("CustomVoice") 
                logger.debug(f"Model loaded. Starting inference for {role}...")
                wavs, sr = model.generate_custom_voice(
                    text=text,
                    speaker=profile["value"], 
                    language="auto"
                )
            elif profile["type"] == "design":
                model = get_model("VoiceDesign")
                logger.debug(f"Model loaded. Starting VoiceDesign inference...")
                wavs, sr = model.generate_voice_design(
                    text=text,
                    instruct=profile["value"],
                    language="auto",
                    non_streaming_mode=True
                )
            elif profile["type"] == "clone":
                ref_path = profile["value"]
                if not Path(ref_path).exists():
                    logger.error(f"Cloning reference audio NOT found at: {ref_path}")
                    raise FileNotFoundError(f"Cloning reference audio not found: {ref_path}")
                    
                model = get_model("Base")
                logger.debug(f"Model loaded. Starting VoiceClone inference...")
                wavs, sr = model.generate_voice_clone(
                    text=text,
                    language="auto",
                    ref_audio=ref_path,
                    x_vector_only_mode=True,
                )
            else:
                logger.error(f"Unknown speaker type requested: {profile['type']}")
                raise ValueError(f"Unknown speaker type: {profile['type']}")
                
            logger.info(f"Synthesis complete for role '{role}'!")
            return wavs[0], sr
            
        except Exception as e:
            logger.error(f"Synthesis failed for role '{role}': {e}", exc_info=True)
            raise RuntimeError(f"Synthesis failed for role '{role}': {str(e)}") from e

    def generate_podcast(self, script: List[Dict[str, Any]], bgm_mood: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate the full podcast with optional background music, respecting 'start_time' if provided.
        """
        from pydub import AudioSegment
        import io

        # 1. Generate all segments first
        segments = []
        sample_rate = 24000
        
        # Calculate total duration needed
        max_duration_ms = 0

        current_offset_ms = 0
        
        for item in script:
            role = item["role"]
            text = item["text"]
            # Start time in seconds, convert to ms
            start_time = item.get("start_time", None) 
            
            try:
                wav, sr = self.generate_segment(role, text)
                sample_rate = sr
                
                # Convert to pydub
                # Normalize float32 to int16
                wav_int16 = (wav * 32767).astype(np.int16)
                seg = AudioSegment(
                    wav_int16.tobytes(), 
                    frame_rate=sr,
                    sample_width=2, 
                    channels=1
                )
                
                # Determine placement
                if start_time is not None:
                    position_ms = int(float(start_time) * 1000)
                else:
                    position_ms = current_offset_ms
                
                segments.append({"audio": seg, "position": position_ms})
                
                # Update linear offset for next fallback
                current_offset_ms = position_ms + len(seg) + 500 # +0.5s silence gap default
                
                # Track max duration
                end_pos = position_ms + len(seg)
                if end_pos > max_duration_ms:
                    max_duration_ms = end_pos
                    
            except Exception as e:
                import traceback
                print(f"Error generating segment for {role}: {e}")
                traceback.print_exc()
                continue
                
        if not segments:
            return None

        # 2. Create canvas
        # Add 2 seconds padding at end
        final_mix = AudioSegment.silent(duration=max_duration_ms + 2000, frame_rate=sample_rate)
        
        # 3. Mix voices
        for seg in segments:
            final_mix = final_mix.overlay(seg["audio"], position=seg["position"])

        # 4. Mix Background Music
        if bgm_mood:
            try:
                # Find BGM file
                bgm_dir = Path(__file__).resolve().parent.parent / "bgm"
                bgm_file = bgm_dir / f"{bgm_mood}.mp3" 

                if bgm_file.exists():
                    bgm_segment = AudioSegment.from_file(bgm_file)
                    # Lower BGM volume and loop
                    bgm_segment = bgm_segment - 20 # -20dB
                    
                    # Loop bgm to match voice length
                    # Simple loop:
                    if len(bgm_segment) < len(final_mix):
                        loops = int(len(final_mix) / len(bgm_segment)) + 1
                        bgm_segment = bgm_segment * loops
                        
                    bgm_segment = bgm_segment[:len(final_mix)] # Trim
                    
                    final_mix = final_mix.overlay(bgm_segment)
                else:
                    print(f"BGM file {bgm_file} not found, skipping mix.")

            except Exception as e:
                import traceback
                print(f"BGM mixing failed: {e}")
                traceback.print_exc()

        # 5. Export to numpy for return
        # pydub to numpy float32
        samples = np.array(final_mix.get_array_of_samples())
        
        # If stereo, pydub returns flat array [L, R, L, R]. 
        # But we forced channels=1 on creation, and BGM might change it?
        # AudioSegment.overlay usually maintains channels of base?
        # Let's ensure mono for now or handle stereo.
        if final_mix.channels == 2:
            samples = samples.reshape((-1, 2))
            # Convert to mono by averaging
            samples = samples.mean(axis=1)
            
        final_wav = samples.astype(np.float32) / 32768.0

        # Normalization
        max_val = np.max(np.abs(final_wav))
        if max_val > 1.0:
            final_wav = final_wav / max_val

        return {"waveform": final_wav, "sample_rate": sample_rate}
