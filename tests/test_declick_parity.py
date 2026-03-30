import numpy as np
import pytest
from backend.utils import AudioPostProcessor

def original_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """Original loop-based de-clicker implementation for parity testing."""
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

@pytest.mark.parametrize("sr", [24000, 44100, 48000, 96000])
@pytest.mark.parametrize("duration", [0.01, 0.1, 0.5, 1.0])
@pytest.mark.parametrize("channels", [1, 2])
def test_declick_parity(sr, duration, channels):
    n_samples = int(sr * duration)
    if channels == 1:
        wav = np.random.normal(0, 0.1, n_samples).astype(np.float32)
    else:
        wav = np.random.normal(0, 0.1, (channels, n_samples)).astype(np.float32)

    # Add several deterministic spikes at different column positions
    # column_idx = abs_idx % window_size
    window_size = int(sr * 0.002)
    if window_size < 2: return # skip

    if channels == 1:
        # Spike at start of a window (col 0)
        wav[0] = 0.9
        # Spike at end of a window (col window_size - 1)
        if n_samples > window_size:
            wav[window_size - 1] = -0.9
        # Spike in the middle
        wav[n_samples // 2] = 0.8
        # Spike in the remainder
        wav[-1] = -0.8
    else:
        # Channel 0
        wav[0, 0] = 0.9
        wav[0, n_samples // 2] = 0.8
        # Channel 1
        if n_samples > window_size:
             wav[1, window_size - 1] = -0.9
        wav[1, -1] = -0.8

    original_out = original_apply_declick(wav, sr)
    optimized_out = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_allclose(original_out, optimized_out, rtol=1e-5, atol=1e-7)

def test_declick_edge_cases():
    sr = 24000

    # Case 1: Empty buffer
    wav_empty = np.array([], dtype=np.float32)
    assert np.array_equal(original_apply_declick(wav_empty, sr), AudioPostProcessor.apply_declick(wav_empty, sr))

    # Case 2: Buffer smaller than window (but > 2 samples)
    # sr * 0.002 = 48 samples
    wav_small = np.random.normal(0, 0.1, 10).astype(np.float32)
    wav_small[5] = 1.0
    np.testing.assert_allclose(original_apply_declick(wav_small, sr), AudioPostProcessor.apply_declick(wav_small, sr))

    # Case 3: Single sample (should return copy)
    wav_single = np.array([0.1], dtype=np.float32)
    assert np.array_equal(original_apply_declick(wav_single, sr), AudioPostProcessor.apply_declick(wav_single, sr))
