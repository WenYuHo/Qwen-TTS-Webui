import numpy as np
import time
import sys
from pathlib import Path

# Ensure src is in path
ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = str(ROOT_DIR / "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from backend.utils import AudioPostProcessor

def benchmark_declick(duration_mins=5, sr=24000):
    print(f"--- Benchmarking apply_declick (Duration: {duration_mins} mins, SR: {sr} Hz) ---")

    # Generate random audio with some spikes
    num_samples = sr * 60 * duration_mins
    wav = np.random.uniform(-0.1, 0.1, num_samples).astype(np.float32)

    # Add 100 high-amplitude spikes (clicks)
    spike_indices = np.random.randint(0, num_samples, 100)
    for idx in spike_indices:
        wav[idx] = 0.9 * np.random.choice([-1, 1])

    # Baseline timing
    start_time = time.time()
    out = AudioPostProcessor.apply_declick(wav, sr)
    end_time = time.time()

    elapsed = end_time - start_time
    print(f"Execution time: {elapsed:.4f} seconds")

    # Sanity check: how many spikes were actually "caught"?
    # Original logic: spikes = np.abs(chunk) > (local_rms * 10)
    # This heuristic depends on the window and background noise.
    spikes_after = np.sum(np.abs(out) > 0.5)
    print(f"Spikes > 0.5 remaining: {spikes_after}")

    # Return metrics for comparison
    return elapsed, out

if __name__ == "__main__":
    benchmark_declick()
