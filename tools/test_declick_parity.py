import numpy as np
import sys
import os

def original_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """Original loop-based implementation."""
    try:
        if len(wav.shape) > 1:
            out = np.zeros_like(wav)
            for i in range(wav.shape[0]):
                out[i] = original_apply_declick(wav[i], sr)
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
    except Exception:
        return wav

def vectorized_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """Vectorized implementation to be tested."""
    try:
        if len(wav.shape) > 1:
            out = np.zeros_like(wav)
            for i in range(wav.shape[0]):
                out[i] = vectorized_apply_declick(wav[i], sr)
            return out

        window = int(sr * 0.002)
        if window < 2 or len(wav) < window:
            return wav.copy()

        # Handle exact chunks
        num_chunks = len(wav) // window
        main_wav = wav[:num_chunks * window]
        remainder = wav[num_chunks * window:]

        chunks = main_wav.reshape(num_chunks, window)

        # ⚡ Bolt: Use einsum for row-wise squared sum (faster than chunks**2.mean(axis=1))
        # This avoids a large intermediate array.
        sq_sum = np.einsum('ij,ij->i', chunks, chunks)
        rms = np.sqrt(sq_sum / window) + 1e-6

        # Identify spikes (broadcasting rms across chunks)
        thresholds = rms * 10
        spikes = np.abs(chunks) > thresholds[:, np.newaxis]

        if np.any(spikes):
            out_chunks = chunks.copy()
            # ⚡ Bolt: Vectorized clamping
            # We need the row indices for each spike to get the correct RMS
            row_idx, col_idx = np.where(spikes)
            clamp_vals = rms[row_idx] * 3
            out_chunks[row_idx, col_idx] = np.sign(chunks[row_idx, col_idx]) * clamp_vals
            out_main = out_chunks.flatten()
        else:
            out_main = main_wav.copy()

        # Handle remainder (usually very small, so serial is fine or just skip)
        if len(remainder) >= 2:
            out_remainder = original_apply_declick(remainder, sr)
            return np.concatenate([out_main, out_remainder])
        else:
            return np.concatenate([out_main, remainder])

    except Exception:
        return wav.copy()

def test_parity():
    sr = 24000
    # Test cases: Mono, Stereo, small, remainder
    test_lengths = [sr, sr + 10, sr // 10, 100]

    for length in test_lengths:
        print(f"Testing length: {length}")
        wav = np.random.uniform(-0.5, 0.5, length).astype(np.float32)
        # Add spikes
        wav[np.random.randint(0, length, 5)] *= 20

        out_orig = original_apply_declick(wav, sr)
        out_vec = vectorized_apply_declick(wav, sr)

        np.testing.assert_allclose(out_orig, out_vec, atol=1e-6, err_msg=f"Parity failed for length {length}")

    # Test Stereo
    print("Testing Stereo")
    wav_stereo = np.random.uniform(-0.5, 0.5, (2, sr)).astype(np.float32)
    wav_stereo[0, 100] = 5.0
    wav_stereo[1, 200] = -5.0

    out_orig = original_apply_declick(wav_stereo, sr)
    out_vec = vectorized_apply_declick(wav_stereo, sr)
    np.testing.assert_allclose(out_orig, out_vec, atol=1e-6, err_msg="Parity failed for Stereo")

    print("All parity tests passed!")

if __name__ == "__main__":
    test_parity()
