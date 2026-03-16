import time
import numpy as np
import sys
import os

# Add src to path
sys.path.append(os.path.abspath("src"))

from backend.utils import AudioPostProcessor

def benchmark_declick():
    sr = 24000
    duration = 60 # 60 seconds
    wav = np.random.uniform(-1, 1, sr * duration).astype(np.float32)

    # Add some clicks
    clicks = np.random.randint(0, len(wav), 100)
    wav[clicks] *= 50

    print(f"Benchmarking apply_declick with {duration}s of audio at {sr}Hz...")

    start_time = time.time()
    out = AudioPostProcessor.apply_declick(wav, sr)
    end_time = time.time()

    elapsed = end_time - start_time
    print(f"Time taken: {elapsed:.4f}s")

    # Check if clicks were actually clamped
    peak = np.max(np.abs(out))
    print(f"Max peak after de-click: {peak:.4f}")

if __name__ == "__main__":
    benchmark_declick()
