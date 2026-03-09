import numpy as np
import time
import sys
import os
import pytest

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from backend.utils import AudioPostProcessor

def original_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """Original implementation for comparison."""
    try:
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
    except Exception:
        return wav

def test_declick_matching():
    sr = 24000
    duration = 1
    wav = np.random.normal(0, 0.01, sr * duration).astype(np.float32)
    # Add some clicks
    for _ in range(10):
        pos = np.random.randint(0, len(wav))
        wav[pos] = 1.0

    out_orig = original_apply_declick(wav, sr)
    out_new = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_array_almost_equal(out_orig, out_new)

def test_declick_stereo():
    sr = 24000
    wav = np.random.normal(0, 0.01, (2, 1000)).astype(np.float32)
    wav[0, 100] = 1.0
    wav[1, 200] = 1.0

    out_orig = original_apply_declick(wav, sr)
    out_new = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_array_almost_equal(out_orig, out_new)

def test_declick_remainder():
    sr = 24000
    window = int(sr * 0.002)
    # 1.5 windows
    wav = np.random.normal(0, 0.01, int(window * 1.5)).astype(np.float32)
    wav[-5] = 1.0

    out_orig = original_apply_declick(wav, sr)
    out_new = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_array_almost_equal(out_orig, out_new)

if __name__ == "__main__":
    # If run directly, do a benchmark
    sr = 24000
    duration = 300 # 5 minutes
    wav = np.random.normal(0, 0.01, sr * duration).astype(np.float32)

    print(f"Benchmarking with {duration}s of audio...")

    start = time.time()
    out_orig = original_apply_declick(wav, sr)
    orig_time = time.time() - start
    print(f"Original implementation: {orig_time:.4f}s")

    # Warm up new implementation
    _ = AudioPostProcessor.apply_declick(wav[:sr], sr)

    start = time.time()
    out_new = AudioPostProcessor.apply_declick(wav, sr)
    new_time = time.time() - start
    print(f"New implementation:      {new_time:.4f}s")

    if orig_time > 0:
        print(f"Speedup: {orig_time / new_time:.2f}x")

    np.testing.assert_array_almost_equal(out_orig, out_new)
    print("Verification: Outputs match exactly!")
