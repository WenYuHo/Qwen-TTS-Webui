import numpy as np
import time
import sys
import os

# Add src to path
sys.path.append(os.path.abspath("src"))

from backend.utils import AudioPostProcessor

def benchmark_declick():
    sr = 24000
    duration = 300  # 5 minutes
    num_samples = sr * duration
    wav = np.random.randn(num_samples).astype(np.float32) * 0.1

    # Add some spikes
    num_spikes = 100
    spike_indices = np.random.randint(0, num_samples, num_spikes)
    wav[spike_indices] *= 50

    print(f"Benchmarking apply_declick with {duration}s of audio ({num_samples} samples) at {sr}Hz")

    start_time = time.time()
    out = AudioPostProcessor.apply_declick(wav, sr)
    end_time = time.time()

    elapsed = end_time - start_time
    print(f"Original apply_declick took: {elapsed:.4f} seconds")

    # Verify it actually did something
    spikes_after = np.sum(np.abs(out[spike_indices]) > 1.0)
    print(f"Spikes remaining: {spikes_after} out of {num_spikes}")

if __name__ == "__main__":
    benchmark_declick()
