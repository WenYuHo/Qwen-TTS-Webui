import os
import sys
import numpy as np
import soundfile as sf
import time
from pathlib import Path

# Add src to path
sys.path.append(os.path.abspath("src"))

from backend.server_state import engine

def test():
    print("--- Starting MINIMAL Synthesis Test ---")
    text = "Short test."
    profile = {"type": "preset", "value": "Ryan"}
    
    try:
        # 1. Test basic synthesis
        print(f"Synthesizing: '{text}'")
        start_time = time.time()
        result = engine.generate_segment(text, profile)
        wav, sr = result
        end_time = time.time()
        
        output_path = "test_synthesis.wav"
        sf.write(output_path, wav, sr)
        print(f"✅ Synthesis successful ({end_time - start_time:.2f}s). Saved to {output_path}")
        
        # 2. Test Voice Changer (S2S)
        print("\n--- Starting Voice Changer (S2S) Test ---")
        target_profile = {"type": "preset", "value": "Aiden"}
        abs_source_path = os.path.abspath(output_path)
        print(f"Changing voice of {abs_source_path} to {target_profile['value']}")
        
        start_time = time.time()
        # Voice changer also runs transcription first
        vc_result = engine.generate_voice_changer(abs_source_path, target_profile)
        vc_wav = vc_result["waveform"]
        vc_sr = vc_result["sample_rate"]
        vc_text = vc_result["text"]
        end_time = time.time()
        
        vc_output_path = "test_voice_changer.wav"
        sf.write(vc_output_path, vc_wav, vc_sr)
        print(f"✅ Voice Changer successful ({end_time - start_time:.2f}s). Transcribed: '{vc_text}'")
        print(f"✅ Saved changed voice to {vc_output_path}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test()
