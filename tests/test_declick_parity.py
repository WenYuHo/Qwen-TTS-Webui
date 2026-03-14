import numpy as np
import pytest
from backend.utils import AudioPostProcessor

def original_declick(wav, sr):
    try:
        if len(wav.shape) > 1:
            out = np.zeros_like(wav)
            for i in range(wav.shape[0]):
                out[i] = original_declick(wav[i], sr)
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
    except Exception:
        return wav

def test_declick_parity_random():
    sr = 24000
    # Use a larger buffer and some extreme values to potentially trigger it
    wav = np.random.uniform(-1.0, 1.0, sr * 2).astype(np.float32)

    out_orig = original_declick(wav, sr)
    out_vec = AudioPostProcessor.apply_declick(wav, sr)

    assert np.allclose(out_orig, out_vec)

def test_declick_stereo_parity():
    sr = 24000
    wav = np.random.uniform(-1.0, 1.0, (2, sr * 1)).astype(np.float32)

    out_orig = original_declick(wav, sr)
    out_vec = AudioPostProcessor.apply_declick(wav, sr)

    assert np.allclose(out_orig, out_vec)

def test_declick_remainder():
    sr = 24000
    # Length that is not a multiple of 48
    wav = np.random.uniform(-1.0, 1.0, 100).astype(np.float32)

    out_orig = original_declick(wav, sr)
    out_vec = AudioPostProcessor.apply_declick(wav, sr)

    assert np.allclose(out_orig, out_vec)
