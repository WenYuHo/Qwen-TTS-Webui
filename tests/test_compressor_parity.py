import numpy as np
import pytest
import sys
import os

# Add src to path for imports
sys.path.append(os.path.abspath("src"))
from backend.utils import AudioPostProcessor

def original_apply_compressor(wav: np.ndarray, sr: int, threshold_db: float = -20.0, ratio: float = 4.0) -> np.ndarray:
    """Applies dynamic range compression (Original implementation)."""
    try:
        # Handle stereo
        if len(wav.shape) > 1:
            out = np.zeros_like(wav)
            for i in range(wav.shape[0]):
                out[i] = original_apply_compressor(wav[i], sr, threshold_db, ratio)
            return out

        # Convert to dB
        # Avoid log(0)
        abs_wav = np.abs(wav)
        db_wav = 20 * np.log10(abs_wav + 1e-10)

        # Gain reduction
        mask = db_wav > threshold_db
        if not np.any(mask):
            return wav

        reduction = (db_wav - threshold_db) * (1 - 1/ratio)
        gain_db = np.zeros_like(db_wav)
        gain_db[mask] = -reduction[mask]

        gain_linear = 10 ** (gain_db / 20.0)
        return wav * gain_linear
    except Exception:
        return wav

def test_compressor_parity():
    sr = 24000
    # Create some audio with samples above and below -20dB (approx 0.1)
    wav_mono = np.array([0.01, 0.2, 0.05, 0.5, -0.3, -0.02], dtype=np.float32)

    res_orig = original_apply_compressor(wav_mono, sr)
    res_new = AudioPostProcessor.apply_compressor(wav_mono, sr)

    assert np.allclose(res_orig, res_new, atol=1e-6)

    # Test Stereo
    wav_stereo = np.array([[0.2, 0.01, 0.5], [0.05, 0.3, 0.02]], dtype=np.float32)
    res_orig_stereo = original_apply_compressor(wav_stereo, sr)
    res_new_stereo = AudioPostProcessor.apply_compressor(wav_stereo, sr)

    assert np.allclose(res_orig_stereo, res_new_stereo, atol=1e-6)

if __name__ == "__main__":
    test_compressor_parity()
    print("Parity test passed!")
