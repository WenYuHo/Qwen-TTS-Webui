import pytest
import numpy as np
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

@pytest.mark.parametrize("sr", [24000, 44100, 96000])
@pytest.mark.parametrize("duration", [0.1, 0.5, 1.0])
@pytest.mark.parametrize("channels", [1, 2])
def test_declick_parity(sr, duration, channels):
    """Verify that vectorized de-clicker matches the original loop-based logic."""
    n_samples = int(sr * duration)
    if channels == 1:
        wav = np.random.uniform(-0.1, 0.1, n_samples).astype(np.float32)
    else:
        wav = np.random.uniform(-0.1, 0.1, (channels, n_samples)).astype(np.float32)

    # Add deterministic spikes
    if channels == 1:
        wav[n_samples // 10] = 1.0
        wav[n_samples // 2] = -1.0
    else:
        wav[0, n_samples // 10] = 1.0
        wav[1, n_samples // 2] = -1.0

    original_out = original_apply_declick(wav, sr)
    vectorized_out = AudioPostProcessor.apply_declick(wav, sr)

    # Assert near equality (float32 precision)
    np.testing.assert_allclose(vectorized_out, original_out, atol=1e-6)

def test_declick_short_buffer():
    """Verify handling of buffers shorter than window size."""
    sr = 24000
    wav = np.array([1.0, 0.5], dtype=np.float32)
    # window_size for 24kHz is 48 samples. 2 samples is < window_size.
    out = AudioPostProcessor.apply_declick(wav, sr)
    assert np.array_equal(out, wav)

def test_declick_tail_processing():
    """Verify that spikes in the non-aligned 'tail' are also handled."""
    # Use high sample rate so that a single spike significantly exceeds 10x RMS
    sr = 96000
    window = int(sr * 0.002) # 192 samples
    # Create wav with 192 (one full window) + 150 samples (tail)
    # For a 150-sample tail, 1 spike makes RMS = sqrt(1/150) approx 0.0816.
    # 10x RMS approx 0.816, so a 1.0 spike SHOULD be detected.
    wav = np.zeros(window + 150, dtype=np.float32)
    wav[-75] = 1.0 # Spike in the middle of the tail

    original_out = original_apply_declick(wav, sr)
    vectorized_out = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_allclose(vectorized_out, original_out, atol=1e-6)
    # Also verify it actually clamped
    assert vectorized_out[-75] < 1.0
