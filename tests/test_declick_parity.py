import numpy as np
import pytest
from backend.utils import AudioPostProcessor

def apply_declick_original(wav: np.ndarray, sr: int) -> np.ndarray:
    """Original loop-based de-clicker for parity testing."""
    if len(wav.shape) > 1:
        out = np.zeros_like(wav)
        for i in range(wav.shape[0]):
            out[i] = apply_declick_original(wav[i], sr)
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
def test_declick_parity_mono(sr, duration):
    n_samples = int(sr * duration)
    wav = np.random.normal(0, 0.1, n_samples).astype(np.float32)

    # Add some spikes
    spike_indices = np.random.choice(n_samples, min(10, n_samples), replace=False)
    wav[spike_indices] *= 20.0

    original = apply_declick_original(wav, sr)
    optimized = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_allclose(original, optimized, atol=1e-6)

def test_declick_parity_stereo():
    sr = 24000
    n_samples = int(sr * 0.5)
    wav = np.random.normal(0, 0.1, (2, n_samples)).astype(np.float32)

    # Add spikes to both channels
    wav[0, 100] = 0.9
    wav[1, 500] = -0.8

    original = apply_declick_original(wav, sr)
    optimized = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_allclose(original, optimized, atol=1e-6)

def test_declick_short_buffer():
    sr = 24000
    # Window is 48 samples. Test with fewer.
    wav = np.array([0.1, 0.2, 0.9, 0.1], dtype=np.float32)

    original = apply_declick_original(wav, sr)
    optimized = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_allclose(original, optimized, atol=1e-6)

def test_declick_remainder():
    sr = 24000
    window = int(sr * 0.002)
    # Test with a buffer that isn't a multiple of the window
    n_samples = window * 2 + 5
    wav = np.random.normal(0, 0.1, n_samples).astype(np.float32)
    wav[n_samples - 2] = 0.9 # Spike in remainder

    original = apply_declick_original(wav, sr)
    optimized = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_allclose(original, optimized, atol=1e-6)
