import numpy as np
import time
import sys
from pathlib import Path

# Add src to path
ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = str(ROOT_DIR / "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from backend.utils import AudioPostProcessor

def benchmark_declick(duration_sec=60, sr=24000):
    print(f"Benchmarking de-click for {duration_sec}s of audio at {sr}Hz...")
    # Generate random audio with some spikes
    wav = np.random.uniform(-0.1, 0.1, duration_sec * sr).astype(np.float32)
    # Add some spikes
    num_spikes = 1000
    spike_indices = np.random.randint(0, len(wav), num_spikes)
    wav[spike_indices] = np.random.choice([-1.0, 1.0], num_spikes)

    start_time = time.time()
    out = AudioPostProcessor.apply_declick(wav, sr)
    end_time = time.time()

    duration = end_time - start_time
    print(f"De-click took: {duration:.4f} seconds")

    # Check if spikes were handled (heuristic check)
    original_max = np.max(np.abs(wav))
    processed_max = np.max(np.abs(out))
    print(f"Original max: {original_max:.4f}, Processed max: {processed_max:.4f}")

    return duration

if __name__ == "__main__":
    benchmark_declick()
