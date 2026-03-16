
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
    t = np.linspace(0, duration, sr * duration)
    # Generate some white noise
    wav = np.random.normal(0, 0.1, len(t)).astype(np.float32)
    # Add some clicks
    num_clicks = 100
    click_indices = np.random.randint(0, len(wav), num_clicks)
    wav[click_indices] = 1.0

    start_time = time.time()
    _ = AudioPostProcessor.apply_declick(wav, sr)
    end_time = time.time()

    print(f"De-click for {duration}s of audio took: {(end_time - start_time) * 1000:.2f} ms")

if __name__ == "__main__":
    benchmark_declick()
