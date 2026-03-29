import numpy as np
import time
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from backend.utils import AudioPostProcessor

def benchmark_declick(duration_sec=60, sr=44100):
    print(f"Benchmarking apply_declick with {duration_sec}s audio at {sr}Hz...")

    # Generate some random noise with some spikes
    n_samples = duration_sec * sr
    wav = np.random.normal(0, 0.1, n_samples).astype(np.float32)

    # Add some spikes
    spike_indices = np.random.randint(0, n_samples, 100)
    wav[spike_indices] = 1.0

    start_time = time.time()
    _ = AudioPostProcessor.apply_declick(wav, sr)
    end_time = time.time()

    print(f"Time taken: {end_time - start_time:.4f} seconds")

if __name__ == "__main__":
    benchmark_declick()
