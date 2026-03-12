import numpy as np
import sys
import os
import pytest

# Add src to path
sys.path.append(os.path.abspath("src"))

from backend.utils import AudioPostProcessor

def test_declick_mono():
    # Use higher SR to get a window > 100 samples so single spikes can be detected
    sr = 96000
    # Window size will be int(96000 * 0.002) = 192
    wav = np.ones(192, dtype=np.float32) * 0.001
    wav[10] = 0.5

    # Debug info
    rms = np.sqrt(np.mean(wav**2))
    print(f"\nSR: {sr}, Window: 192, RMS: {rms}, Threshold: {rms*10}")

    out = AudioPostProcessor.apply_declick(wav, sr)

    assert out.shape == wav.shape
    assert not np.array_equal(wav, out)
    assert out[100] < 0.5
    assert np.all(np.abs(out) <= 1.0)

def test_declick_stereo():
    sr = 96000
    wav = np.ones((2, 192), dtype=np.float32) * 0.001
    wav[0, 100] = 0.5
    wav[1, 100] = -0.5

    out = AudioPostProcessor.apply_declick(wav, sr)

    assert out.shape == wav.shape
    assert out[0, 100] < 0.5
    assert out[1, 100] > -0.5

def test_declick_remainder():
    sr = 192000 # window = 384
    # Length that is not a multiple of window
    # Remainder length should be 200
    wav = np.ones(384 * 2 + 200, dtype=np.float32) * 0.001
    wav[-5] = 0.5 # In the remainder (length 200)

    rem_rms = np.sqrt(np.mean(wav[384*2:]**2))
    print(f"\nRemainder SR: {sr}, RMS: {rem_rms}, Threshold: {rem_rms*10}")

    out = AudioPostProcessor.apply_declick(wav, sr)

    assert out.shape == wav.shape
    assert out[-5] < 0.5

def test_declick_identity():
    sr = 24000
    # Silent/Low audio should be unchanged
    wav = np.zeros(sr, dtype=np.float32)
    out = AudioPostProcessor.apply_declick(wav, sr)
    assert np.array_equal(wav, out)

def test_declick_copy():
    sr = 24000
    wav = np.zeros(sr, dtype=np.float32)
    out = AudioPostProcessor.apply_declick(wav, sr)
    assert out is not wav # Should be a copy
