import numpy as np
import pytest
from backend.utils import AudioPostProcessor

def apply_declick_reference(wav: np.ndarray, sr: int) -> np.ndarray:
    """Original loop-based implementation for parity testing."""
    if len(wav.shape) > 1:
        out = np.zeros_like(wav)
        for i in range(wav.shape[0]):
            out[i] = apply_declick_reference(wav[i], sr)
        return out

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

@pytest.mark.parametrize("sr", [24000, 44100, 48000])
@pytest.mark.parametrize("duration", [0.1, 0.5, 1.0])
@pytest.mark.parametrize("channels", [1, 2])
def test_declick_parity(sr, duration, channels):
    n_samples = int(sr * duration)
    if channels == 1:
        wav = np.random.normal(0, 0.1, n_samples).astype(np.float32)
        # Add some spikes
        wav[n_samples // 10] = 0.9
        wav[n_samples // 5] = -0.8
    else:
        wav = np.random.normal(0, 0.1, (channels, n_samples)).astype(np.float32)
        wav[0, n_samples // 10] = 0.9
        wav[1, n_samples // 5] = -0.8

    ref = apply_declick_reference(wav, sr)
    # This will test the current implementation first, which should pass identity
    opt = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_allclose(ref, opt, atol=1e-7)

def test_declick_small_buffer():
    sr = 24000
    wav = np.array([0.1, 0.9, 0.1], dtype=np.float32)
    # window = 48
    ref = apply_declick_reference(wav, sr)
    opt = AudioPostProcessor.apply_declick(wav, sr)
    np.testing.assert_allclose(ref, opt, atol=1e-7)

def test_declick_remainder():
    sr = 24000
    window = int(sr * 0.002) # 48
    # 48 * 2 + 10 = 106 samples
    n_samples = window * 2 + 10
    wav = np.random.normal(0, 0.1, n_samples).astype(np.float32)
    wav[window * 2 + 5] = 0.9 # spike in remainder

    ref = apply_declick_reference(wav, sr)
    opt = AudioPostProcessor.apply_declick(wav, sr)
    np.testing.assert_allclose(ref, opt, atol=1e-7)
