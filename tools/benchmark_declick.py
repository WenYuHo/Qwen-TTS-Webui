import numpy as np
import time
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from backend.utils import AudioPostProcessor

def benchmark_declick():
    sr = 24000
    # 5 minutes of audio
    duration = 300
    n_samples = sr * duration
    wav = np.random.normal(0, 0.1, n_samples).astype(np.float32)

    # Add some spikes
    spikes = np.random.choice(n_samples, 1000)
    wav[spikes] = 1.0

    start_time = time.time()
    _ = AudioPostProcessor.apply_declick(wav, sr)
    end_time = time.time()

    print(f"Time taken for {duration}s of audio: {end_time - start_time:.4f}s")

if __name__ == "__main__":
    benchmark_declick()
