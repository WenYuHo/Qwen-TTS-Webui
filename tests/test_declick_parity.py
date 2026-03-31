import pytest
import numpy as np
from backend.utils import AudioPostProcessor

def original_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """A copy of the original loop-based de-clicker for parity testing."""
    try:
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
    except Exception:
        return wav

def test_declick_parity_mono():
    sr = 24000
    duration = 1.0 # 1s
    n_samples = int(sr * duration)
    wav = np.random.normal(0, 0.1, n_samples).astype(np.float32)

    # Add spikes
    wav[100] = 0.9
    wav[5000] = -0.8
    wav[n_samples - 5] = 0.95 # spike in the tail

    expected = original_apply_declick(wav, sr)
    actual = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_array_almost_equal(expected, actual)

def test_declick_parity_stereo():
    sr = 24000
    duration = 0.5
    n_samples = int(sr * duration)
    wav = np.random.normal(0, 0.1, (2, n_samples)).astype(np.float32)

    # Add spikes to both channels
    wav[0, 200] = 0.9
    wav[1, 300] = -0.9

    expected = original_apply_declick(wav, sr)
    actual = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_array_almost_equal(expected, actual)

def test_declick_short_buffer():
    sr = 24000
    wav = np.array([0.1, 0.2], dtype=np.float32)

    # Window for 24k is 48 samples. 2 samples is way too short.
    expected = original_apply_declick(wav, sr)
    actual = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_array_almost_equal(expected, actual)

def test_declick_remainder_tail():
    sr = 24000
    window = int(sr * 0.002)
    # n_samples that is not a multiple of window
    n_samples = window * 10 + 5
    wav = np.random.normal(0, 0.1, n_samples).astype(np.float32)

    # Add spike in the remainder tail (last 5 samples)
    wav[-3] = 0.9

    expected = original_apply_declick(wav, sr)
    actual = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_array_almost_equal(expected, actual)
