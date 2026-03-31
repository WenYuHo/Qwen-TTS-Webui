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

@pytest.mark.parametrize("sr", [24000, 44100, 48000])
@pytest.mark.parametrize("duration", [0.1, 0.5, 1.0])
@pytest.mark.parametrize("channels", [1, 2])
def test_declick_parity(sr, duration, channels):
    # Generate random audio
    n_samples = int(duration * sr)
    if channels == 2:
        wav = np.random.normal(0, 0.1, (2, n_samples)).astype(np.float32)
    else:
        wav = np.random.normal(0, 0.1, n_samples).astype(np.float32)

    # Add some deterministic spikes
    if channels == 2:
        wav[0, n_samples // 10] = 1.0
        wav[1, n_samples // 5] = -1.0
    else:
        wav[n_samples // 10] = 1.0
        wav[n_samples // 2] = -1.0

    # Current implementation (before vectorization it's identical to original_apply_declick)
    # We run it now to verify the test itself and the baseline
    expected = original_apply_declick(wav, sr)
    actual = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_allclose(actual, expected, rtol=1e-5, atol=1e-5)

def test_declick_edge_cases():
    sr = 24000
    # Very short buffer
    wav = np.array([0.1, 0.2], dtype=np.float32)
    expected = original_apply_declick(wav, sr)
    actual = AudioPostProcessor.apply_declick(wav, sr)
    np.testing.assert_allclose(actual, expected)

    # All zeros
    wav = np.zeros(1000, dtype=np.float32)
    expected = original_apply_declick(wav, sr)
    actual = AudioPostProcessor.apply_declick(wav, sr)
    np.testing.assert_allclose(actual, expected)
