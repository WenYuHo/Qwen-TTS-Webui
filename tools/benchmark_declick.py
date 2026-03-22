import numpy as np
import time
import sys
import os

# Add src to PYTHONPATH
sys.path.append(os.path.abspath("src"))

from backend.utils import AudioPostProcessor

def benchmark_declick():
    sr = 24000
    duration = 60 # 60 seconds
    wav = np.random.uniform(-1, 1, sr * duration).astype(np.float32)

    # Add some spikes
    wav[::sr] = 1.0
    wav[1::sr] = -1.0

    print(f"Benchmarking apply_declick with {duration}s of audio at {sr}Hz...")

    start_time = time.time()
    out = AudioPostProcessor.apply_declick(wav, sr)
    end_time = time.time()

    print(f"Original execution time: {end_time - start_time:.4f} seconds")

if __name__ == "__main__":
    benchmark_declick()
