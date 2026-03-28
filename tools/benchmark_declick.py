
import numpy as np
import time
import sys
import os

# Add src to path
sys.path.append(os.path.abspath("src"))

from backend.utils import AudioPostProcessor

def original_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """Simple heuristic de-clicker: clamps spikes > 10x local RMS."""
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

def benchmark_declick(duration_sec=60, sr=24000):
    print(f"Benchmarking apply_declick with {duration_sec}s of audio at {sr}Hz...")

    # Create a dummy waveform with some spikes
    n_samples = duration_sec * sr
    wav = np.random.uniform(-0.1, 0.1, n_samples).astype(np.float32)

    # Add some spikes
    spike_indices = np.random.choice(n_samples, 100, replace=False)
    wav[spike_indices] = np.random.uniform(0.5, 1.0, 100) * np.random.choice([-1, 1], 100)

    # Original
    start_time = time.time()
    iterations = 5
    for _ in range(iterations):
        _ = original_apply_declick(wav, sr)
    end_time = time.time()
    avg_orig = (end_time - start_time) / iterations
    print(f"Original avg time for {duration_sec}s: {avg_orig:.4f}s")

    # Vectorized
    start_time = time.time()
    for _ in range(iterations):
        _ = AudioPostProcessor.apply_declick(wav, sr)
    end_time = time.time()
    avg_vec = (end_time - start_time) / iterations
    print(f"Vectorized avg time for {duration_sec}s: {avg_vec:.4f}s")

    print(f"Speedup: {avg_orig / avg_vec:.2f}x")
    return avg_orig, avg_vec

if __name__ == "__main__":
    benchmark_declick()
