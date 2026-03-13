import pytest
import numpy as np
from backend.utils import AudioPostProcessor

def test_declick_vectorized_mono():
    """Verify de-click optimization on mono audio."""
    sr = 192000 # High SR to ensure sqrt(window) > 10 for single spike detection
    # Create 1 second of noise
    wav = np.random.uniform(-0.01, 0.01, sr).astype(np.float32)
    # Add a clear spike
    spike_idx = sr // 2
    wav[spike_idx] = 1.0

    out = AudioPostProcessor.apply_declick(wav, sr)

    # Spike should be clamped
    assert out[spike_idx] < 0.9
    assert len(out) == len(wav)
    assert out.dtype == np.float32

def test_declick_vectorized_stereo():
    """Verify de-click optimization on stereo audio."""
    sr = 192000
    wav = np.random.uniform(-0.01, 0.01, (2, sr)).astype(np.float32)
    wav[0, sr // 2] = 1.0
    wav[1, sr // 2 + 100] = 1.0

    out = AudioPostProcessor.apply_declick(wav, sr)

    assert out.shape == (2, sr)
    assert out[0, sr // 2] < 0.9
    assert out[1, sr // 2 + 100] < 0.9

def test_declick_remainder_handling():
    """Verify that samples not fitting into a 2ms window are still processed or preserved."""
    sr = 192000
    window = int(sr * 0.002) # 384 samples
    # window + 150 samples remainder (N > 100 required for single spike detection)
    wav = np.random.uniform(-0.001, 0.001, window + 150).astype(np.float32)
    # Spike in the remainder
    wav[-1] = 1.0

    out = AudioPostProcessor.apply_declick(wav, sr)

    assert len(out) == window + 150
    assert out[-1] < 0.9

def test_declick_short_audio():
    """Verify that audio shorter than one window is handled without error."""
    sr = 24000
    wav = np.array([0.1, 1.0, 0.1], dtype=np.float32)

    # Should still work or return original if too short
    out = AudioPostProcessor.apply_declick(wav, sr)
    assert len(out) == 3
