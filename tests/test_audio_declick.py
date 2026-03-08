import numpy as np
import pytest
from backend.utils import AudioPostProcessor

def test_apply_declick_basic():
    # SR=96000 gives window = 192. sqrt(192) ~= 13.8 > 10.
    sr_high = 96000
    wav_high = np.zeros(2000, dtype=np.float32)
    wav_high[200] = 1.0

    out = AudioPostProcessor.apply_declick(wav_high, sr_high)
    assert abs(out[200]) < 1.0
    assert out[200] > 0

def test_apply_declick_stereo():
    sr = 96000
    wav = np.zeros((2, 2000), dtype=np.float32)
    wav[0, 200] = 1.0
    wav[1, 400] = 1.0

    out = AudioPostProcessor.apply_declick(wav, sr)

    assert abs(out[0, 200]) < 1.0
    assert abs(out[1, 400]) < 1.0
    assert out.shape == (2, 2000)

def test_apply_declick_no_spikes():
    sr = 24000
    wav = np.random.normal(0, 0.01, 2400).astype(np.float32)

    out = AudioPostProcessor.apply_declick(wav, sr)
    np.testing.assert_allclose(out, wav)

def test_apply_declick_remainder():
    # Use very high SR to ensure remainder is large enough for heuristic to trigger
    sr = 1000000
    window = int(sr * 0.002) # 2000
    wav = np.zeros(window + 500, dtype=np.float32)
    wav[window + 250] = 1.0

    out = AudioPostProcessor.apply_declick(wav, sr)
    assert abs(out[window + 250]) < 1.0

def test_apply_declick_small_audio():
    sr = 24000
    wav = np.zeros(10, dtype=np.float32)
    out = AudioPostProcessor.apply_declick(wav, sr)
    assert np.array_equal(out, wav)
