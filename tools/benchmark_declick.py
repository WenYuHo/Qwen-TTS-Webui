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

    # Generate some "audio" with random clicks
    wav = np.random.normal(0, 0.01, num_samples).astype(np.float32)
    # Add a huge spike that definitely exceeds 10x RMS
    wav[100] = 1.0

    print(f"Benchmarking apply_declick with {duration}s of audio at {sr}Hz ({num_samples} samples)")

    # Force single chunk with 1 spike
    test_wav = np.ones(48, dtype=np.float32) * 0.001
    test_wav[10] = 0.5
    print(f"Test wav RMS: {np.sqrt(np.mean(test_wav**2))}")
    test_out = AudioPostProcessor.apply_declick(test_wav, sr)
    print(f"Test out spike value: {test_out[10]}")

    start_time = time.time()
    processed = AudioPostProcessor.apply_declick(wav, sr)
    end_time = time.time()

    print(f"Time taken: {end_time - start_time:.4f} seconds")

    # Verify it actually did something
    diff = np.abs(wav - processed)
    print(f"Max difference: {np.max(diff)}")
    print(f"Number of samples changed: {np.sum(diff > 0)}")

if __name__ == "__main__":
    benchmark_declick()
