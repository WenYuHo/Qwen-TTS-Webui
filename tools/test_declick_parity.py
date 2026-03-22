import numpy as np
import sys
import os

# Add src to path for imports
sys.path.append(os.path.abspath("src"))

def original_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """The original loop-based implementation for parity testing."""
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

def vectorized_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """The proposed vectorized implementation."""
    if len(wav.shape) > 1:
        out = np.zeros_like(wav)
        for i in range(wav.shape[0]):
            out[i] = vectorized_declick(wav[i], sr)
        return out

    window = int(sr * 0.002) # 2ms
    if window < 2 or len(wav) < window:
        return wav.copy()

    # 1. Reshape into chunks, handling the remainder separately
    n_chunks = len(wav) // window
    main_len = n_chunks * window
    chunks = wav[:main_len].reshape(n_chunks, window)
    remainder = wav[main_len:]

    # 2. Calculate RMS for each chunk
    # Use np.einsum for row-wise dot product (squared sum)
    rms = np.sqrt(np.einsum('ij,ij->i', chunks, chunks) / window) + 1e-6

    # 3. Identify spikes (10x local RMS)
    spikes = np.abs(chunks) > (rms[:, None] * 10)

    # 4. Prepare output
    out_main = chunks.copy()

    # 5. Clamp spikes
    if np.any(spikes):
        row_idx, col_idx = np.where(spikes)
        clamp_vals = rms[row_idx] * 3
        out_main[row_idx, col_idx] = np.sign(chunks[row_idx, col_idx]) * clamp_vals

    # 6. Handle remainder
    out_remainder = remainder.copy()
    if len(remainder) >= 2:
        rem_rms = np.sqrt(np.vdot(remainder, remainder) / len(remainder)) + 1e-6
        rem_spikes = np.abs(remainder) > (rem_rms * 10)
        if np.any(rem_spikes):
            out_remainder[rem_spikes] = np.sign(remainder[rem_spikes]) * rem_rms * 3

    return np.concatenate([out_main.ravel(), out_remainder])

def test_parity():
    sr = 24000
    test_cases = [
        # Small mono
        np.random.normal(0, 0.1, 1000).astype(np.float32),
        # Large mono (not perfectly divisible by window)
        np.random.normal(0, 0.1, 24000 * 2 + 50).astype(np.float32),
        # Stereo
        np.random.normal(0, 0.1, (2, 5000)).astype(np.float32),
    ]

    # Add spikes to all test cases
    for i in range(len(test_cases)):
        wav = test_cases[i]
        if len(wav.shape) > 1:
            indices = np.random.choice(wav.shape[1], 10)
            wav[0, indices] = 0.9
            wav[1, indices] = -0.9
        else:
            indices = np.random.choice(len(wav), 10)
            wav[indices] = 0.9
        test_cases[i] = wav

    for i, wav in enumerate(test_cases):
        print(f"Testing Case {i+1} (Shape: {wav.shape})...")
        res_orig = original_declick(wav, sr)
        res_vect = vectorized_declick(wav, sr)

        # Check identity
        np.testing.assert_allclose(res_orig, res_vect, rtol=1e-5, atol=1e-5)
        print(f"Case {i+1} PASSED")

if __name__ == "__main__":
    try:
        test_parity()
        print("\nAll parity tests PASSED! Vectorized implementation is mathematically identical.")
    except Exception as e:
        print(f"\nParity test FAILED: {e}")
        sys.exit(1)
