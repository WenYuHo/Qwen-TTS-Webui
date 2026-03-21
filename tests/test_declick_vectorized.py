import numpy as np
from backend.utils import AudioPostProcessor

def test_apply_declick_mono():
    # Use high SR to ensure window size N > 100 so single spike can be detected.
    sr = 192000
    wav = np.zeros(sr, dtype=np.float32)
    wav[100] = 0.9
    out = AudioPostProcessor.apply_declick(wav, sr)
    assert len(out) == len(wav)
    assert abs(out[100]) < 0.9

def test_apply_declick_stereo():
    sr = 192000
    wav = np.zeros((2, sr), dtype=np.float32)
    wav[0, 100] = 0.9
    wav[1, 200] = -0.9

    out = AudioPostProcessor.apply_declick(wav, sr)
    assert out.shape == wav.shape
    assert abs(out[0, 100]) < 0.9
    assert abs(out[1, 200]) < 0.9

def test_apply_declick_small_buffer():
    sr = 24000
    wav = np.zeros(10, dtype=np.float32)
    out = AudioPostProcessor.apply_declick(wav, sr)
    assert len(out) == 10
    assert np.array_equal(wav, out)

def test_apply_declick_remainder():
    sr = 192000
    window = int(sr * 0.002) # 384
    # Create wav that is 1.5 windows long.
    # Total samples: 384 + 192 = 576.
    wav = np.zeros(int(window * 1.5), dtype=np.float32)
    # Put spike in the remainder part (after index 384).
    wav[window + 50] = 0.9

    out = AudioPostProcessor.apply_declick(wav, sr)
    assert len(out) == len(wav)
    assert abs(out[window + 50]) < 0.9
