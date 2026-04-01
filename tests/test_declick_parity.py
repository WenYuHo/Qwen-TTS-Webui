import numpy as np
import pytest
import sys
import os

# Add src to path
sys.path.append(os.path.abspath("src"))
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

    for i in range(0, len(wav), window):
        chunk = wav[i:i+window]
        if len(chunk) < 2: continue
        local_rms = np.sqrt(np.mean(chunk**2)) + 1e-6
        spikes = np.abs(chunk) > (local_rms * 10)
        if np.any(spikes):
            sign = np.sign(chunk[spikes])
            out[i:i+window][spikes] = sign * local_rms * 3
    return out

def test_declick_parity():
    sr = 24000
    duration = 1.0
    wav = np.random.normal(0, 0.1, int(sr * duration)).astype(np.float32)
    # Add some spikes
    wav[100] = 0.9
    wav[5000] = -0.8

    original_out = original_apply_declick(wav, sr)
    optimized_out = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_allclose(original_out, optimized_out, atol=1e-7)

def test_declick_parity_stereo():
    sr = 24000
    wav = np.random.normal(0, 0.1, (2, int(sr * 0.1))).astype(np.float32)
    wav[0, 100] = 0.9
    wav[1, 200] = -0.9

    original_out = original_apply_declick(wav, sr)
    optimized_out = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_allclose(original_out, optimized_out, atol=1e-7)

def test_declick_edge_cases():
    sr = 24000
    # Empty
    wav_empty = np.array([], dtype=np.float32)
    assert len(AudioPostProcessor.apply_declick(wav_empty, sr)) == 0

    # Very short
    wav_short = np.array([0.1, 0.2], dtype=np.float32)
    np.testing.assert_allclose(AudioPostProcessor.apply_declick(wav_short, sr), wav_short)

    # No spikes
    wav_clean = np.linspace(0, 0.5, 1000).astype(np.float32)
    np.testing.assert_allclose(AudioPostProcessor.apply_declick(wav_clean, sr), wav_clean)
