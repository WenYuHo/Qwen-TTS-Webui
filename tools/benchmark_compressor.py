import numpy as np
import time
import sys
import os

# Add src to path for imports
sys.path.append(os.path.abspath("src"))
from backend.utils import AudioPostProcessor

def benchmark_compressor(duration_sec=60, sr=24000, stereo=False, iterations=5):
    channels = 2 if stereo else 1
    mode = "stereo" if stereo else "mono"
    print(f"Benchmarking compressor on {duration_sec}s of {sr}Hz {mode} audio ({iterations} iterations)...")

    # Generate random audio
    if stereo:
        wav = np.random.normal(0, 0.2, (2, duration_sec * sr)).astype(np.float32)
    else:
        wav = np.random.normal(0, 0.2, duration_sec * sr).astype(np.float32)

    times = []
    for _ in range(iterations):
        start_time = time.perf_counter()
        _ = AudioPostProcessor.apply_compressor(wav, sr)
        end_time = time.perf_counter()
        times.append(end_time - start_time)

    avg_time = sum(times) / iterations
    print(f"Average execution time ({mode}): {avg_time*1000:.2f} ms")
    return avg_time

if __name__ == "__main__":
    benchmark_compressor(stereo=False)
    benchmark_compressor(stereo=True)
