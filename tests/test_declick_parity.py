import numpy as np
import pytest
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

@pytest.mark.parametrize("sr", [16000, 24000, 44100, 48000])
@pytest.mark.parametrize("duration", [0.1, 0.5, 1.0])
@pytest.mark.parametrize("is_stereo", [False, True])
def test_declick_parity(sr, duration, is_stereo):
    n_samples = int(sr * duration)
    if is_stereo:
        wav = np.random.normal(0, 0.1, (2, n_samples)).astype(np.float32)
        # Add random spikes
        for c in range(2):
            spike_indices = np.random.choice(n_samples, 10, replace=False)
            wav[c, spike_indices] = np.random.choice([-1.0, 1.0], 10) * 0.9
    else:
        wav = np.random.normal(0, 0.1, n_samples).astype(np.float32)
        # Add random spikes
        spike_indices = np.random.choice(n_samples, 10, replace=False)
        wav[spike_indices] = np.random.choice([-1.0, 1.0], 10) * 0.9

    original_out = original_apply_declick(wav, sr)
    vectorized_out = AudioPostProcessor.apply_declick(wav, sr)

    # They should be identical before any changes as well
    np.testing.assert_allclose(original_out, vectorized_out, atol=1e-7)

def test_declick_tail_processing():
    """Ensure the remainder of the audio (less than one window) is handled identically."""
    sr = 24000
    window = int(sr * 0.002)
    # 2.5 windows long
    n_samples = int(window * 2.5)

    wav = np.random.normal(0, 0.1, n_samples).astype(np.float32)
    # Add a spike in the last half-window
    wav[-1] = 0.9

    original_out = original_apply_declick(wav, sr)
    vectorized_out = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_allclose(original_out, vectorized_out, atol=1e-7)
