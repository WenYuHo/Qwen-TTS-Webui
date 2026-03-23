import numpy as np
import time
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.append(os.path.abspath("src"))
from backend.utils import AudioPostProcessor

def apply_declick_original(wav: np.ndarray, sr: int) -> np.ndarray:
    """Original loop-based de-clicker for parity testing."""
    try:
        if len(wav.shape) > 1:
            out = np.zeros_like(wav)
            for i in range(wav.shape[0]):
                out[i] = apply_declick_original(wav[i], sr)
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
    except Exception:
        return wav

def test_parity(duration_sec=5, sr=24000):
    print(f"Testing parity on {duration_sec}s of {sr}Hz audio...")
    n_samples = duration_sec * sr
    wav = np.random.normal(0, 0.1, n_samples).astype(np.float32)

    # Add random spikes
    spike_indices = np.random.choice(n_samples, 50, replace=False)
    wav[spike_indices] = np.random.choice([-1.0, 1.0], 50) * 0.9

    # Original
    start_orig = time.perf_counter()
    out_orig = apply_declick_original(wav, sr)
    end_orig = time.perf_counter()

    # New (currently same as original in src)
    start_new = time.perf_counter()
    out_new = AudioPostProcessor.apply_declick(wav, sr)
    end_new = time.perf_counter()

    diff = np.abs(out_orig - out_new).max()
    print(f"Max difference: {diff}")
    print(f"Original time: {(end_orig - start_orig)*1000:.2f} ms")
    print(f"New time: {(end_new - start_new)*1000:.2f} ms")

    if diff > 1e-6:
        print("❌ Parity FAILED")
        return False
    else:
        print("✅ Parity PASSED")
        return True

def test_multi_channel_parity(duration_sec=2, sr=24000):
    print(f"Testing multi-channel parity...")
    n_samples = duration_sec * sr
    wav = np.random.normal(0, 0.1, (2, n_samples)).astype(np.float32)

    # Add spikes
    wav[0, 1000] = 0.9
    wav[1, 2000] = -0.9

    out_orig = apply_declick_original(wav, sr)
    out_new = AudioPostProcessor.apply_declick(wav, sr)

    diff = np.abs(out_orig - out_new).max()
    print(f"Multi-channel max difference: {diff}")
    if diff > 1e-6:
        print("❌ Multi-channel parity FAILED")
        return False
    else:
        print("✅ Multi-channel parity PASSED")
        return True

if __name__ == "__main__":
    p1 = test_parity()
    p2 = test_multi_channel_parity()

    if p1 and p2:
        print("\nAll parity tests initial check complete (comparing current against itself).")
    else:
        sys.exit(1)
