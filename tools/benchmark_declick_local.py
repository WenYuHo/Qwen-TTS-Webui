import numpy as np
import time
from src.backend.utils import AudioPostProcessor

def benchmark_declick():
    sr = 24000
    # 5 minutes of audio
    wav = np.random.uniform(-0.1, 0.1, sr * 60 * 5).astype(np.float32)

    # Add some spikes
    for _ in range(100):
        idx = np.random.randint(0, len(wav))
        wav[idx] = 0.9

    start_time = time.time()
    out = AudioPostProcessor.apply_declick(wav, sr)
    end_time = time.time()

    print(f"Original apply_declick took: {end_time - start_time:.4f} seconds")

    # Verify it actually did something
    spikes_remaining = np.sum(np.abs(out) > 0.5)
    print(f"Spikes remaining: {spikes_remaining}")

if __name__ == "__main__":
    benchmark_declick()
