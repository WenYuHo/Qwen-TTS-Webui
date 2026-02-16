import torch
import numpy as np
from typing import List, Dict, Any
from .model_loader import get_model

# Constants for presets
PRESET_SPEAKERS = ["Ryan", "Aiden", "Serena", "Anna", "Tess"]  # Add more based on mapped availables

class PodcastEngine:
    def __init__(self):
        self.speaker_profiles = {}  # Map "Role Name" -> {type: "preset"|"design"|"clone", value: "Ryan"|"Description"|"/path/to/ref.wav"}

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
            
        print(f"Generating for {role} ({profile['type']}): {text[:30]}...")
            
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
                language="auto"
            )
        elif profile["type"] == "clone":
            # Assuming CustomVoice model supports path-based reference cloning
            model = get_model("CustomVoice")
            wavs, sr = model.generate_custom_voice(
                text=text,
                reference_audio_path=profile["value"],
                language="auto"
            )
        else:
            raise ValueError(f"Unknown speaker type: {profile['type']}")
            
        return wavs[0], sr

    def generate_podcast(self, script: List[Dict[str, str]], bgm_mood: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate the full podcast with optional background music.
        """
        all_audio = []
        sample_rate = 24000 # Default
        
        for segment in script:
            role = segment["role"]
            text = segment["text"]
            
            try:
                wav, sr = self.generate_segment(role, text)
                sample_rate = sr
                
                # Normalize shape (1-D array)
                if isinstance(wav, torch.Tensor):
                    wav = wav.cpu().numpy()
                
                if wav.ndim > 1:
                    wav = wav.flatten()
                    
                all_audio.append(wav)
                
                # Add small silence between segments (0.5s)
                silence = np.zeros(int(0.5 * sr), dtype=np.float32)
                all_audio.append(silence)
                
            except Exception as e:
                print(f"Error generating segment for {role}: {e}")
                continue
                
        if not all_audio:
            return None
            
        # Concatenate
        final_wav = np.concatenate(all_audio)

        # Mix Background Music
        if bgm_mood:
            try:
                from pydub import AudioSegment
                import io

                # Convert synthesized audio to pydub AudioSegment
                # (Assuming 16-bit PCM for pydub compatibility)
                int_wav = (final_wav * 32767).astype(np.int16)
                voice_segment = AudioSegment(
                    int_wav.tobytes(), 
                    frame_rate=sample_rate,
                    sample_width=2, 
                    channels=1
                )

                # Find BGM file
                bgm_dir = Path(__file__).resolve().parent.parent / "bgm"
                bgm_file = bgm_dir / f"{bgm_mood}.mp3" # or .wav

                if bgm_file.exists():
                    bgm_segment = AudioSegment.from_file(bgm_file)
                    # Lower BGM volume and loop it to match voice length
                    bgm_segment = bgm_segment - 20 # -20dB
                    mixed = voice_segment.overlay(bgm_segment, loop=True)
                    
                    # Convert back to numpy
                    final_wav = np.array(mixed.get_array_of_samples()).astype(np.float32) / 32768.0
                else:
                    print(f"BGM file {bgm_file} not found, skipping mix.")

            except Exception as e:
                print(f"BGM mixing failed: {e}")

        return {"waveform": final_wav, "sample_rate": sample_rate}
