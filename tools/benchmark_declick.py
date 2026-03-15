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
    wav = np.random.randn(sr * duration).astype(np.float32) * 0.1

    # Add some spikes
    spikes_indices = np.random.randint(0, len(wav), 100)
    wav[spikes_indices] *= 50

    print(f"Benchmarking apply_declick with {duration}s of audio at {sr}Hz ({len(wav)} samples)")

    start = time.time()
    out = AudioPostProcessor.apply_declick(wav, sr)
    end = time.time()

    print(f"Execution time: {end - start:.4f} seconds")

    # Verify it actually did something
    spikes_after = np.abs(out) > (np.sqrt(np.mean(wav**2)) * 10)
    # This might be tricky because local RMS changes.
    # But let's just check if max amplitude decreased.
    print(f"Max amp before: {np.max(np.abs(wav)):.4f}")
    print(f"Max amp after: {np.max(np.abs(out)):.4f}")

if __name__ == "__main__":
    benchmark_declick()
