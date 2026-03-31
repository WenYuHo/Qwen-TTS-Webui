import numpy as np
import time
import sys
import os

# Add src to path
sys.path.append(os.path.abspath("src"))

from backend.utils import AudioPostProcessor

def benchmark_declick():
    sr = 24000
    duration = 60 # 60 seconds
    num_samples = sr * duration
    wav = np.random.uniform(-0.5, 0.5, num_samples).astype(np.float32)

    # Add some spikes
    for _ in range(100):
        idx = np.random.randint(0, num_samples)
        wav[idx] = 1.0 if np.random.random() > 0.5 else -1.0

    print(f"Benchmarking apply_declick with {duration}s of {sr}Hz audio ({num_samples} samples)...")

    start_time = time.time()
    out = AudioPostProcessor.apply_declick(wav, sr)
    end_time = time.time()

    duration_ms = (end_time - start_time) * 1000
    print(f"Vectorized apply_declick took: {duration_ms:.2f} ms")

if __name__ == "__main__":
    benchmark_declick()
