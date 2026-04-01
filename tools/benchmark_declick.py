import numpy as np
import time
from src.backend.utils import AudioPostProcessor

def benchmark_declick():
    sr = 24000
    duration = 60 # 60 seconds
    wav = np.random.randn(sr * duration).astype(np.float32) * 0.1

    # Add some spikes
    for _ in range(100):
        idx = np.random.randint(0, len(wav))
        wav[idx] = 1.0

    start = time.perf_counter()
    out = AudioPostProcessor.apply_declick(wav, sr)
    end = time.perf_counter()

    print(f"Original apply_declick took: {(end - start) * 1000:.2f} ms")

if __name__ == "__main__":
    benchmark_declick()
