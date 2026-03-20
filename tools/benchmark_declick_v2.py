import numpy as np
import time
import sys
import os

# Add src to path
sys.path.append(os.path.abspath("src"))
from backend.utils import AudioPostProcessor

def apply_declick_vectorized_test(wav, sr):
    if len(wav.shape) > 1:
        return np.stack([apply_declick_vectorized_test(wav[i], sr) for i in range(wav.shape[0])])

    out = wav.copy()
    window = int(sr * 0.002)
    if window < 2: return wav

    n_full_windows = len(wav) // window
    if n_full_windows > 0:
        full_len = n_full_windows * window
        chunks = wav[:full_len].reshape(n_full_windows, window)
        sq_sums = np.einsum('ij,ij->i', chunks, chunks)
        rms = np.sqrt(sq_sums / window) + 1e-6
        spikes = np.abs(chunks) > (rms[:, None] * 10)

        if np.any(spikes):
            out_chunks = out[:full_len].reshape(n_full_windows, window)
            row_idx, _ = np.where(spikes)
            out_chunks[spikes] = np.sign(chunks[spikes]) * rms[row_idx] * 3

    remainder_start = n_full_windows * window
    if len(wav) - remainder_start >= 2:
        chunk = wav[remainder_start:]
        local_rms = np.sqrt(np.vdot(chunk, chunk) / len(chunk)) + 1e-6
        spikes = np.abs(chunk) > (local_rms * 10)
        if np.any(spikes):
            out[remainder_start:][spikes] = np.sign(chunk[spikes]) * local_rms * 3

    return out

def benchmark(duration_sec=60, sr=24000):
    print(f"Benchmarking de-click on {duration_sec}s of {sr}Hz audio...")
    n_samples = duration_sec * sr
    wav = np.random.normal(0, 0.1, n_samples).astype(np.float32)
    spike_indices = np.random.choice(n_samples, 100, replace=False)
    wav[spike_indices] = np.random.choice([-1.0, 1.0], 100) * 0.9

    # Original
    start = time.perf_counter()
    _ = AudioPostProcessor.apply_declick(wav, sr)
    orig_time = time.perf_counter() - start
    print(f"Original logic: {orig_time*1000:.2f} ms")

    # Vectorized
    start = time.perf_counter()
    _ = apply_declick_vectorized_test(wav, sr)
    vect_time = time.perf_counter() - start
    print(f"Vectorized logic: {vect_time*1000:.2f} ms")

    speedup = orig_time / vect_time
    print(f"⚡ Speedup: {speedup:.2f}x")

if __name__ == "__main__":
    benchmark()
