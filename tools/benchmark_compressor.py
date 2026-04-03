import numpy as np
import time
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
        out = wav.copy()
        # threshold_linear / abs_wav[mask] is safe because abs_wav[mask] > threshold_linear > 0
        gain_active = (threshold_linear / abs_wav[mask]) ** exponent
        out[mask] *= gain_active
        return out
    except Exception as e:
        return wav

def benchmark_both(duration_sec=60, sr=24000, stereo=False):
    print(f"Benchmarking compressor on {duration_sec}s of {sr}Hz audio (stereo={stereo})...")

    # Generate random audio
    if stereo:
        n_samples = duration_sec * sr
        wav = np.random.normal(0, 0.5, (2, n_samples)).astype(np.float32)
    else:
        n_samples = duration_sec * sr
        wav = np.random.normal(0, 0.5, n_samples).astype(np.float32)

    # Measure original
    start_time = time.perf_counter()
    _ = original_apply_compressor(wav, sr)
    end_time = time.perf_counter()
    elapsed_orig = end_time - start_time
    print(f"Original execution time: {elapsed_orig*1000:.2f} ms")

    # Measure optimized
    start_time = time.perf_counter()
    _ = optimized_apply_compressor(wav, sr)
    end_time = time.perf_counter()
    elapsed_opt = end_time - start_time
    print(f"Optimized execution time: {elapsed_opt*1000:.2f} ms")

    speedup = elapsed_orig / elapsed_opt
    print(f"Speedup: {speedup:.2f}x")

if __name__ == "__main__":
    benchmark_both(stereo=False)
    benchmark_both(stereo=True)
