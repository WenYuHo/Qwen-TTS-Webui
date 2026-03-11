import numpy as np
import pytest
from backend.utils import AudioPostProcessor

def reference_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    if len(wav.shape) > 1:
        out = np.zeros_like(wav)
        for i in range(wav.shape[0]):
            out[i] = reference_apply_declick(wav[i], sr)
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

def test_declick_mono_identity():
    sr = 24000
    wav = np.random.randn(sr).astype(np.float32)

    out_ref = reference_apply_declick(wav, sr)
    out_opt = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_allclose(out_ref, out_opt, atol=1e-6)

def test_declick_stereo_identity():
    sr = 24000
    wav = np.random.randn(2, sr).astype(np.float32)

    out_ref = reference_apply_declick(wav, sr)
    out_opt = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_allclose(out_ref, out_opt, atol=1e-6)

def test_declick_remainder_identity():
    sr = 24000
    window = int(sr * 0.002)
    wav = np.random.randn(window * 2 + 10).astype(np.float32)

    out_ref = reference_apply_declick(wav, sr)
    out_opt = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_allclose(out_ref, out_opt, atol=1e-6)

def test_declick_identity_small():
    sr = 24000
    # Small audio shouldn't be touched if window >= len
    wav = np.random.randn(10).astype(np.float32)
    out = AudioPostProcessor.apply_declick(wav, sr)
    np.testing.assert_array_equal(wav, out)
