import time
import numpy as np
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from backend.utils import AudioPostProcessor

def benchmark_declick():
    sr = 24000
    duration = 60 # 60 seconds
    num_samples = sr * duration

    # Generate some noisy audio with spikes
    wav = np.random.normal(0, 0.1, num_samples).astype(np.float32)
    # Add some spikes
    spikes_indices = np.random.choice(num_samples, 100, replace=False)
    wav[spikes_indices] *= 50

    print(f"Benchmarking apply_declick with {duration}s of audio at {sr}Hz ({num_samples} samples)...")

    start_time = time.time()
    # Warm up
    _ = AudioPostProcessor.apply_declick(wav[:sr], sr)

    start_time = time.time()
    processed = AudioPostProcessor.apply_declick(wav, sr)
    end_time = time.time()

    elapsed = end_time - start_time
    print(f"Elapsed time: {elapsed:.4f} seconds")

    # Check if spikes were reduced
    input_max = np.max(np.abs(wav))
    output_max = np.max(np.abs(processed))
    print(f"Input Max: {input_max:.4f}, Output Max: {output_max:.4f}")

if __name__ == "__main__":
    benchmark_declick()
