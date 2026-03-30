import pytest
import numpy as np
from backend.utils import AudioPostProcessor

def original_apply_declick_logic(wav: np.ndarray, sr: int) -> np.ndarray:
    """The original loop-based logic for de-clicking, used as a parity reference."""
    try:
        if len(wav.shape) > 1:
            out = np.zeros_like(wav)
            for i in range(wav.shape[0]):
                out[i] = original_apply_declick_logic(wav[i], sr)
            return out

        out = wav.copy()
        window = int(sr * 0.002)  # 2ms
        if window < 2:
            return wav

        # Process in chunks
        for i in range(0, len(wav), window):
            chunk = wav[i:i+window]
            if len(chunk) < 2:
                continue
            local_rms = np.sqrt(np.mean(chunk**2)) + 1e-6
            # Identify spikes
            spikes = np.abs(chunk) > (local_rms * 10)
            if np.any(spikes):
                # Clamp spikes to local RMS * 3
                sign = np.sign(chunk[spikes])
                out[i:i+window][spikes] = sign * local_rms * 3
        return out
    except Exception:
        return wav

@pytest.mark.parametrize("sr", [16000, 24000, 44100])
@pytest.mark.parametrize("duration", [0.1, 0.5])
@pytest.mark.parametrize("channels", [1, 2])
def test_declick_parity(sr, duration, channels):
    """Verify that the current implementation matches the reference logic."""
    n_samples = int(sr * duration)
    if channels == 1:
        wav = np.random.normal(0, 0.1, n_samples).astype(np.float32)
    else:
        wav = np.random.normal(0, 0.1, (channels, n_samples)).astype(np.float32)

    # Add some deterministic spikes
    if channels == 1:
        wav[n_samples // 10] = 0.9
        wav[n_samples // 5] = -0.9
    else:
        wav[0, n_samples // 10] = 0.9
        wav[1, n_samples // 5] = -0.9

    expected = original_apply_declick_logic(wav, sr)
    actual = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_allclose(actual, expected, atol=1e-7)

def test_declick_small_buffer():
    """Test with a buffer smaller than the 2ms window."""
    sr = 24000
    wav = np.array([0.1, 0.5, 0.1], dtype=np.float32)
    # window for 24k is 48 samples. 3 samples is too small.

    expected = original_apply_declick_logic(wav, sr)
    actual = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_allclose(actual, expected)

def test_declick_exact_window_multiple():
    """Test with a buffer that is an exact multiple of the window size."""
    sr = 24000
    window = int(sr * 0.002)
    wav = np.random.normal(0, 0.1, window * 3).astype(np.float32)
    wav[window + 5] = 1.0 # Spike in second window

    expected = original_apply_declick_logic(wav, sr)
    actual = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_allclose(actual, expected)

def test_declick_with_remainder():
    """Test with a buffer that has a remainder smaller than the window size."""
    sr = 24000
    window = int(sr * 0.002)
    wav = np.random.normal(0, 0.1, window * 2 + 10).astype(np.float32)
    wav[-5] = 1.0 # Spike in the remainder

    expected = original_apply_declick_logic(wav, sr)
    actual = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_allclose(actual, expected)
