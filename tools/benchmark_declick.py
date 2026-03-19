import time
import numpy as np
import sys
import os

# Add src to path
sys.path.append(os.path.abspath("src"))

from backend.utils import AudioPostProcessor

def benchmark_declick():
    sr = 24000
    duration = 60  # 60 seconds
    num_samples = sr * duration
    wav = np.random.randn(num_samples).astype(np.float32) * 0.1

    # Add some spikes
    for _ in range(100):
        idx = np.random.randint(0, num_samples)
        wav[idx] *= 20

    print(f"Benchmarking de-click on {duration}s of {sr}Hz audio ({num_samples} samples)...")

    start_time = time.time()
    _ = AudioPostProcessor.apply_declick(wav, sr)
    end_time = time.time()

    elapsed = end_time - start_time
    print(f"De-click took {elapsed*1000:.2f} ms")

    # Also benchmark stereo
    wav_stereo = np.random.randn(2, num_samples).astype(np.float32) * 0.1
    for _ in range(100):
        idx = np.random.randint(0, num_samples)
        wav_stereo[0, idx] *= 20
        wav_stereo[1, idx] *= 20

    start_time = time.time()
    _ = AudioPostProcessor.apply_declick(wav_stereo, sr)
    end_time = time.time()

    elapsed_stereo = end_time - start_time
    print(f"Stereo De-click took {elapsed_stereo*1000:.2f} ms")

if __name__ == "__main__":
    benchmark_declick()
