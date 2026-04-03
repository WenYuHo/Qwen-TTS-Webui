import numpy as np
import sys
import os

# Add src to path for imports
sys.path.append(os.path.abspath("src"))
from backend.utils import AudioPostProcessor

def original_apply_compressor(wav, sr, threshold_db=-20.0, ratio=4.0):
    """Original loop-based (recursive for stereo) implementation for parity checking."""
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
    duration = 1.0

    # Test Mono
    wav_mono = np.random.normal(0, 0.5, int(sr * duration)).astype(np.float32)
    out_orig_mono = original_apply_compressor(wav_mono, sr)
    out_new_mono = AudioPostProcessor.apply_compressor(wav_mono, sr)

    # Check parity
    np.testing.assert_allclose(out_orig_mono, out_new_mono, rtol=1e-5, atol=1e-5)
    print("Mono parity check passed!")

    # Test Stereo
    wav_stereo = np.random.normal(0, 0.5, (2, int(sr * duration))).astype(np.float32)
    out_orig_stereo = original_apply_compressor(wav_stereo, sr)
    out_new_stereo = AudioPostProcessor.apply_compressor(wav_stereo, sr)

    # Check parity
    np.testing.assert_allclose(out_orig_stereo, out_new_stereo, rtol=1e-5, atol=1e-5)
    print("Stereo parity check passed!")

if __name__ == "__main__":
    test_compressor_parity()
