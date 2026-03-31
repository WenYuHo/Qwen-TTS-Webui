import numpy as np
import pytest
import sys
import os

# Add src to path
sys.path.append(os.path.abspath("src"))

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

def test_declick_parity_mono():
    sr = 24000
    duration = 1.0
    n_samples = int(sr * duration)
    wav = np.random.uniform(-0.5, 0.5, n_samples).astype(np.float32)

    # Add some spikes
    wav[100] = 1.0
    wav[500] = -1.0
    wav[n_samples - 5] = 0.9 # In the tail

    from backend.utils import AudioPostProcessor

    res_orig = original_apply_declick(wav, sr)
    res_vec = AudioPostProcessor.apply_declick(wav, sr)

    assert np.allclose(res_orig, res_vec)
    assert np.array_equal(res_orig, res_vec)

def test_declick_parity_stereo():
    sr = 24000
    n_samples = 48000
    wav = np.random.uniform(-0.5, 0.5, (2, n_samples)).astype(np.float32)
    wav[0, 100] = 1.0
    wav[1, 200] = -1.0

    from backend.utils import AudioPostProcessor

    res_orig = original_apply_declick(wav, sr)
    res_vec = AudioPostProcessor.apply_declick(wav, sr)
    assert np.array_equal(res_orig, res_vec)

def test_declick_short_buffer():
    sr = 24000
    wav = np.array([0.1, 0.2, 0.3], dtype=np.float32)

    from backend.utils import AudioPostProcessor

    res_orig = original_apply_declick(wav, sr)
    res_vec = AudioPostProcessor.apply_declick(wav, sr)
    assert np.array_equal(res_orig, res_vec)
