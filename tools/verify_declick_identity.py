import numpy as np
import time
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))

from backend.utils import AudioPostProcessor

def original_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """The original loop-based implementation for verification."""
    if len(wav.shape) > 1:
        out = np.zeros_like(wav)
        for i in range(wav.shape[0]):
            out[i] = original_apply_declick(wav[i], sr)
        return out

    out = wav.copy()
    window = int(sr * 0.002) # 2ms
    if window < 2: return wav

    # Process in chunks
    for i in range(0, len(wav), window):
        chunk = wav[i:i+window]
        if len(chunk) < 2: continue
        local_rms = np.sqrt(np.mean(chunk**2)) + 1e-6
        # Identify spikes
        spikes = np.abs(chunk) > (local_rms * 10)
        if np.any(spikes):
            # Clamp spikes to local RMS * 3
            sign = np.sign(chunk[spikes])
            out[i:i+window][spikes] = sign * local_rms * 3
    return out

def verify():
    sr = 24000
    duration_sec = 1
    # Create wav with some guaranteed spikes
    wav = np.random.uniform(-0.1, 0.1, sr * duration_sec).astype(np.float32)
    for _ in range(10):
        idx = np.random.randint(0, len(wav))
        wav[idx] = 1.0

    print(f"Verifying optimized apply_declick against original...")

    expected = original_apply_declick(wav, sr)
    actual = AudioPostProcessor.apply_declick(wav, sr)

    if np.allclose(expected, actual):
        print("✅ SUCCESS: Outputs match exactly.")
    else:
        diff = np.abs(expected - actual)
        print(f"❌ FAILURE: Outputs differ. Max diff: {np.max(diff)}")
        # Print some values where they differ
        diff_indices = np.where(diff > 1e-7)[0]
        if len(diff_indices) > 0:
            idx = diff_indices[0]
            print(f"At index {idx}: Expected {expected[idx]}, Got {actual[idx]}")

if __name__ == "__main__":
    verify()
