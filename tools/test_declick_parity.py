import numpy as np
import sys
import os

# Add src to path for imports
sys.path.append(os.path.abspath("src"))

def apply_declick_original(wav: np.ndarray, sr: int) -> np.ndarray:
    """Original implementation from src/backend/utils/__init__.py"""
    if len(wav.shape) > 1:
        out = np.zeros_like(wav)
        for i in range(wav.shape[0]):
            out[i] = apply_declick_original(wav[i], sr)
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

def apply_declick_vectorized(wav: np.ndarray, sr: int) -> np.ndarray:
    """Proposed vectorized implementation"""
    if len(wav.shape) > 1:
        # Multi-channel handling
        return np.stack([apply_declick_vectorized(ch, sr) for ch in wav])

    window = int(sr * 0.002)
    if window < 2 or len(wav) < window:
        return wav.copy()

    n_full = (len(wav) // window) * window
    main_wav = wav[:n_full]
    remainder = wav[n_full:]

    chunks = main_wav.reshape(-1, window).copy()

    # Vectorized RMS calculation
    # sq_sum[i] = sum(chunks[i, :]**2)
    sq_sum = np.einsum('ij,ij->i', chunks, chunks)
    rms = np.sqrt(sq_sum / window) + 1e-6

    # Identify spikes across all chunks
    thresholds = rms * 10
    spikes = np.abs(chunks) > thresholds[:, None]

    if np.any(spikes):
        row_idx, col_idx = np.where(spikes)
        chunks[row_idx, col_idx] = np.sign(chunks[row_idx, col_idx]) * rms[row_idx] * 3

    out = chunks.ravel()

    # Handle remainder
    if len(remainder) >= 2:
        rem_rms = np.sqrt(np.vdot(remainder, remainder) / len(remainder)) + 1e-6
        rem_spikes = np.abs(remainder) > (rem_rms * 10)
        if np.any(rem_spikes):
            remainder_out = remainder.copy()
            remainder_out[rem_spikes] = np.sign(remainder[rem_spikes]) * rem_rms * 3
            out = np.concatenate([out, remainder_out])
        else:
            out = np.concatenate([out, remainder])
    else:
        out = np.concatenate([out, remainder])

    return out

def test_parity():
    sr = 24000
    durations = [0.1, 1.0, 2.3, 5.0]

    for dur in durations:
        print(f"Testing parity for {dur}s duration...")
        n_samples = int(dur * sr)
        wav = np.random.normal(0, 0.1, n_samples).astype(np.float32)

        # Add some spikes
        n_spikes = int(dur * 10)
        spike_indices = np.random.choice(n_samples, n_spikes, replace=False)
        wav[spike_indices] = np.random.choice([-1.0, 1.0], n_spikes) * 0.9

        out_orig = apply_declick_original(wav, sr)
        out_vect = apply_declick_vectorized(wav, sr)

        # Check if identical
        if np.allclose(out_orig, out_vect, atol=1e-7):
            print(f"  PASS: {dur}s")
        else:
            diff = np.max(np.abs(out_orig - out_vect))
            print(f"  FAIL: {dur}s (max diff: {diff})")
            # Debug first difference
            idx = np.where(~np.isclose(out_orig, out_vect))[0]
            if len(idx) > 0:
                i = idx[0]
                print(f"    First diff at index {i}: orig={out_orig[i]}, vect={out_vect[i]}")

    # Test Stereo
    print("Testing parity for Stereo...")
    wav_stereo = np.random.normal(0, 0.1, (2, 24000)).astype(np.float32)
    wav_stereo[0, 100] = 0.9
    wav_stereo[1, 200] = -0.9

    out_orig = apply_declick_original(wav_stereo, sr)
    out_vect = apply_declick_vectorized(wav_stereo, sr)

    if np.allclose(out_orig, out_vect, atol=1e-7):
        print("  PASS: Stereo")
    else:
        print("  FAIL: Stereo")

if __name__ == "__main__":
    test_parity()
