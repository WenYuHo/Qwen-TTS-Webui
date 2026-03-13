import numpy as np
import time
import logging
from src.backend.utils import AudioPostProcessor

logging.basicConfig(level=logging.INFO)

def benchmark_declick():
    sr = 24000
    # 5 minutes of audio
    wav = np.random.randn(sr * 60 * 5).astype(np.float32)
    # Add some spikes
    wav[1000] = 100.0
    wav[50000] = -80.0

    start_time = time.time()
    out = AudioPostProcessor.apply_declick(wav, sr)
    end_time = time.time()

    print(f"Original de-click took: {end_time - start_time:.4f} seconds for 5 minutes of audio")

    # Verify it actually did something
    assert np.abs(out[1000]) < 10.0
    assert np.abs(out[50000]) < 10.0

if __name__ == "__main__":
    benchmark_declick()
