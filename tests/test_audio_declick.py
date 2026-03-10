import numpy as np
import pytest
from backend.utils import AudioPostProcessor

def test_apply_declick_correctness():
    sr = 24000
    # Create a waveform with a known spike
    # window = 48
    wav = np.zeros(100, dtype=np.float32)
    # Background noise
    wav += np.random.normal(0, 0.001, 100).astype(np.float32)

    # A single spike at index 10
    wav[10] = 0.5

    # Original implementation for comparison
    def apply_declick_ref(wav, sr):
        out = wav.copy()
        window = int(sr * 0.002)
        for i in range(0, len(wav), window):
            chunk = wav[i:i+window]
            if len(chunk) < 2: continue
            local_rms = np.sqrt(np.mean(chunk**2)) + 1e-6
            spikes = np.abs(chunk) > (local_rms * 10)
            if np.any(spikes):
                sign = np.sign(chunk[spikes])
                out[i:i+window][spikes] = sign * local_rms * 3
        return out

    expected = apply_declick_ref(wav, sr)
    actual = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_allclose(actual, expected, atol=1e-7)

def test_apply_declick_multi_channel():
    sr = 24000
    wav = np.random.normal(0, 0.1, (2, 1000)).astype(np.float32)
    out = AudioPostProcessor.apply_declick(wav, sr)

    assert out.shape == wav.shape
    # Check that it processed both channels
    for i in range(wav.shape[0]):
        expected = AudioPostProcessor.apply_declick(wav[i], sr)
        np.testing.assert_allclose(out[i], expected, atol=1e-7)

def test_apply_declick_edge_cases():
    sr = 24000
    # Empty
    assert len(AudioPostProcessor.apply_declick(np.array([], dtype=np.float32), sr)) == 0

    # Too short for a window
    wav_short = np.array([0.1, 0.2], dtype=np.float32)
    out_short = AudioPostProcessor.apply_declick(wav_short, sr)
    # Should return a copy (as per my implementation)
    assert np.array_equal(out_short, wav_short)
    assert out_short is not wav_short

    # Exactly one window
    window = int(sr * 0.002)
    wav_exact = np.random.normal(0, 0.1, window).astype(np.float32)
    out_exact = AudioPostProcessor.apply_declick(wav_exact, sr)
    assert len(out_exact) == window
