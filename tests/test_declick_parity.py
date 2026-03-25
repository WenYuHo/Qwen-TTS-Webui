import numpy as np
import pytest
import sys
import os

# Add src to path
sys.path.append(os.path.abspath("src"))
from backend.utils import AudioPostProcessor

def apply_declick_original(wav: np.ndarray, sr: int) -> np.ndarray:
    """Original loop-based implementation for parity check."""
    out = wav.copy()
    window = int(sr * 0.002) # 2ms
    if window < 2: return wav

    for i in range(0, len(wav), window):
        chunk = wav[i:i+window]
        if len(chunk) < 2: continue
        local_rms = np.sqrt(np.mean(chunk**2)) + 1e-6
        spikes = np.abs(chunk) > (local_rms * 10)
        if np.any(spikes):
            sign = np.sign(chunk[spikes])
            out[i:i+window][spikes] = sign * local_rms * 3
    return out

def test_declick_parity():
    sr = 24000
    # Test different lengths including remainders
    for length in [1000, 1024, 2000, 2400]:
        wav = np.random.normal(0, 0.1, length).astype(np.float32)
        # Add some spikes
        wav[np.random.choice(length, 10)] = 0.9

        expected = apply_declick_original(wav, sr)
        actual = AudioPostProcessor.apply_declick(wav, sr)

        np.testing.assert_allclose(actual, expected, rtol=1e-5, atol=1e-5)

def test_declick_stereo_parity():
    sr = 24000
    length = 2400
    wav = np.random.normal(0, 0.1, (2, length)).astype(np.float32)
    wav[0, 100] = 0.9
    wav[1, 200] = -0.9

    expected0 = apply_declick_original(wav[0], sr)
    expected1 = apply_declick_original(wav[1], sr)
    expected = np.stack([expected0, expected1])

    actual = AudioPostProcessor.apply_declick(wav, sr)
    np.testing.assert_allclose(actual, expected, rtol=1e-5, atol=1e-5)

def test_declick_small_buffer():
    sr = 24000
    wav = np.array([0.1, 0.9, 0.1], dtype=np.float32)
    # window for 24k is 48. Small buffer should return original.
    actual = AudioPostProcessor.apply_declick(wav, sr)
    np.testing.assert_array_equal(actual, wav)
