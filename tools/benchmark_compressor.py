import numpy as np
import time
import sys
import os

# Add src to path for imports
sys.path.append(os.path.abspath("src"))
from backend.utils import AudioPostProcessor

def benchmark_compressor(duration_sec=60, sr=24000):
    print(f"Benchmarking compressor on {duration_sec}s of {sr}Hz audio...")

    # Mono
    wav_mono = np.random.normal(0, 0.5, duration_sec * sr).astype(np.float32)

    start_time = time.perf_counter()
    _ = AudioPostProcessor.apply_compressor(wav_mono, sr)
    elapsed_mono = time.perf_counter() - start_time
    print(f"Mono execution time: {elapsed_mono*1000:.2f} ms")

    # Stereo
    wav_stereo = np.random.normal(0, 0.5, (2, duration_sec * sr)).astype(np.float32)

    start_time = time.perf_counter()
    _ = AudioPostProcessor.apply_compressor(wav_stereo, sr)
    elapsed_stereo = time.perf_counter() - start_time
    print(f"Stereo execution time: {elapsed_stereo*1000:.2f} ms")

    return elapsed_mono, elapsed_stereo

if __name__ == "__main__":
    benchmark_compressor()
