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
@pytest.mark.parametrize("duration_ms", [10, 50, 100, 1000])
@pytest.mark.parametrize("channels", [1, 2])
def test_declick_parity(sr, duration_ms, channels):
    """Ensures vectorized de-clicker is mathematically identical to original loop-based logic."""
    n_samples = int(sr * duration_ms / 1000)
    if channels == 2:
        wav = np.random.randn(2, n_samples).astype(np.float32)
    else:
        wav = np.random.randn(n_samples).astype(np.float32)

    # Add artificial spikes
    if channels == 2:
        for _ in range(5):
            c = np.random.randint(0, 2)
            idx = np.random.randint(0, n_samples)
            wav[c, idx] *= 100
    else:
        for _ in range(5):
            idx = np.random.randint(0, n_samples)
            wav[idx] *= 100

    res_orig = original_apply_declick(wav, sr)
    res_vect = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_array_almost_equal(res_orig, res_vect, decimal=6)

def test_declick_edge_cases():
    sr = 24000
    # Very small buffer
    wav_small = np.array([1.0, 0.5], dtype=np.float32)
    res = AudioPostProcessor.apply_declick(wav_small, sr)
    assert len(res) == 2

    # Buffer exactly one window
    window = int(sr * 0.002)
    wav_window = np.random.randn(window).astype(np.float32)
    wav_window[0] = 100.0 # spike
    res_orig = original_apply_declick(wav_window, sr)
    res_vect = AudioPostProcessor.apply_declick(wav_window, sr)
    np.testing.assert_array_almost_equal(res_orig, res_vect)

    # Buffer with remainder 1
    wav_rem1 = np.random.randn(window + 1).astype(np.float32)
    res_orig = original_apply_declick(wav_rem1, sr)
    res_vect = AudioPostProcessor.apply_declick(wav_rem1, sr)
    np.testing.assert_array_almost_equal(res_orig, res_vect)
