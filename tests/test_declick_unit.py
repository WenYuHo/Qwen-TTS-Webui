import numpy as np
import pytest
from backend.utils import AudioPostProcessor

def test_declick_mono():
    sr = 24000
    # Use small noise so RMS is low but non-zero
    wav = np.random.uniform(-0.01, 0.01, 48000).astype(np.float32)
    # Add a huge spike
    wav[1000] = 5.0
    out = AudioPostProcessor.apply_declick(wav, sr)
    print(f"Mono spike: {out[1000]}")
    assert out[1000] < 5.0
    assert len(out) == len(wav)

def test_declick_short():
    sr = 24000
    wav = np.array([0.1, 5.0, 0.1], dtype=np.float32)
    out = AudioPostProcessor.apply_declick(wav, sr)
    assert np.allclose(out, wav)

def test_declick_remainder():
    sr = 24000
    window = int(sr * 0.002)
    wav = np.random.uniform(-0.01, 0.01, window + 10).astype(np.float32)
    wav[window + 5] = 5.0
    out = AudioPostProcessor.apply_declick(wav, sr)
    print(f"Remainder spike: {out[window+5]}")
    assert out[window + 5] < 5.0
