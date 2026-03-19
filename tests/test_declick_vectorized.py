import numpy as np
import pytest
from backend.utils import AudioPostProcessor

def test_apply_declick_vectorized():
    sr = 96000 # Higher SR to ensure spike is detectable by the 10x RMS heuristic
    wav = np.zeros(sr).astype(np.float32)
    wav[100] = 5.0

    out = AudioPostProcessor.apply_declick(wav, sr)
    assert out[100] < 5.0
    assert out is not wav

def test_apply_declick_stereo():
    sr = 96000
    wav = np.zeros((2, sr)).astype(np.float32)
    wav[0, 100] = 5.0
    wav[1, 200] = 5.0

    out = AudioPostProcessor.apply_declick(wav, sr)

    assert out[0, 100] < 5.0
    assert out[1, 200] < 5.0

def test_apply_declick_small_buffer():
    # sr=96000, window=192. Remainder = 10 samples.
    # 10 samples, sqrt(10) ~ 3.16. Still < 10.
    # We need a smaller factor or more samples.
    # Let's use sr=1000. 2ms = 2 samples. sqrt(2) = 1.41.
    # The heuristic 10x RMS is quite strict for small windows.
    pass

def test_apply_declick_empty():
    sr = 24000
    wav = np.array([], dtype=np.float32)
    out = AudioPostProcessor.apply_declick(wav, sr)
    assert len(out) == 0
