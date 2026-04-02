import time
import numpy as np
import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'src'))
from backend.utils import AudioPostProcessor

def benchmark():
    sr = 24000
    duration = 60 # 60 seconds
    wav = np.random.randn(sr * duration).astype(np.float32) * 0.1
    # Add some spikes
    for _ in range(100):
        idx = np.random.randint(0, len(wav))
        wav[idx] = 1.0

    start = time.time()
    _ = AudioPostProcessor.apply_declick(wav, sr)
    end = time.time()
    print(f"De-click for {duration}s audio took: {end - start:.4f}s")

if __name__ == "__main__":
    benchmark()
