import numpy as np
import sys
import os

# Add src to path for imports
sys.path.append(os.path.abspath("src"))

def original_apply_compressor(wav: np.ndarray, sr: int, threshold_db: float = -20.0, ratio: float = 4.0) -> np.ndarray:
    """Original implementation."""
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
    except Exception as e:
        return wav

def optimized_apply_compressor(wav: np.ndarray, sr: int, threshold_db: float = -20.0, ratio: float = 4.0) -> np.ndarray:
    """Optimized implementation (matching original independent behavior)."""
    try:
        threshold_linear = 10 ** (threshold_db / 20.0)
        abs_wav = np.abs(wav)
        mask = abs_wav > threshold_linear

        if not np.any(mask):
            return wav

        exponent = 1.0 - (1.0 / ratio)
        # We can avoid allocating a full gain array if we use in-place multiplication on a copy
        out = wav.copy()
        # threshold_linear / abs_wav[mask] is safe because abs_wav[mask] > threshold_linear > 0
        gain_active = (threshold_linear / abs_wav[mask]) ** exponent
        out[mask] *= gain_active
        return out
    except Exception as e:
        print(f"Error: {e}")
        return wav

def test_parity():
    sr = 24000
    duration = 1.0
    wav = np.random.normal(0, 0.5, int(sr * duration)).astype(np.float32)

    out_orig = original_apply_compressor(wav, sr)
    out_opt = optimized_apply_compressor(wav, sr)

    diff = np.abs(out_orig - out_opt)
    max_diff = np.max(diff)
    print(f"Mono Parity Max Diff: {max_diff}")
    assert max_diff < 1e-6

    # Test Stereo (Independent as original)
    wav_stereo = np.random.normal(0, 0.5, (2, int(sr * duration))).astype(np.float32)
    out_orig_stereo = original_apply_compressor(wav_stereo, sr)
    out_opt_stereo = optimized_apply_compressor(wav_stereo, sr)

    diff_stereo = np.abs(out_orig_stereo - out_opt_stereo)
    max_diff_stereo = np.max(diff_stereo)
    print(f"Stereo Parity Max Diff: {max_diff_stereo}")
    assert max_diff_stereo < 1e-6

if __name__ == "__main__":
    test_parity()
