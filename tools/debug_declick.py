import numpy as np
import sys
import os

def apply_declick_vectorized(wav: np.ndarray, sr: int) -> np.ndarray:
    # Use the one from the actual codebase
    from backend.utils import AudioPostProcessor
    return AudioPostProcessor.apply_declick(wav, sr)

def test_manual():
    sr = 96000 # 2ms = 192 samples. sqrt(192) ~ 13.8 > 10.
    wav = np.zeros(96000, dtype=np.float32)
    wav[100] = 5.0

    out = apply_declick_vectorized(wav, sr)
    print(f"DEBUG: sr={sr}, wav[100]={wav[100]}, out[100]={out[100]}")
    if out[100] < 5.0:
        print("PASS")
    else:
        print("FAIL")

if __name__ == "__main__":
    sys.path.append(os.path.abspath("src"))
    test_manual()
