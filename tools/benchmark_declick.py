import numpy as np
import time
import sys
import os

# Add src to path for imports
sys.path.append(os.path.abspath("src"))
from backend.utils import AudioPostProcessor

def benchmark_declick(duration_sec=60, sr=24000):
    print(f"Benchmarking de-click on {duration_sec}s of {sr}Hz audio...")

    # Generate random audio with some spikes
    n_samples = duration_sec * sr
    wav = np.random.normal(0, 0.1, n_samples).astype(np.float32)

    # Add 100 random spikes
    spike_indices = np.random.choice(n_samples, 100, replace=False)
    wav[spike_indices] = np.random.choice([-1.0, 1.0], 100) * 0.9

    # Measure original implementation
    start_time = time.perf_counter()
    _ = AudioPostProcessor.apply_declick(wav, sr)
    end_time = time.perf_counter()

    elapsed = end_time - start_time
    print(f"Execution time: {elapsed*1000:.2f} ms")
    return elapsed

if __name__ == "__main__":
    benchmark_declick()
