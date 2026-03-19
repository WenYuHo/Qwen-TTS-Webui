import numpy as np
import sys
import os

# Add src to path
sys.path.append(os.path.abspath("src"))

from backend.utils import AudioPostProcessor

def original_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """Original loop-based implementation for reference."""
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

def vectorized_declick_draft(wav: np.ndarray, sr: int) -> np.ndarray:
    """Proposed vectorized implementation."""
    if len(wav.shape) > 1:
        out = np.zeros_like(wav)
        for i in range(wav.shape[0]):
            out[i] = vectorized_declick_draft(wav[i], sr)
        return out

    window = int(sr * 0.002)
    if window < 2 or len(wav) < window:
        return wav.copy()

    # Calculate how many full windows we have
    n_windows = len(wav) // window
    limit = n_windows * window

    # Reshape to (n_windows, window)
    chunks = wav[:limit].reshape(n_windows, window)

    # Vectorized RMS per chunk: sqrt(mean(chunk**2))
    # Using einsum for speed and memory efficiency
    sq_sums = np.einsum('ij,ij->i', chunks, chunks)
    rms = np.sqrt(sq_sums / window) + 1e-6

    # Identify spikes: abs(chunk) > 10 * local_rms
    # Broadcoast rms to (n_windows, window)
    spikes = np.abs(chunks) > (rms[:, np.newaxis] * 10)

    # Create output copy
    out = wav.copy()
    out_chunks = out[:limit].reshape(n_windows, window)

    if np.any(spikes):
        # Clamp spikes to local RMS * 3
        # We need the sign and the corresponding RMS for each spike
        row_idx, col_idx = np.where(spikes)
        out_chunks[row_idx, col_idx] = np.sign(chunks[row_idx, col_idx]) * rms[row_idx] * 3

    # Handle remainder
    remainder = wav[limit:]
    if len(remainder) >= 2:
        rem_rms = np.sqrt(np.mean(remainder**2)) + 1e-6
        rem_spikes = np.abs(remainder) > (rem_rms * 10)
        if np.any(rem_spikes):
            out[limit:][rem_spikes] = np.sign(remainder[rem_spikes]) * rem_rms * 3

    return out

def test_parity():
    sr = 24000
    # Test with different lengths, including remainders
    lengths = [sr, sr + 1, sr + 47, sr + 48, sr * 2 + 10]

    for length in lengths:
        print(f"Testing parity for length {length}...")
        wav = np.random.randn(length).astype(np.float32) * 0.1
        # Add some spikes
        for _ in range(10):
            idx = np.random.randint(0, length)
            wav[idx] *= 20

        expected = original_declick(wav, sr)
        actual = vectorized_declick_draft(wav, sr)

        # Check identity
        if not np.allclose(expected, actual, atol=1e-7):
            diff_idx = np.where(~np.isclose(expected, actual))[0]
            print(f"FAILURE: Parity check failed for length {length}")
            print(f"First 5 differences at indices: {diff_idx[:5]}")
            print(f"Expected: {expected[diff_idx[:5]]}")
            print(f"Actual:   {actual[diff_idx[:5]]}")
            sys.exit(1)

    print("SUCCESS: Parity check passed for all lengths!")

if __name__ == "__main__":
    test_parity()
