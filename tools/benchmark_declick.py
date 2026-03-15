import numpy as np
import time
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from backend.utils import AudioPostProcessor

def benchmark_declick():
    sr = 24000
    duration = 60 # 60 seconds
    wav = np.random.randn(sr * duration).astype(np.float32)
    # Add some "clicks"
    clicks = np.random.randint(0, len(wav), 100)
    wav[clicks] *= 50

    print(f"Benchmarking de-click on {duration}s of audio ({len(wav)} samples)...")

    start = time.time()
    out = AudioPostProcessor.apply_declick(wav, sr)
    end = time.time()

    print(f"Original de-click took: {end - start:.4f}s")
    return end - start

if __name__ == "__main__":
    benchmark_declick()
