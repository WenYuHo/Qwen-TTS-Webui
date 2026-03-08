import torch
import numpy as np
import sys
from pathlib import Path
import os
import soundfile as sf

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from backend.model_loader import get_model
from backend.config import logger

def test_icl_silence_padding():
    print("Testing ICL Silence Padding...")
    
    # Create a dummy 1-second wav
    test_wav = "icl_test.wav"
    sr = 24000
    dummy_audio = np.random.uniform(-0.1, 0.1, sr).astype(np.float32)
    sf.write(test_wav, dummy_audio, sr)
    
    try:
        model = get_model("Base")
        
        print("Calling create_voice_clone_prompt with ICL mode...")
        # x_vector_only_mode=False triggers ICL
        prompts = model.create_voice_clone_prompt(
            ref_audio=test_wav,
            ref_text="This is a test reference text.",
            x_vector_only_mode=False
        )
        
        print(f"Successfully created {len(prompts)} prompt(s).")
        
        # Verify ref_code length if possible, or just check logs
        # The log "Appended 0.5s silence buffer..." should appear
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if os.path.exists(test_wav):
            os.remove(test_wav)

if __name__ == "__main__":
    test_icl_silence_padding()
