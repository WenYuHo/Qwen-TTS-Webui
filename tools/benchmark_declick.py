import numpy as np
import time
import sys
import os

# Add src to path
sys.path.append(os.path.abspath("src"))

from backend.utils import AudioPostProcessor

def benchmark():
    sr = 24000
    # Use a larger buffer to get more accurate results
    duration = 300 # 5 minutes
    num_samples = sr * duration
    wav = np.random.normal(0, 0.1, num_samples).astype(np.float32)

    # Add some random spikes
    num_spikes = 1000
    spike_indices = np.random.randint(0, num_samples, num_spikes)
    wav[spike_indices] = 1.0

    print(f"Benchmarking apply_declick with {duration}s of audio at {sr}Hz ({num_samples} samples)...")

    # Warm up
    _ = AudioPostProcessor.apply_declick(wav[:sr], sr)

    start = time.time()
    out = AudioPostProcessor.apply_declick(wav, sr)
    end = time.time()

    duration_ms = (end - start) * 1000
    print(f"Execution time: {duration_ms:.2f} ms")

    # Basic verification that it did something
    spikes_remaining = np.sum(np.abs(out) > 0.9)
    print(f"Spikes remaining: {spikes_remaining} (Original: {num_spikes})")

    return duration_ms

if __name__ == "__main__":
    benchmark()
