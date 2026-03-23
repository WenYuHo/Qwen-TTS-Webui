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

    for i in range(0, len(wav), window):
        chunk = wav[i:i+window]
        if len(chunk) < 2: continue
        local_rms = np.sqrt(np.mean(chunk**2)) + 1e-6
        spikes = np.abs(chunk) > (local_rms * 10)
        if np.any(spikes):
            sign = np.sign(chunk[spikes])
            out[i:i+window][spikes] = sign * local_rms * 3
    return out

def test_declick_parity_mono():
    sr = 24000
    # Create random audio with spikes
    np.random.seed(42)
    duration = 0.1 # 100ms
    n_samples = int(duration * sr)
    wav = np.random.normal(0, 0.1, n_samples).astype(np.float32)

    # Add spikes
    spike_indices = [100, 500, 1000, 2000]
    wav[spike_indices] = [0.9, -0.8, 1.0, -0.9]

    # Get original result
    expected = apply_declick_original(wav, sr)

    # Get current (to be optimized) result
    actual = AudioPostProcessor.apply_declick(wav, sr)

    # They should be identical now
    assert np.allclose(expected, actual)

def test_declick_parity_stereo():
    sr = 24000
    np.random.seed(42)
    n_samples = 1000
    wav = np.random.normal(0, 0.1, (2, n_samples)).astype(np.float32)
    wav[0, 100] = 1.0
    wav[1, 200] = -1.0

    expected = apply_declick_original(wav, sr)
    actual = AudioPostProcessor.apply_declick(wav, sr)

    assert np.allclose(expected, actual)

def test_declick_edge_cases():
    sr = 24000
    # Very short buffer
    short_wav = np.array([0.1, 0.2], dtype=np.float32)
    assert np.array_equal(AudioPostProcessor.apply_declick(short_wav, sr), short_wav)

    # Remainder handling
    window = int(sr * 0.002)
    wav = np.random.normal(0, 0.1, window + 5).astype(np.float32)
    wav[window + 2] = 1.0 # Spike in remainder

    expected = apply_declick_original(wav, sr)
    actual = AudioPostProcessor.apply_declick(wav, sr)
    assert np.allclose(expected, actual)
