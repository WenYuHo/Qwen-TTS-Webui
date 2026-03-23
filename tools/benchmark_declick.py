import numpy as np
import time
from backend.utils import AudioPostProcessor

def apply_declick_vectorized(wav: np.ndarray, sr: int) -> np.ndarray:
    """Vectorized de-clicker: clamps spikes > 10x local RMS."""
    if len(wav.shape) > 1:
        out = np.zeros_like(wav)
        for i in range(wav.shape[0]):
            out[i] = apply_declick_vectorized(wav[i], sr)
        return out

    window = int(sr * 0.002) # 2ms
    if window < 2: return wav.copy()

    # Pad to make it divisible by window
    n = len(wav)
    remainder = n % window
    if remainder > 0:
        padding = window - remainder
        wav_padded = np.concatenate([wav, np.zeros(padding, dtype=wav.dtype)])
    else:
        wav_padded = wav

    # Reshape into chunks
    chunks = wav_padded.reshape(-1, window)

    # Calculate RMS for each chunk
    # np.einsum is very fast for row-wise dot products
    rms = np.sqrt(np.einsum('ij,ij->i', chunks, chunks) / window) + 1e-6

    # Find spikes: abs(chunk) > 10 * rms
    # rms needs to be broadcasted to match chunks shape
    spikes = np.abs(chunks) > (rms[:, np.newaxis] * 10)

    if np.any(spikes):
        # Create output copy
        out_chunks = chunks.copy()
        # Clamp spikes to local RMS * 3
        # We need to broadcast rms * 3 to match out_chunks
        clamp_vals = rms * 3

        # Applying the clamp only where spikes are true
        # sign * clamp_vals
        # This is the tricky part to do fully vectorized for only specific elements
        signs = np.sign(chunks[spikes])

        # We need the corresponding rms value for each spike
        # np.where(spikes) returns (row_indices, col_indices)
        row_idx, _ = np.where(spikes)
        out_chunks[spikes] = signs * clamp_vals[row_idx]

        out = out_chunks.flatten()
    else:
        out = wav_padded.flatten()

    # Trim back to original length
    return out[:n]

def benchmark_declick():
    sr = 24000
    # 60 seconds of audio
    duration = 60
    wav = np.random.randn(sr * duration).astype(np.float32)

    # Add some spikes
    for _ in range(100):
        idx = np.random.randint(0, len(wav))
        wav[idx] *= 50

    print(f"Benchmarking 60s of {sr}Hz audio...")

    # Original
    start_time = time.time()
    res1 = AudioPostProcessor.apply_declick(wav, sr)
    end_time = time.time()
    orig_time = end_time - start_time
    print(f"Original de-click took: {orig_time:.4f}s")

    # Vectorized
    start_time = time.time()
    res2 = apply_declick_vectorized(wav, sr)
    end_time = time.time()
    vect_time = end_time - start_time
    print(f"Vectorized de-click took: {vect_time:.4f}s")

    print(f"Speedup: {orig_time / vect_time:.2f}x")

    # Verify parity
    np.testing.assert_array_almost_equal(res1, res2)
    print("Verification PASSED: Results are identical.")

if __name__ == "__main__":
    benchmark_declick()
