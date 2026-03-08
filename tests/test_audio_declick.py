import numpy as np
import pytest
from src.backend.utils import AudioPostProcessor

def test_apply_declick_mono():
    sr = 240000 # window = 480
    wav = np.random.normal(0, 0.01, 480).astype(np.float32)
    wav[5] = 1.0 # RMS ~ 0.045, threshold ~ 0.45.

    out = AudioPostProcessor.apply_declick(wav, sr)
    assert abs(out[5]) < 0.5

def test_apply_declick_remainder_caught():
    sr = 240000 # window 480
    # 480 samples (1 chunk) + 100 samples (remainder)
    # Total 580 samples.
    wav = np.random.normal(0, 0.01, 580).astype(np.float32)
    # Put spike in remainder (starts at index 480)
    wav[530] = 20.0
    # remainder size 100. RMS ~ sqrt(20^2 / 100) = 2.
    # Threshold (10x) = 20. 20.0 is not > 20.
    # Let's make it 30.0. RMS = 3. Threshold = 30. Still borderline.
    # Let's make the remainder larger or spike larger.
    wav[530] = 50.0
    # RMS = sqrt(50^2 / 100) = 5. Threshold = 50.
    # Use 100.0. RMS = 10. Threshold = 100.
    wav[530] = 200.0
    # RMS = sqrt(200^2 / 100) = 20. Threshold = 200.
    # Wait, if S is spike, N is window size. S/sqrt(N) * 10 < S => 10 < sqrt(N) => N > 100.
    # My remainder is 100. sqrt(100) = 10. Exactly 10.
    # So 10 * S / 10 = S. Heuristic says > thresholds. S > S is False.
    # So N must be > 100. Let's use 200 samples remainder.
    wav = np.random.normal(0, 0.01, 480 + 200).astype(np.float32)
    wav[480 + 100] = 100.0
    # N=200, sqrt(N) ~ 14.1. 10/14.1 ~ 0.7. 100 > 70. Caught!

    out = AudioPostProcessor.apply_declick(wav, sr)
    assert abs(out[480 + 100]) < 50.0

def test_apply_declick_identity():
    sr = 24000
    wav = np.random.normal(0, 0.01, 1000).astype(np.float32)
    out = AudioPostProcessor.apply_declick(wav, sr)
    assert out is wav

def test_apply_declick_stereo():
    sr = 240000
    wav = np.random.normal(0, 0.01, (2, 1000)).astype(np.float32)
    wav[0, 50] = 1.0
    wav[1, 100] = 1.0
    out = AudioPostProcessor.apply_declick(wav, sr)
    assert abs(out[0, 50]) < 0.5
    assert abs(out[1, 100]) < 0.5
