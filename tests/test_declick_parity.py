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

@pytest.mark.parametrize("sr", [24000, 44100, 48000])
@pytest.mark.parametrize("duration", [0.1, 0.5, 1.0])
@pytest.mark.parametrize("is_stereo", [False, True])
def test_declick_parity(sr, duration, is_stereo):
    n_samples = int(sr * duration)
    if is_stereo:
        wav = np.random.normal(0, 0.1, (2, n_samples)).astype(np.float32)
        # Add some spikes
        wav[0, n_samples // 4] = 0.9
        wav[1, n_samples // 2] = -0.9
    else:
        wav = np.random.normal(0, 0.1, n_samples).astype(np.float32)
        # Add some spikes
        wav[n_samples // 4] = 0.9
        wav[n_samples // 2] = -0.9

    original_out = original_apply_declick(wav, sr)
    optimized_out = AudioPostProcessor.apply_declick(wav, sr)

    # Use small atol because of potential floating point differences if using einsum vs mean
    np.testing.assert_allclose(original_out, optimized_out, atol=1e-7)

def test_declick_edge_cases():
    sr = 24000
    # Empty
    wav_empty = np.array([], dtype=np.float32)
    assert np.array_equal(AudioPostProcessor.apply_declick(wav_empty, sr), wav_empty)

    # Very short
    wav_short = np.array([0.1], dtype=np.float32)
    assert np.array_equal(AudioPostProcessor.apply_declick(wav_short, sr), wav_short)

    # No spikes
    wav_clean = np.random.normal(0, 0.01, 1000).astype(np.float32)
    assert np.allclose(AudioPostProcessor.apply_declick(wav_clean, sr), wav_clean)
