import numpy as np
import time
import sys
import os

# Add src to path
sys.path.append(os.path.abspath("src"))

from backend.utils import AudioPostProcessor

def benchmark_declick(duration_sec=60, sr=24000):
    print(f"Benchmarking de-click for {duration_sec}s of {sr}Hz audio...")

    # Generate random audio with some spikes
    wav = np.random.uniform(-0.1, 0.1, duration_sec * sr).astype(np.float32)
    # Add 100 random spikes
    spike_indices = np.random.randint(0, len(wav), 100)
    wav[spike_indices] *= 20

    start_time = time.time()
    _ = AudioPostProcessor.apply_declick(wav, sr)
    end_time = time.time()

    duration_ms = (end_time - start_time) * 1000
    print(f"Execution time: {duration_ms:.2f} ms")
    return duration_ms

if __name__ == "__main__":
    benchmark_declick()
