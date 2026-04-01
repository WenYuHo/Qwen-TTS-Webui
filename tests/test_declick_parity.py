import numpy as np
import pytest
from backend.utils import AudioPostProcessor

def original_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """Original loop-based implementation for parity testing."""
    if len(wav.shape) > 1:
        out = np.zeros_like(wav)
        for i in range(wav.shape[0]):
            out[i] = original_apply_declick(wav[i], sr)
        return out

    out = wav.copy()
    window = int(sr * 0.002) # 2ms
    if window < 2: return wav

    # Process in chunks
    for i in range(0, len(wav), window):
        chunk = wav[i:i+window]
        if len(chunk) < 2: continue
        local_rms = np.sqrt(np.mean(chunk**2)) + 1e-6
        # Identify spikes
        spikes = np.abs(chunk) > (local_rms * 10)
        if np.any(spikes):
            # Clamp spikes to local RMS * 3
            sign = np.sign(chunk[spikes])
            out[i:i+window][spikes] = sign * local_rms * 3
    return out

def test_declick_parity_mono():
    sr = 24000
    duration = 1.0 # 1 second
    n_samples = int(sr * duration)

    # Generate random audio with some spikes
    np.random.seed(42)
    wav = np.random.normal(0, 0.1, n_samples).astype(np.float32)

    # Add some significant spikes
    spike_indices = [100, 5000, 12000, 23000]
    wav[spike_indices] = [0.9, -0.85, 0.95, -0.99]

    # Currently AudioPostProcessor.apply_declick is the loop version
    result_optimized = AudioPostProcessor.apply_declick(wav, sr)
    result_original = original_apply_declick(wav, sr)

    assert np.allclose(result_optimized, result_original, atol=1e-7)

def test_declick_parity_stereo():
    sr = 24000
    duration = 0.5
    n_samples = int(sr * duration)

    np.random.seed(42)
    wav = np.random.normal(0, 0.1, (2, n_samples)).astype(np.float32)

    # Add spikes to both channels
    wav[0, 1000] = 0.9
    wav[1, 5000] = -0.8

    result_optimized = AudioPostProcessor.apply_declick(wav, sr)
    result_original = original_apply_declick(wav, sr)

    assert np.allclose(result_optimized, result_original, atol=1e-7)

def test_declick_edge_cases():
    sr = 24000

    # 1. Very short audio (less than 2ms)
    short_wav = np.array([0.1, 0.5], dtype=np.float32)
    assert np.array_equal(AudioPostProcessor.apply_declick(short_wav, sr), short_wav)

    # 2. All zeros
    zeros = np.zeros(1000, dtype=np.float32)
    assert np.array_equal(AudioPostProcessor.apply_declick(zeros, sr), zeros)

    # 3. No spikes
    clean = np.ones(1000, dtype=np.float32) * 0.1
    assert np.array_equal(AudioPostProcessor.apply_declick(clean, sr), clean)
