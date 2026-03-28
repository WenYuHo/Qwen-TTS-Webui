import numpy as np
import pytest
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.append(os.path.abspath("src"))
from backend.utils import AudioPostProcessor

def reference_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """The original loop-based implementation to use as a reference."""
    if len(wav.shape) > 1:
        out = np.zeros_like(wav)
        for i in range(wav.shape[0]):
            out[i] = reference_apply_declick(wav[i], sr)
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
    duration = 1.0
    wav = np.random.normal(0, 0.1, int(sr * duration)).astype(np.float32)

    # Add some spikes
    wav[100] = 0.9
    wav[500] = -0.8
    wav[2000] = 0.95

    ref_out = reference_apply_declick(wav, sr)
    opt_out = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_allclose(ref_out, opt_out, rtol=1e-5, atol=1e-5)

def test_declick_parity_stereo():
    sr = 24000
    duration = 0.5
    wav = np.random.normal(0, 0.1, (2, int(sr * duration))).astype(np.float32)

    # Add spikes to both channels
    wav[0, 100] = 0.9
    wav[1, 200] = -0.8

    ref_out = reference_apply_declick(wav, sr)
    opt_out = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_allclose(ref_out, opt_out, rtol=1e-5, atol=1e-5)

def test_declick_parity_short():
    sr = 24000
    # Less than 2ms (48 samples)
    wav = np.random.normal(0, 0.1, 30).astype(np.float32)

    ref_out = reference_apply_declick(wav, sr)
    opt_out = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_allclose(ref_out, opt_out, rtol=1e-5, atol=1e-5)

def test_declick_parity_remainder():
    sr = 24000
    # Not a multiple of window size (48)
    wav = np.random.normal(0, 0.1, 100).astype(np.float32)
    wav[90] = 0.9 # Spike in remainder

    ref_out = reference_apply_declick(wav, sr)
    opt_out = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_allclose(ref_out, opt_out, rtol=1e-5, atol=1e-5)
