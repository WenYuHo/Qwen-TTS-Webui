import numpy as np
import time
from backend.utils import AudioPostProcessor

def benchmark_declick():
    sr = 24000
    duration = 60 # 60 seconds
    wav = np.random.randn(sr * duration).astype(np.float32)
    # Add some spikes
    spikes_idx = np.random.randint(0, len(wav), 100)
    wav[spikes_idx] *= 50

    start_time = time.perf_counter()
    out = AudioPostProcessor.apply_declick(wav, sr)
    end_time = time.perf_counter()

    print(f"De-click took: {(end_time - start_time) * 1000:.2f} ms")

if __name__ == "__main__":
    benchmark_declick()
