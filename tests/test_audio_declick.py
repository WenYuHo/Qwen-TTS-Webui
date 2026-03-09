import numpy as np
import pytest
from src.backend.utils import AudioPostProcessor

def test_apply_declick_logic():
    # Use a high sample rate to ensure window > 100 so a single spike can be detected
    sr = 96000
    wav = np.zeros(1000, dtype=np.float32)
    # Add a spike in the main part
    wav[500] = 1.0

    out = AudioPostProcessor.apply_declick(wav, sr)

    # It should have modified the spike
    assert out[500] < 1.0
    assert out[500] > 0
    # Other parts should remain 0
    assert out[0] == 0

def test_apply_declick_remainder_only():
    sr = 24000
    # window = 48 samples
    # We want a remainder that is > 100 samples.
    # To get main_len=48 and rem_len=152, total_len=200.
    # To get main_len=48, num_chunks must be 1.
    # sr=24000 * 0.002 = 48.

    # Let's override the sr logic slightly by choosing a weird sr
    # Or just use sr=24000, window=48.
    # Any length between 48 and 95 will have main_len=48.
    # Max remainder length is 47. 47 is not enough for sqrt(1/47) to be small enough.

    # Wait, the remainder can be ANY length if num_chunks is 0.
    # If len(wav) < window, it returns copy.
    # If len(wav) = window + 152 = 48 + 152 = 200.
    # num_chunks = 200 // 48 = 4. My math was wrong again.

    # If I want num_chunks=1 and rem_len=152:
    # window would need to be something else.
    # window is fixed by sr.

    # If I use sr = 24000 / 48 * 200 = 500 * 200 = 100000.
    # sr = 100000. window = 100000 * 0.002 = 200.
    # len(wav) = 350. num_chunks = 350 // 200 = 1. main_len = 200. rem_len = 150.

    sr_custom = 100000
    wav = np.zeros(350, dtype=np.float32)
    wav[349] = 1.0 # In remainder

    out = AudioPostProcessor.apply_declick(wav, sr_custom)
    assert out[349] < 1.0
    assert out[0] == 0

def test_apply_declick_stereo():
    sr = 96000
    wav = np.zeros((2, 1000), dtype=np.float32)
    wav[0, 500] = 1.0
    wav[1, 600] = 1.0

    out = AudioPostProcessor.apply_declick(wav, sr)

    assert out[0, 500] < 1.0
    assert out[1, 600] < 1.0
    assert np.all(out[:, 0:400] == 0)

def test_apply_declick_no_spikes():
    sr = 24000
    wav = np.random.uniform(-0.1, 0.1, 1000).astype(np.float32)
    out = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_array_equal(wav, out)

def test_apply_declick_short_signal():
    sr = 24000
    wav = np.array([0.1, 1.0], dtype=np.float32)
    # window will be 48. signal length 2.
    # Current impl returns copy if window >= signal len
    out = AudioPostProcessor.apply_declick(wav, sr)
    np.testing.assert_array_equal(wav, out)
