import numpy as np
import time
import sys
import os

# Add src to path
sys.path.append(os.path.abspath("src"))

from backend.utils import AudioPostProcessor

def benchmark_declick():
    sr = 24000
    duration_sec = 60
    wav = np.random.uniform(-0.5, 0.5, sr * duration_sec).astype(np.float32)

    # Add some spikes
    spikes_idx = np.random.choice(len(wav), 1000, replace=False)
    wav[spikes_idx] *= 20

    print(f"Benchmarking apply_declick with {duration_sec}s of {sr}Hz audio ({len(wav)} samples)...")

    start = time.time()
    out = AudioPostProcessor.apply_declick(wav, sr)
    end = time.time()

    print(f"Time taken: {(end - start) * 1000:.2f} ms")
    return end - start

if __name__ == "__main__":
    benchmark_declick()
