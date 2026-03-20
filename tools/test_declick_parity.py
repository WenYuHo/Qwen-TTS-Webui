import numpy as np
import sys
import os

# Original implementation for parity testing
def apply_declick_original(wav, sr):
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

# Proposed vectorized implementation
def apply_declick_vectorized(wav, sr):
    if len(wav.shape) > 1:
        # Recursive for multi-channel
        return np.stack([apply_declick_vectorized(wav[i], sr) for i in range(wav.shape[0])])

    out = wav.copy()
    window = int(sr * 0.002)
    if window < 2: return wav

    n_full_windows = len(wav) // window
    if n_full_windows > 0:
        full_len = n_full_windows * window
        chunks = wav[:full_len].reshape(n_full_windows, window)
        # Vectorized RMS calculation
        sq_sums = np.einsum('ij,ij->i', chunks, chunks)
        rms = np.sqrt(sq_sums / window) + 1e-6

        # Spike detection
        spikes = np.abs(chunks) > (rms[:, None] * 10)

        if np.any(spikes):
            out_chunks = out[:full_len].reshape(n_full_windows, window)
            row_idx, _ = np.where(spikes)
            out_chunks[spikes] = np.sign(chunks[spikes]) * rms[row_idx] * 3

    # Remainder handling
    remainder_start = n_full_windows * window
    if len(wav) - remainder_start >= 2:
        chunk = wav[remainder_start:]
        local_rms = np.sqrt(np.vdot(chunk, chunk) / len(chunk)) + 1e-6
        spikes = np.abs(chunk) > (local_rms * 10)
        if np.any(spikes):
            out[remainder_start:][spikes] = np.sign(chunk[spikes]) * local_rms * 3

    return out

def test_parity():
    sr = 24000
    # Test with random audio + spikes
    n_samples = sr * 2 # 2 seconds
    wav = np.random.normal(0, 0.1, n_samples).astype(np.float32)

    # Add some spikes
    spike_indices = np.random.choice(n_samples, 50, replace=False)
    wav[spike_indices] = np.random.choice([-1.0, 1.0], 50) * 0.9

    orig = apply_declick_original(wav, sr)
    vect = apply_declick_vectorized(wav, sr)

    diff = np.abs(orig - vect)
    max_diff = np.max(diff)
    print(f"Max difference: {max_diff}")

    if max_diff < 1e-6:
        print("✅ Parity check passed!")
    else:
        print("❌ Parity check failed!")
        sys.exit(1)

if __name__ == "__main__":
    test_parity()
