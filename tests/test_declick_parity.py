import pytest
import numpy as np
from backend.utils import AudioPostProcessor

def original_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """The original loop-based de-clicker for parity testing."""
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

@pytest.mark.parametrize("sr", [16000, 24000, 44100])
@pytest.mark.parametrize("duration", [0.1, 0.5, 1.0])
@pytest.mark.parametrize("channels", [1, 2])
def test_declick_parity(sr, duration, channels):
    """Ensure optimized de-clicker is mathematically identical to the original."""
    n_samples = int(sr * duration)
    if channels == 1:
        wav = np.random.normal(0, 0.1, n_samples).astype(np.float32)
    else:
        wav = np.random.normal(0, 0.1, (channels, n_samples)).astype(np.float32)

    # Add some predictable spikes
    if channels == 1:
        wav[n_samples // 10] = 1.0
        wav[n_samples // 5] = -1.0
    else:
        wav[0, n_samples // 10] = 1.0
        wav[1, n_samples // 5] = -1.0

    original_out = original_apply_declick(wav, sr)
    optimized_out = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_allclose(optimized_out, original_out, atol=1e-6)

def test_declick_small_buffer():
    """Test de-clicker with a buffer smaller than the window size."""
    sr = 24000
    wav = np.array([0.1, 0.5, -0.2], dtype=np.float32)

    original_out = original_apply_declick(wav, sr)
    optimized_out = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_allclose(optimized_out, original_out, atol=1e-6)

def test_declick_remainder():
    """Test de-clicker with a buffer that leaves a remainder after windowing."""
    sr = 24000
    window = int(sr * 0.002)
    n_samples = window + (window // 2)
    wav = np.random.normal(0, 0.1, n_samples).astype(np.float32)

    original_out = original_apply_declick(wav, sr)
    optimized_out = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_allclose(optimized_out, original_out, atol=1e-6)
