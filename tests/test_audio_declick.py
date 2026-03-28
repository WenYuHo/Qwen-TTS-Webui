import numpy as np
import time
import pytest
from src.backend.utils import AudioPostProcessor

def original_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """Original loop-based implementation for verification."""
    if len(wav.shape) > 1:
        out = np.zeros_like(wav)
        for i in range(wav.shape[0]):
            out[i] = original_apply_declick(wav[i], sr)
        return out

    out = wav.copy()
    window = int(sr * 0.002) # 2ms
    if window < 2: return wav

    # Process in chunks
    for i in range(0, len(wav), window):
        chunk = wav[i:i+window]
        if len(chunk) < 2: continue
        local_rms = np.sqrt(np.mean(chunk**2)) + 1e-6
        # Identify spikes
        spikes = np.abs(chunk) > (local_rms * 10)
        if np.any(spikes):
            # Clamp spikes to local RMS * 3
            sign = np.sign(chunk[spikes])
            out[i:i+window][spikes] = sign * local_rms * 3
    return out

def test_declick_correctness():
    sr = 24000
    # 1 second of audio
    wav = np.random.randn(sr).astype(np.float32) * 0.1
    # Add some clicks
    wav[100] = 1.0
    wav[5000] = -1.0

    # After we implement the optimization, AudioPostProcessor.apply_declick will be the new one
    out_old = original_apply_declick(wav, sr)
    out_new = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_allclose(out_old, out_new, atol=1e-6)

def test_declick_stereo_correctness():
    sr = 24000
    wav = np.random.randn(2, sr).astype(np.float32) * 0.1
    wav[0, 100] = 1.0
    wav[1, 200] = -1.0

    out_old = original_apply_declick(wav, sr)
    out_new = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_allclose(out_old, out_new, atol=1e-6)

@pytest.mark.benchmark
def test_declick_performance():
    sr = 24000
    # 1 minute of audio for benchmark (5 mins might be too slow for the original)
    duration = 60
    wav = np.random.randn(sr * duration).astype(np.float32) * 0.1

    print(f"\nBenchmarking de-click on {duration}s of audio...")

    start_old = time.time()
    _ = original_apply_declick(wav, sr)
    end_old = time.time()
    dur_old = end_old - start_old
    print(f"Original implementation: {dur_old:.4f}s")

    start_new = time.time()
    _ = AudioPostProcessor.apply_declick(wav, sr)
    end_new = time.time()
    dur_new = end_new - start_new
    print(f"Vectorized implementation: {dur_new:.4f}s")

    if dur_new > 0:
        print(f"Speedup: {dur_old / dur_new:.2f}x")

    # We expect at least 10x speedup
    assert dur_new < dur_old
