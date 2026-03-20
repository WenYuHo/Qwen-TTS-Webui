import numpy as np
import pytest
from backend.utils import AudioPostProcessor

def test_declick_vectorized():
    sr = 24000
    duration = 1
    n_samples = duration * sr

    # window is 48 samples.
    # To detect a single spike of 2.0, threshold must be < 2.0.
    # rms = sqrt((47 * noise^2 + 2.0^2) / 48)
    # threshold = 10 * rms
    # For detection: 2.0 > 10 * sqrt((47*noise^2 + 4) / 48)
    # 0.2 > sqrt((47*noise^2 + 4) / 48)
    # 0.04 > (47*noise^2 + 4) / 48
    # 1.92 > 47*noise^2 + 4
    # -2.08 > 47*noise^2  --> IMPOSSIBLE for a single spike to trigger it if window=48.

    # If sqrt(N) <= 10, a single spike CANNOT trigger the heuristic because the spike itself
    # raises the RMS enough to stay below the 10x threshold.

    # We need a larger window or a different test.
    # Let's use a very low sample rate to get a smaller window, OR just use multiple spikes.

    sr_low = 44100 # window = 88. sqrt(88) = 9.38. Still <= 10.
    sr_high = 96000 # window = 192. sqrt(192) = 13.85. > 10!

    n_samples = sr_high
    wav = np.random.normal(0, 0.01, n_samples).astype(np.float32)
    spike_idx = 500
    wav[spike_idx] = 2.0

    # Check math:
    # rms = sqrt((191*0.01^2 + 2^2)/192) = sqrt((0.0191 + 4)/192) = sqrt(0.0209) = 0.144
    # threshold = 1.44.
    # 2.0 > 1.44. YES!

    out = AudioPostProcessor.apply_declick(wav, sr_high)

    assert abs(out[spike_idx]) < 2.0
    assert len(out) == len(wav)

def test_declick_stereo():
    sr = 96000
    wav = np.random.normal(0, 0.01, (2, 96000)).astype(np.float32)
    wav[0, 500] = 2.0
    wav[1, 1000] = 2.0

    out = AudioPostProcessor.apply_declick(wav, sr)

    assert out.shape == wav.shape
    assert abs(out[0, 500]) < 2.0
    assert abs(out[1, 1000]) < 2.0

def test_declick_short():
    sr = 24000
    wav = np.array([0.1, 2.0, 0.1], dtype=np.float32)
    out = AudioPostProcessor.apply_declick(wav, sr)
    assert np.array_equal(out, wav)
    assert out is not wav
