import numpy as np
import pytest
from backend.utils import AudioPostProcessor

def test_apply_declick_mono_no_spikes():
    sr = 24000
    wav = np.sin(2 * np.pi * 440 * np.linspace(0, 0.1, 2400)).astype(np.float32) * 0.5
    out = AudioPostProcessor.apply_declick(wav, sr)
    # Should be no spikes detected, so out should be equal to wav
    assert np.allclose(wav, out)

def test_apply_declick_mono_with_spike():
    sr = 48000 # Use higher SR so sqrt(N) > 10, N = 48000 * 0.002 = 96. Still < 100.
    # Let's use SR = 96000 for the test to ensure detection if we want to test detection.
    # Or just use a very low threshold in our own mind.
    # Actually, let's use SR=100000. N=200. sqrt(200) = 14.14 > 10.
    sr = 100000
    wav = np.zeros(1000, dtype=np.float32)
    wav[500] = 1.0 # Spike

    out = AudioPostProcessor.apply_declick(wav, sr)

    # Check if spike at 500 was clamped
    assert out[500] < 1.0
    assert out[500] > 0
    # Check that other parts are still zero
    assert np.all(out[:500] == 0)
    assert np.all(out[501:] == 0)

def test_apply_declick_stereo():
    sr = 100000
    wav = np.zeros((2, 1000), dtype=np.float32)
    wav[0, 200] = 1.0 # Spike in left
    wav[1, 800] = 1.0 # Spike in right

    out = AudioPostProcessor.apply_declick(wav, sr)

    assert out[0, 200] < 1.0
    assert out[1, 800] < 1.0
    assert out[0, 800] == 0
    assert out[1, 200] == 0

def test_apply_declick_short_wav():
    sr = 24000
    # Window is 48 samples. Let's provide 10.
    wav = np.ones(10, dtype=np.float32)
    out = AudioPostProcessor.apply_declick(wav, sr)
    assert np.array_equal(wav, out)

def test_apply_declick_identity_sr_too_low():
    sr = 400 # 2ms * 400 = 0.8 samples. window will be 0.
    wav = np.ones(100, dtype=np.float32)
    out = AudioPostProcessor.apply_declick(wav, sr)
    assert np.array_equal(wav, out)
