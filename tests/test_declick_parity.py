import numpy as np
import pytest
from backend.utils import AudioPostProcessor

def original_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """Original loop-based implementation for parity testing."""
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

@pytest.mark.parametrize("sr", [16000, 24000, 44100, 48000])
@pytest.mark.parametrize("duration", [0.1, 0.5, 1.0])
@pytest.mark.parametrize("channels", [1, 2])
def test_declick_parity(sr, duration, channels):
    """Verify that the optimized apply_declick is mathematically identical to the original."""
    n_samples = int(sr * duration)
    if channels == 1:
        wav = np.random.normal(0, 0.1, n_samples).astype(np.float32)
    else:
        wav = np.random.normal(0, 0.1, (channels, n_samples)).astype(np.float32)

    # Add some deterministic spikes
    if channels == 1:
        wav[n_samples // 10] = 0.9
        wav[n_samples // 5] = -0.8
    else:
        wav[0, n_samples // 10] = 0.9
        wav[1, n_samples // 5] = -0.8

    expected = original_apply_declick(wav, sr)
    actual = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_allclose(actual, expected, rtol=1e-6, atol=1e-6)

def test_declick_small_buffer():
    """Test with a buffer smaller than the window size."""
    sr = 24000
    wav = np.array([0.1, 0.2, 0.9, 0.1], dtype=np.float32)

    expected = original_apply_declick(wav, sr)
    actual = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_allclose(actual, expected)

def test_declick_remainder():
    """Test with a buffer that is not a multiple of the window size."""
    sr = 24000
    window = int(sr * 0.002) # 48 samples
    wav = np.random.normal(0, 0.1, window * 2 + 10).astype(np.float32)
    wav[window + 5] = 0.9 # Spike in second window
    wav[window * 2 + 5] = 0.8 # Spike in remainder (should be ignored by original if < 2 samples)

    expected = original_apply_declick(wav, sr)
    actual = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_allclose(actual, expected)
