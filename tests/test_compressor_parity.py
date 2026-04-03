import numpy as np
import pytest
import sys
import os

# Add src to path for imports
sys.path.append(os.path.abspath("src"))
from backend.utils import AudioPostProcessor

def original_apply_compressor(wav: np.ndarray, sr: int, threshold_db: float = -20.0, ratio: float = 4.0) -> np.ndarray:
    """Original implementation of apply_compressor."""
    try:
        # Handle stereo
        if len(wav.shape) > 1:
            out = np.zeros_like(wav)
            for i in range(wav.shape[0]):
                out[i] = original_apply_compressor(wav[i], sr, threshold_db, ratio)
            return out

        # Convert to dB
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

def test_compressor_parity_mono():
    sr = 24000
    wav = np.random.normal(0, 0.5, sr).astype(np.float32)

    expected = original_apply_compressor(wav, sr)
    # Since we haven't changed the code yet, this should pass
    actual = AudioPostProcessor.apply_compressor(wav, sr)

    np.testing.assert_allclose(actual, expected, rtol=1e-5, atol=1e-5)

def test_compressor_parity_stereo():
    sr = 24000
    wav = np.random.normal(0, 0.5, (2, sr)).astype(np.float32)

    expected = original_apply_compressor(wav, sr)
    actual = AudioPostProcessor.apply_compressor(wav, sr)

    np.testing.assert_allclose(actual, expected, rtol=1e-5, atol=1e-5)

def test_compressor_no_spikes():
    sr = 24000
    wav = np.random.normal(0, 0.01, sr).astype(np.float32) # Very quiet, no compression

    expected = original_apply_compressor(wav, sr, threshold_db=-20.0)
    actual = AudioPostProcessor.apply_compressor(wav, sr, threshold_db=-20.0)

    np.testing.assert_allclose(actual, expected, rtol=1e-5, atol=1e-5)
    # Also verify no change if below threshold
    np.testing.assert_array_equal(actual, wav)
