import numpy as np
import pytest
import sys
import os

# Add src to path for imports
sys.path.append(os.path.abspath("src"))
from backend.utils import AudioPostProcessor

def original_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """Original loop-based implementation for parity checking."""
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
@pytest.mark.parametrize("is_stereo", [False, True])
@pytest.mark.parametrize("duration_ms", [10, 50, 100, 157]) # includes non-multiples of window
def test_declick_parity(sr, is_stereo, duration_ms):
    n_samples = int(sr * duration_ms / 1000)
    shape = (2, n_samples) if is_stereo else (n_samples,)

    # Generate random audio
    wav = np.random.normal(0, 0.1, shape).astype(np.float32)

    # Add some guaranteed spikes
    if is_stereo:
        wav[0, 10] = 0.9
        wav[1, 20] = -0.9
    else:
        if n_samples > 10:
            wav[10] = 0.9

    expected = original_apply_declick(wav, sr)
    actual = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_allclose(actual, expected, atol=1e-7, err_msg=f"Parity failed for sr={sr}, stereo={is_stereo}, duration={duration_ms}ms")

def test_declick_edge_cases():
    sr = 24000
    # Empty
    wav = np.array([], dtype=np.float32)
    assert len(AudioPostProcessor.apply_declick(wav, sr)) == 0

    # Very short (less than window)
    wav = np.array([0.1, 0.2], dtype=np.float32)
    np.testing.assert_allclose(AudioPostProcessor.apply_declick(wav, sr), wav)

    # Multi-channel (> 2)
    wav = np.random.normal(0, 0.1, (3, 1000)).astype(np.float32)
    expected = original_apply_declick(wav, sr)
    actual = AudioPostProcessor.apply_declick(wav, sr)
    np.testing.assert_allclose(actual, expected)
