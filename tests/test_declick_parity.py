import numpy as np
import pytest
from backend.utils import AudioPostProcessor

def apply_declick_reference(wav: np.ndarray, sr: int) -> np.ndarray:
    """Original loop-based implementation for parity checking."""
    if len(wav.shape) > 1:
        out = np.zeros_like(wav)
        for i in range(wav.shape[0]):
            out[i] = apply_declick_reference(wav[i], sr)
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
@pytest.mark.parametrize("duration", [0.1, 1.0, 5.0])
def test_declick_parity(sr, duration):
    n_samples = int(sr * duration)
    # Random audio
    wav = np.random.uniform(-0.5, 0.5, n_samples).astype(np.float32)
    # Add deterministic spikes
    # Use indices that are definitely within bounds
    spike_indices = [n_samples // 10, n_samples // 2, n_samples - 5]
    for idx in spike_indices:
        if 0 <= idx < n_samples:
            wav[idx] = 0.95

    ref_out = apply_declick_reference(wav, sr)
    opt_out = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_allclose(ref_out, opt_out, atol=1e-6)

def test_declick_stereo_parity():
    sr = 24000
    n_samples = int(sr * 0.5)
    wav = np.random.uniform(-0.5, 0.5, (2, n_samples)).astype(np.float32)
    # Add spikes to both channels
    wav[0, n_samples // 4] = 0.9
    wav[1, n_samples // 2] = -0.9

    ref_out = apply_declick_reference(wav, sr)
    opt_out = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_allclose(ref_out, opt_out, atol=1e-6)

def test_declick_small_buffer():
    sr = 24000
    # Buffer smaller than window (2ms = 48 samples)
    wav = np.random.uniform(-0.5, 0.5, 20).astype(np.float32)

    ref_out = apply_declick_reference(wav, sr)
    opt_out = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_allclose(ref_out, opt_out, atol=1e-6)

def test_declick_remainder_parity():
    sr = 24000
    window_size = int(sr * 0.002)
    # Create a buffer that is not a multiple of window_size
    n_samples = window_size * 2 + 10
    wav = np.random.uniform(-0.1, 0.1, n_samples).astype(np.float32)
    # Add a spike in the remainder part
    wav[window_size * 2 + 5] = 0.9

    ref_out = apply_declick_reference(wav, sr)
    opt_out = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_allclose(ref_out, opt_out, atol=1e-6)
