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

    # Create a noisy signal with some spikes
    wav = np.random.randn(num_samples).astype(np.float32) * 0.1
    # Add some spikes
    spikes_idx = np.random.choice(num_samples, 1000, replace=False)
    wav[spikes_idx] *= 50

    print(f"Benchmarking de-click on {duration}s of {sr}Hz audio ({num_samples} samples)...")

    start_time = time.time()
    out = AudioPostProcessor.apply_declick(wav, sr)
    end_time = time.time()

    duration_ms = (end_time - start_time) * 1000
    print(f"De-click took: {duration_ms:.2f} ms")

    # Parity check (make sure it actually did something)
    spikes_after = np.sum(np.abs(out) > (np.sqrt(np.mean(out**2)) * 10))
    print(f"Spikes before: {len(spikes_idx)}")
    print(f"Spikes after: {spikes_after}")

if __name__ == "__main__":
    benchmark_declick()
