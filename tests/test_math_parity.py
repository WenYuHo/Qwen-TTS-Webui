import numpy as np
import pytest

def original_rms(wav):
    return np.sqrt(np.mean(wav ** 2))

def optimized_rms(wav):
    return np.sqrt(np.vdot(wav, wav) / wav.size)

def original_peak(wav):
    return np.max(np.abs(wav))

def optimized_peak(wav):
    return max(np.max(wav), -np.min(wav))

@pytest.mark.parametrize("size", [100, 1000, 10000])
@pytest.mark.parametrize("dtype", [np.float32, np.float64])
def test_rms_parity(size, dtype):
    wav = np.random.uniform(-1, 1, size).astype(dtype)
    res_orig = original_rms(wav)
    res_opt = optimized_rms(wav)
    assert np.allclose(res_orig, res_opt)

@pytest.mark.parametrize("size", [100, 1000, 10000])
@pytest.mark.parametrize("dtype", [np.float32, np.float64])
def test_peak_parity(size, dtype):
    wav = np.random.uniform(-1, 1, size).astype(dtype)
    res_orig = original_peak(wav)
    res_opt = optimized_peak(wav)
    assert np.allclose(res_orig, res_opt)

def test_edge_cases():
    # Silence
    wav = np.zeros(1000)
    assert optimized_rms(wav) == 0
    assert optimized_peak(wav) == 0

    # Single spike
    wav = np.zeros(1000)
    wav[500] = 1.0
    assert np.allclose(optimized_peak(wav), 1.0)

    # Negative spike
    wav = np.zeros(1000)
    wav[500] = -1.0
    assert np.allclose(optimized_peak(wav), 1.0)

if __name__ == "__main__":
    pytest.main([__file__])
