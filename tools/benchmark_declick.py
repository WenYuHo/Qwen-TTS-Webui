import numpy as np
import time
import sys
import os

# Add src to path
sys.path.append(os.path.abspath("src"))

from backend.utils import AudioPostProcessor

def original_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """Original loop-based implementation."""
    if len(wav.shape) > 1:
        out = np.zeros_like(wav)
        for i in range(wav.shape[0]):
            out[i] = original_declick(wav[i], sr)
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

def benchmark():
    sr = 24000
    duration = 300  # 5 minutes
    wav = np.random.normal(0, 0.01, sr * duration).astype(np.float32)

    # Add explicit high-amplitude spikes (clicks)
    num_spikes = 1000
    spikes_idx = np.random.randint(0, len(wav), num_spikes)
    wav[spikes_idx] = 0.9  # Fixed high amplitude

    print(f"Benchmarking on {duration}s of audio ({len(wav)} samples)...")

    start = time.perf_counter()
    _ = original_declick(wav, sr)
    end = time.perf_counter()
    orig_time = end - start
    print(f"Original took: {orig_time:.4f}s")

    start = time.perf_counter()
    _ = AudioPostProcessor.apply_declick(wav, sr)
    end = time.perf_counter()
    vect_time = end - start
    print(f"Vectorized took: {vect_time:.4f}s")

    print(f"Speedup: {orig_time / vect_time:.2f}x")

if __name__ == "__main__":
    benchmark()
