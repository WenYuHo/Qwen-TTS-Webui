import numpy as np
import time
import sys
import os

# Add src to path for imports
sys.path.append(os.path.abspath("src"))
from backend.utils import AudioPostProcessor

def benchmark_compressor(duration_sec=60, sr=24000, stereo=False):
    print(f"Benchmarking compressor on {duration_sec}s of {sr}Hz {'stereo' if stereo else 'mono'} audio...")

    # Generate random audio
    n_samples = duration_sec * sr
    if stereo:
        wav = np.random.normal(0, 0.2, (2, n_samples)).astype(np.float32)
    else:
        wav = np.random.normal(0, 0.2, n_samples).astype(np.float32)

    # Measure implementation
    start_time = time.perf_counter()
    _ = AudioPostProcessor.apply_compressor(wav, sr)
    end_time = time.perf_counter()

    elapsed = end_time - start_time
    print(f"Execution time: {elapsed*1000:.2f} ms")
    return elapsed

if __name__ == "__main__":
    benchmark_compressor(stereo=False)
    benchmark_compressor(stereo=True)
