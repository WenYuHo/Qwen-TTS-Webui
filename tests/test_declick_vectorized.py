import pytest
import numpy as np
from backend.utils import AudioPostProcessor

def test_declick_vectorized_parity():
    """Verify that the vectorized de-clicker matches the original loop-based logic."""
    sr = 24000
    # Create random audio with some high-amplitude spikes
    n_samples = sr * 2 # 2 seconds
    wav = np.random.normal(0, 0.1, n_samples).astype(np.float32)

    # Add spikes that are > 10x local RMS (which is ~0.1 here)
    spike_indices = np.random.choice(n_samples, 50, replace=False)
    wav[spike_indices] = np.random.choice([-1.0, 1.0], 50) * 0.9

    # Original loop-based implementation (re-implemented here for verification)
    def apply_declick_original(wav, sr):
        out = wav.copy()
        window = int(sr * 0.002) # 2ms
        if window < 2: return wav
        for i in range(0, len(wav), window):
            chunk = wav[i:i+window]
            if len(chunk) < 2: continue
            local_rms = np.sqrt(np.mean(chunk**2)) + 1e-6
            spikes = np.abs(chunk) > (local_rms * 10)
            if np.any(spikes):
                sign = np.sign(chunk[spikes])
                out[i:i+window][spikes] = sign * local_rms * 3
        return out

    orig = apply_declick_original(wav, sr)
    vect = AudioPostProcessor.apply_declick(wav, sr)

    # Check for mathematical identity (within float precision)
    np.testing.assert_allclose(orig, vect, atol=1e-7)

def test_declick_stereo_support():
    """Verify that de-clicking handles stereo signals correctly."""
    # Use high sample rate to ensure window size N > 100 so sqrt(N) > 10
    # This allows a single spike to trigger the 10x RMS heuristic.
    sr = 100000
    n_samples = sr
    wav_stereo = np.zeros((2, n_samples), dtype=np.float32)

    # Add high-amplitude spikes to both channels
    wav_stereo[0, 100] = 1.0
    wav_stereo[1, 200] = -1.0

    out = AudioPostProcessor.apply_declick(wav_stereo, sr)

    assert out.shape == (2, n_samples)
    # Check that spikes were clamped
    assert np.abs(out[0, 100]) < 1.0
    assert np.abs(out[1, 200]) < 1.0

def test_declick_small_buffer():
    """Verify that de-clicking handles buffers smaller than the window size."""
    sr = 24000
    window = int(sr * 0.002)
    wav_small = np.random.normal(0, 0.1, window // 2).astype(np.float32)

    # Should return original for buffers with < 2 samples, or handle remainder correctly
    out = AudioPostProcessor.apply_declick(wav_small, sr)
    assert len(out) == len(wav_small)
