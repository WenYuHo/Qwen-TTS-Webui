import numpy as np
import pytest
from src.backend.utils import AudioPostProcessor

def original_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """Original loop-based implementation for parity checking."""
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
def test_declick_parity(sr, duration):
    wav = np.random.randn(int(sr * duration)).astype(np.float32) * 0.1
    # Add some spikes
    for _ in range(10):
        idx = np.random.randint(0, len(wav))
        wav[idx] = 1.0

    expected = original_apply_declick(wav, sr)
    actual = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_allclose(actual, expected, atol=1e-7)

def test_declick_stereo_parity():
    sr = 24000
    wav = np.random.randn(2, sr).astype(np.float32) * 0.1
    wav[0, 100] = 1.0
    wav[1, 200] = 1.0

    expected = original_apply_declick(wav, sr)
    actual = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_allclose(actual, expected, atol=1e-7)

def test_declick_short_buffer():
    sr = 24000
    wav = np.random.randn(10).astype(np.float32) * 0.1

    expected = original_apply_declick(wav, sr)
    actual = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_allclose(actual, expected, atol=1e-7)
