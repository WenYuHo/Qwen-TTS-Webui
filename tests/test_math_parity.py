import numpy as np
import pytest

def rms_original(wav):
    return np.sqrt(np.mean(wav ** 2))

def rms_optimized(wav):
    return np.sqrt(np.vdot(wav, wav) / wav.size)

def peak_original(wav):
    return np.max(np.abs(wav))

def peak_optimized(wav):
    # For empty arrays, np.max/min fail, so handle that if needed,
    # but the codebases usually check for .size
    if wav.size == 0:
        return 0.0
    return max(np.max(wav), -np.min(wav))

@pytest.mark.parametrize("size", [10, 100, 1000, 10000])
def test_rms_parity(size):
    wav = np.random.uniform(-1, 1, size).astype(np.float32)
    assert np.allclose(rms_original(wav), rms_optimized(wav), atol=1e-7)

@pytest.mark.parametrize("size", [10, 100, 1000, 10000])
def test_peak_parity(size):
    wav = np.random.uniform(-1, 1, size).astype(np.float32)
    assert np.allclose(peak_original(wav), peak_optimized(wav), atol=1e-7)

def test_edge_cases():
    # All zeros
    wav = np.zeros(100)
    assert rms_original(wav) == rms_optimized(wav) == 0.0
    assert peak_original(wav) == peak_optimized(wav) == 0.0

    # Single value
    wav = np.array([0.5])
    assert np.allclose(rms_original(wav), rms_optimized(wav))
    assert np.allclose(peak_original(wav), peak_optimized(wav))

    # Negative peak
    wav = np.array([-0.9, 0.1, 0.5])
    assert np.allclose(peak_original(wav), peak_optimized(wav))
    assert peak_optimized(wav) == 0.9

    # Large values
    wav = np.random.uniform(-1e6, 1e6, 1000)
    assert np.allclose(rms_original(wav), rms_optimized(wav))
    assert np.allclose(peak_original(wav), peak_optimized(wav))
