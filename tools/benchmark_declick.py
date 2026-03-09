import numpy as np
import time
from src.backend.utils import AudioPostProcessor

def benchmark_declick():
    sr = 96000 # High SR to ensure detection
    # 5 minutes of audio
    duration = 5 * 60
    # Use lower amplitude so 1.0 spikes are definitely > 10x RMS
    wav = np.random.uniform(-0.01, 0.01, sr * duration).astype(np.float32)

    # Add some spikes
    spikes_idx = np.random.choice(len(wav), 1000, replace=False)
    wav[spikes_idx] = np.random.choice([-1.0, 1.0], 1000) * 0.9

    print(f"Benchmarking apply_declick with {len(wav)} samples ({duration}s) at {sr}Hz...")

    # Warm up
    _ = AudioPostProcessor.apply_declick(wav[:sr], sr)

    start = time.time()
    out = AudioPostProcessor.apply_declick(wav, sr)
    end = time.time()

    duration_taken = end - start
    print(f"Time taken: {duration_taken:.4f}s")

    # Verify it actually did something
    diff = np.abs(wav - out)
    modified = np.sum(diff > 0)
    print(f"Number of samples modified: {modified}")

    if modified > 0:
        # Check if it correctly reduced some spikes
        original_spikes = wav[spikes_idx]
        new_spikes = out[spikes_idx]
        reduction = np.mean(np.abs(original_spikes) - np.abs(new_spikes))
        print(f"Average reduction at spike locations: {reduction:.4f}")

if __name__ == "__main__":
    benchmark_declick()
