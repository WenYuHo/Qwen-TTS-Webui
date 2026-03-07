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

def test_audio_validation():
    print("Testing Reference Audio Validation...")
    sr = 24000
    model = get_model("Base")
    
    # 1. Test Too Short (1s)
    print("\n--- Testing 1s audio (Too Short) ---")
    wav_short = "short.wav"
    sf.write(wav_short, np.random.uniform(-0.1, 0.1, sr), sr)
    try:
        model.create_voice_clone_prompt(ref_audio=wav_short, x_vector_only_mode=True)
        print("FAIL: Should have raised ValueError for short audio")
    except ValueError as e:
        print(f"SUCCESS: Caught expected error: {e}")
    finally: os.remove(wav_short)

    # 2. Test Too Long (35s)
    print("\n--- Testing 35s audio (Too Long) ---")
    wav_long = "long.wav"
    sf.write(wav_long, np.random.uniform(-0.1, 0.1, sr * 35), sr)
    try:
        model.create_voice_clone_prompt(ref_audio=wav_long, x_vector_only_mode=True)
        print("FAIL: Should have raised ValueError for long audio")
    except ValueError as e:
        print(f"SUCCESS: Caught expected error: {e}")
    finally: os.remove(wav_long)

    # 3. Test Silent (5s)
    print("\n--- Testing 5s silent audio ---")
    wav_silent = "silent.wav"
    sf.write(wav_silent, np.zeros(sr * 5), sr)
    try:
        model.create_voice_clone_prompt(ref_audio=wav_silent, x_vector_only_mode=True)
        print("FAIL: Should have raised ValueError for silent audio")
    except ValueError as e:
        print(f"SUCCESS: Caught expected error: {e}")
    finally: os.remove(wav_silent)

    # 4. Test Valid (5s)
    print("\n--- Testing 5s valid audio ---")
    wav_valid = "valid.wav"
    sf.write(wav_valid, np.random.uniform(-0.1, 0.1, sr * 5), sr)
    try:
        model.create_voice_clone_prompt(ref_audio=wav_valid, x_vector_only_mode=True)
        print("SUCCESS: Valid audio accepted")
    except Exception as e:
        print(f"FAIL: Should have accepted valid audio, got: {e}")
    finally: os.remove(wav_valid)

if __name__ == "__main__":
    test_audio_validation()
