import numpy as np
import time
import logging
import sys
import os

# Ensure src is in path
sys.path.insert(0, os.getcwd())

from src.backend.utils import AudioPostProcessor

logging.basicConfig(level=logging.INFO)

def benchmark_declick():
    sr = 24000
    # 5 minutes of audio (7.2M samples)
    wav = (np.random.randn(sr * 60 * 5) * 0.01).astype(np.float32)

    # Use 192kHz to ensure we can verify the LOGIC as well as speed.
    sr_high = 192000
    duration_sec = 60
    wav_high = (np.random.randn(sr_high * duration_sec) * 0.01).astype(np.float32)

    wav_high[1000] = 10.0
    wav_high[50000] = -10.0

    print(f"Benchmarking de-click on {duration_sec}s of 192kHz audio ({sr_high * duration_sec} samples)...")

    # Warm up
    _ = AudioPostProcessor.apply_declick(wav_high[:sr_high], sr_high)

    start_time = time.time()
    out = AudioPostProcessor.apply_declick(wav_high, sr_high)
    end_time = time.time()

    duration = end_time - start_time
    print(f"De-click (Mono) took: {duration:.4f} seconds")

    # Verify it actually did something
    assert np.abs(out[1000]) < 2.0, f"Spike at 1000 not clamped: {out[1000]}"
    assert np.abs(out[50000]) < 2.0, f"Spike at 50000 not clamped: {out[50000]}"

    # Test Stereo
    wav_stereo = np.stack([wav_high, wav_high])
    start_time = time.time()
    out_stereo = AudioPostProcessor.apply_declick(wav_stereo, sr_high)
    end_time = time.time()
    print(f"De-click (Stereo) took: {end_time - start_time:.4f} seconds")

    assert out_stereo.shape == (2, len(wav_high))
    assert np.abs(out_stereo[0, 1000]) < 2.0
    assert np.abs(out_stereo[1, 1000]) < 2.0

    # Test Remainder (odd length)
    wav_odd = wav_high[:sr_high + 7] # 1s + 7 samples
    out_odd = AudioPostProcessor.apply_declick(wav_odd, sr_high)
    assert len(out_odd) == len(wav_odd)

    print("Verification passed!")

if __name__ == "__main__":
    benchmark_declick()
