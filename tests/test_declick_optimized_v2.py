import pytest
import numpy as np
from backend.utils import AudioPostProcessor

def original_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """The original loop-based implementation for verification."""
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

def test_declick_mono():
    # ⚡ Bolt: Use high sample rate so window size > 100, allowing 10x RMS detection
    sr = 192000
    # Create 0.1 second of audio with some spikes
    wav = np.random.uniform(-0.01, 0.01, sr // 10).astype(np.float32)
    wav[100] = 0.9
    wav[5000] = -0.9

    optimized = AudioPostProcessor.apply_declick(wav, sr)
    original = original_apply_declick(wav, sr)

    assert np.allclose(optimized, original, atol=1e-7)
    assert abs(optimized[100]) < 0.9
    assert abs(optimized[5000]) < 0.9

def test_declick_stereo():
    sr = 192000
    # Create 0.1 second of stereo audio
    wav = np.random.uniform(-0.01, 0.01, (2, sr // 10)).astype(np.float32)
    wav[0, 100] = 0.9
    wav[1, 500] = -0.9

    optimized = AudioPostProcessor.apply_declick(wav, sr)

    # Verify both channels processed
    assert optimized.shape == (2, sr // 10)
    assert abs(optimized[0, 100]) < 0.9
    assert abs(optimized[1, 500]) < 0.9

    # Compare with original channel-by-channel
    orig_l = original_apply_declick(wav[0], sr)
    orig_r = original_apply_declick(wav[1], sr)

    assert np.allclose(optimized[0], orig_l, atol=1e-7)
    assert np.allclose(optimized[1], orig_r, atol=1e-7)

def test_declick_remainder():
    sr = 192000
    window = int(sr * 0.002)
    # Length that is not a multiple of window
    num_samples = window * 10 + (window // 2)
    wav = np.random.uniform(-0.01, 0.01, num_samples).astype(np.float32)

    # Spike in the remainder part
    wav[-5] = 0.9

    optimized = AudioPostProcessor.apply_declick(wav, sr)
    original = original_apply_declick(wav, sr)

    assert len(optimized) == num_samples
    assert np.allclose(optimized, original, atol=1e-7)
    assert abs(optimized[-5]) < 0.9

def test_declick_small_buffer():
    sr = 24000
    # Smaller than window
    num_samples = int(sr * 0.001)
    wav = np.random.uniform(-0.1, 0.1, num_samples).astype(np.float32)

    optimized = AudioPostProcessor.apply_declick(wav, sr)
    assert len(optimized) == num_samples
    # Should be a copy of original (no de-clicking for < 2ms)
    assert np.array_equal(optimized, wav)

def test_declick_no_spikes():
    sr = 24000
    wav = np.zeros(sr, dtype=np.float32)
    optimized = AudioPostProcessor.apply_declick(wav, sr)
    assert np.array_equal(optimized, wav)
