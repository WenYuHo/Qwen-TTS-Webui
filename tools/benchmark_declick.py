import numpy as np
import time
import sys
import os

# Add src to path
sys.path.append(os.path.abspath("src"))

from backend.utils import AudioPostProcessor

def original_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """Original loop-based implementation."""
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
    except Exception as e:
        return wav

def optimized_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """Proposed vectorized implementation."""
    try:
        if len(wav.shape) > 1:
            return np.stack([optimized_apply_declick(ch, sr) for ch in wav])

        window = int(sr * 0.002)  # 2ms
        if window < 2 or len(wav) < 2:
            return wav.copy()

        n_chunks = len(wav) // window
        main_part_len = n_chunks * window
        main_part = wav[:main_part_len]
        remainder = wav[main_part_len:]

        if n_chunks > 0:
            chunks = main_part.reshape(n_chunks, window)
            sq_sum = np.einsum('ij,ij->i', chunks, chunks)
            rms = np.sqrt(sq_sum / window) + 1e-6
            spikes = np.abs(chunks) > (rms[:, np.newaxis] * 10)

            if np.any(spikes):
                out_chunks = chunks.copy()
                clamp_vals = rms[:, np.newaxis] * 3
                out_chunks[spikes] = np.sign(out_chunks[spikes]) * clamp_vals[spikes]
                main_part = out_chunks.ravel()

        if len(remainder) >= 2:
            rem_rms = np.sqrt(np.vdot(remainder, remainder) / len(remainder)) + 1e-6
            rem_spikes = np.abs(remainder) > (rem_rms * 10)
            if np.any(rem_spikes):
                remainder = remainder.copy()
                remainder[rem_spikes] = np.sign(remainder[rem_spikes]) * rem_rms * 3

        if n_chunks > 0:
            return np.concatenate([main_part, remainder])
        else:
            return remainder.copy()
    except Exception:
        return wav.copy()

def benchmark_declick():
    sr = 24000
    duration = 60 # 60 seconds
    # Force some background noise so RMS isn't 0
    wav = np.random.uniform(-0.1, 0.1, sr * duration).astype(np.float32)

    # Add many spikes to ensure branch hits
    num_spikes = 1000
    spike_indices = np.random.randint(0, len(wav), num_spikes)
    wav[spike_indices] = np.random.uniform(0.8, 1.0, num_spikes) * np.sign(np.random.uniform(-1, 1, num_spikes))

    print(f"Benchmarking de-click on {duration}s of {sr}Hz audio ({len(wav)} samples)...")

    start = time.time()
    _ = original_apply_declick(wav, sr)
    orig_time = (time.time() - start) * 1000
    print(f"Original Time: {orig_time:.2f} ms")

    start = time.time()
    _ = optimized_apply_declick(wav, sr)
    opt_time = (time.time() - start) * 1000
    print(f"Optimized Time: {opt_time:.2f} ms")

    speedup = orig_time / opt_time
    print(f"Speedup: {speedup:.2f}x")

if __name__ == "__main__":
    benchmark_declick()
