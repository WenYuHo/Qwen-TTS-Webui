import numpy as np
import time
import sys
import os

# Add src to path
sys.path.append(os.path.abspath("src"))

from backend.utils import AudioPostProcessor

def benchmark():
    sr = 24000
    duration = 60 # 60 seconds
    wav = np.random.uniform(-0.5, 0.5, sr * duration).astype(np.float32)

    # Add some clicks
    num_clicks = 100
    indices = np.random.randint(0, len(wav), num_clicks)
    wav[indices] = np.random.uniform(0.8, 1.0, num_clicks) * np.sign(np.random.uniform(-1, 1, num_clicks))

    print(f"Benchmarking apply_declick on {duration}s of {sr}Hz audio ({len(wav)} samples)...")

    start = time.perf_counter()
    out = AudioPostProcessor.apply_declick(wav, sr)
    end = time.perf_counter()

    print(f"Execution time: {(end - start) * 1000:.2f} ms")

if __name__ == "__main__":
    benchmark()
