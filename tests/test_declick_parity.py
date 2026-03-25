import numpy as np
import pytest
import sys
import os

# Add src to path for imports
sys.path.append(os.path.abspath("src"))
from backend.utils import AudioPostProcessor

def original_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """Original loop-based de-clicker for parity testing."""
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

@pytest.mark.parametrize("sr", [24000, 44100, 48000])
@pytest.mark.parametrize("duration", [0.1, 0.5, 1.0])
@pytest.mark.parametrize("channels", [1, 2])
def test_declick_parity(sr, duration, channels):
    """Verify that current apply_declick matches original loop-based logic."""
    n_samples = int(sr * duration)
    if channels == 1:
        wav = np.random.normal(0, 0.1, n_samples).astype(np.float32)
        # Add some spikes
        wav[n_samples // 10] = 0.9
        wav[n_samples // 2] = -0.8
    else:
        wav = np.random.normal(0, 0.1, (channels, n_samples)).astype(np.float32)
        # Add some spikes
        wav[0, n_samples // 10] = 0.9
        wav[1, n_samples // 2] = -0.8

    # The current implementation in src/backend/utils/__init__.py is loop-based.
    # We test it against our local copy of the same logic.
    expected = original_apply_declick(wav, sr)
    actual = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_allclose(actual, expected, rtol=1e-5, atol=1e-5)

def test_declick_remainder_handling():
    """Verify handling of buffers not perfectly divisible by window size."""
    sr = 24000
    window = int(sr * 0.002) # 48 samples
    n_samples = window * 10 + (window // 2) # remainder chunk

    wav = np.random.normal(0, 0.1, n_samples).astype(np.float32)
    # Add spike in the remainder part
    wav[-5] = 1.0

    expected = original_apply_declick(wav, sr)
    actual = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_allclose(actual, expected, rtol=1e-5, atol=1e-5)

def test_declick_very_short_buffer():
    """Verify handling of buffers shorter than window size (parity check)."""
    sr = 24000
    window = int(sr * 0.002) # 48 samples
    n_samples = 20 # less than window

    wav = np.random.normal(0, 0.1, n_samples).astype(np.float32)
    # Add spike
    wav[10] = 0.9

    expected = original_apply_declick(wav, sr)
    actual = AudioPostProcessor.apply_declick(wav, sr)

    # Original code would treat the entire short buffer as one chunk
    np.testing.assert_allclose(actual, expected, rtol=1e-5, atol=1e-5)

def test_declick_empty_buffer():
    """Verify handling of empty buffers."""
    sr = 24000
    wav = np.array([], dtype=np.float32)

    actual = AudioPostProcessor.apply_declick(wav, sr)
    assert len(actual) == 0
    assert actual is not wav # Must be a copy
