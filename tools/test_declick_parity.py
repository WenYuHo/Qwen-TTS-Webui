import numpy as np
import sys
import os

# Original loop-based implementation for parity testing
def apply_declick_loop(wav: np.ndarray, sr: int) -> np.ndarray:
    if len(wav.shape) > 1:
        out = np.zeros_like(wav)
        for i in range(wav.shape[0]):
            out[i] = apply_declick_loop(wav[i], sr)
        return out

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

# New vectorized implementation
def apply_declick_vectorized(wav: np.ndarray, sr: int) -> np.ndarray:
    if len(wav.shape) > 1:
        # Multi-channel handling
        out = np.empty_like(wav)
        for i in range(wav.shape[0]):
            out[i] = apply_declick_vectorized(wav[i], sr)
        return out

    window = int(sr * 0.002)
    if window < 2 or len(wav) < 2:
        return wav.copy()

    n_chunks = len(wav) // window
    main_len = n_chunks * window

    if n_chunks > 0:
        main_part = wav[:main_len].reshape(n_chunks, window)

        # Vectorized RMS calculation using einsum to avoid O(N) temporary squared array
        sq_sums = np.einsum('ij,ij->i', main_part, main_part)
        rms = np.sqrt(sq_sums / window) + 1e-6

        # Detection: abs(x) > 10 * local_rms
        # rms[:, None] broadcasts (n_chunks,) to (n_chunks, window)
        spikes = np.abs(main_part) > (rms[:, np.newaxis] * 10)

        if np.any(spikes):
            out_main = main_part.copy()
            row_idx, _ = np.where(spikes)
            # Clamp: sign(x) * local_rms * 3
            out_main[spikes] = (np.sign(out_main[spikes]) * rms[row_idx] * 3).astype(out_main.dtype)
            out_main = out_main.ravel()
        else:
            out_main = wav[:main_len].copy()
    else:
        out_main = np.array([], dtype=wav.dtype)

    # Handle remainder
    remainder = wav[main_len:]
    if len(remainder) >= 2:
        rem_rms = np.sqrt(np.vdot(remainder, remainder) / len(remainder)) + 1e-6
        rem_spikes = np.abs(remainder) > (rem_rms * 10)
        if np.any(rem_spikes):
            out_rem = remainder.copy()
            out_rem[rem_spikes] = np.sign(remainder[rem_spikes]) * rem_rms * 3
        else:
            out_rem = remainder.copy()
    else:
        out_rem = remainder.copy()

    return np.concatenate([out_main, out_rem])

def test_parity():
    sr = 24000

    test_cases = [
        ("Small mono", np.random.uniform(-0.1, 0.1, 100)),
        ("Exact window multiple", np.random.uniform(-0.1, 0.1, 48 * 10)), # window=48 at 24k
        ("With remainder", np.random.uniform(-0.1, 0.1, 48 * 10 + 10)),
        ("Stereo", np.random.uniform(-0.1, 0.1, (2, 1000))),
        ("Empty", np.array([], dtype=np.float32)),
        ("Single sample", np.array([0.5], dtype=np.float32)),
    ]

    for name, wav in test_cases:
        wav = wav.astype(np.float32)
        # Inject some spikes to trigger clamping
        if wav.size > 10:
            if len(wav.shape) == 1:
                wav[np.random.choice(len(wav), 5)] *= 50
            else:
                wav[0, np.random.choice(wav.shape[1], 5)] *= 50
                wav[1, np.random.choice(wav.shape[1], 5)] *= 50

        loop_out = apply_declick_loop(wav, sr)
        vec_out = apply_declick_vectorized(wav, sr)

        try:
            np.testing.assert_allclose(loop_out, vec_out, rtol=1e-5, atol=1e-5)
            print(f"PASS: {name}")
        except AssertionError as e:
            print(f"FAIL: {name}")
            print(e)
            sys.exit(1)

if __name__ == "__main__":
    test_parity()
