import numpy as np
import time
import sys
import os

# Add src to path for imports
sys.path.append(os.path.abspath("src"))
from backend.utils import AudioPostProcessor

def original_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """Original loop-based implementation for parity checking."""
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

def vectorized_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """Vectorized implementation to be tested."""
    if len(wav.shape) > 1:
        return np.stack([vectorized_declick(ch, sr) for ch in wav])

    window = int(sr * 0.002)
    if window < 2 or len(wav) < window:
        return wav.copy()

    n_full_chunks = len(wav) // window
    full_len = n_full_chunks * window

    chunks = wav[:full_len].reshape(n_full_chunks, window)

    # Use einsum for row-wise squared sum to avoid large temp arrays
    # rms = sqrt(sum(x^2) / N)
    sq_sum = np.einsum('ij,ij->i', chunks, chunks)
    rms = np.sqrt(sq_sum / window) + 1e-6

    # Identify spikes: abs(x) > 10 * local_rms
    # spikes is a boolean mask of shape (n_chunks, window)
    spikes = np.abs(chunks) > (rms[:, np.newaxis] * 10)

    if np.any(spikes):
        # We need a copy because we'll modify it
        out_chunks = chunks.copy()

        # Get indices of spikes
        row_idx, col_idx = np.where(spikes)

        # Clamp: sign(x) * 3 * local_rms
        out_chunks[spikes] = np.sign(chunks[spikes]) * (rms[row_idx] * 3)

        out = out_chunks.flatten()
    else:
        out = wav[:full_len].copy()

    # Handle remainder
    if len(wav) > full_len:
        remainder = wav[full_len:]
        if len(remainder) >= 2:
            rem_rms = np.sqrt(np.vdot(remainder, remainder) / len(remainder)) + 1e-6
            rem_spikes = np.abs(remainder) > (rem_rms * 10)
            if np.any(rem_spikes):
                rem_out = remainder.copy()
                rem_out[rem_spikes] = np.sign(remainder[rem_spikes]) * rem_rms * 3
                out = np.concatenate([out, rem_out])
            else:
                out = np.concatenate([out, remainder])
        else:
            out = np.concatenate([out, remainder])

    return out

def test_parity():
    sr = 24000
    duration = 5 # 5 seconds for parity test
    n_samples = duration * sr
    wav = np.random.normal(0, 0.1, n_samples).astype(np.float32)

    # Add spikes
    spike_indices = np.random.choice(n_samples, 100, replace=False)
    wav[spike_indices] = np.random.choice([-1.0, 1.0], 100) * 0.9

    orig_out = original_declick(wav, sr)
    vec_out = vectorized_declick(wav, sr)

    # Check if they are identical
    diff = np.abs(orig_out - vec_out)
    max_diff = np.max(diff)
    print(f"Max difference: {max_diff}")

    if max_diff < 1e-6:
        print("✅ Parity test passed!")
    else:
        print("❌ Parity test failed!")
        # Find where it fails
        fail_idx = np.where(diff > 1e-6)[0]
        print(f"Fails at indices: {fail_idx[:10]}")

if __name__ == "__main__":
    test_parity()
