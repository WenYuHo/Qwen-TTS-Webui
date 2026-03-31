import numpy as np
import pytest
import sys
import os

# Add src to path for imports
sys.path.append(os.path.abspath("src"))
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

@pytest.mark.parametrize("duration", [1, 5, 10])
@pytest.mark.parametrize("sr", [16000, 24000, 44100])
@pytest.mark.parametrize("channels", [1, 2])
def test_declick_parity(duration, sr, channels):
    n_samples = duration * sr
    if channels == 1:
        wav = np.random.normal(0, 0.1, n_samples).astype(np.float32)
        # Add some spikes
        spike_indices = np.random.choice(n_samples, 10, replace=False)
        wav[spike_indices] = np.random.choice([-1.0, 1.0], 10) * 0.9
    else:
        wav = np.random.normal(0, 0.1, (channels, n_samples)).astype(np.float32)
        # Add some spikes
        for c in range(channels):
            spike_indices = np.random.choice(n_samples, 10, replace=False)
            wav[c, spike_indices] = np.random.choice([-1.0, 1.0], 10) * 0.9

    expected = original_apply_declick(wav, sr)
    actual = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_allclose(actual, expected, atol=1e-7)

def test_declick_short_audio():
    sr = 24000
    wav = np.random.normal(0, 0.1, 10).astype(np.float32) # Very short

    expected = original_apply_declick(wav, sr)
    actual = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_allclose(actual, expected, atol=1e-7)

def test_declick_tail_processing():
    sr = 24000
    window = int(sr * 0.002)
    # 1.5 windows
    n_samples = int(window * 1.5)
    wav = np.random.normal(0, 0.1, n_samples).astype(np.float32)

    # Add spike in the tail
    wav[-1] = 0.9

    expected = original_apply_declick(wav, sr)
    actual = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_allclose(actual, expected, atol=1e-7)
