import numpy as np
import sys
import os

# Add src to path for imports
sys.path.append(os.path.abspath("src"))

def old_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """Original loop-based implementation."""
    if len(wav.shape) > 1:
        out = np.zeros_like(wav)
        for i in range(wav.shape[0]):
            out[i] = old_apply_declick(wav[i], sr)
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

def new_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """Proposed vectorized implementation."""
    try:
        if len(wav.shape) > 1:
            # Vectorized multi-channel handling is harder for 10x local RMS if channels are treated separately
            # so we keep the recursive call but ensure the inner function is fast.
            out = np.zeros_like(wav)
            for i in range(wav.shape[0]):
                out[i] = new_apply_declick(wav[i], sr)
            return out

        window = int(sr * 0.002) # 2ms
        if window < 2 or len(wav) < 2:
            return wav.copy()

        n_full_chunks = len(wav) // window
        remainder_len = len(wav) % window

        # Initialize output
        out = wav.copy()

        if n_full_chunks > 0:
            full_part = wav[:n_full_chunks * window]
            chunks = full_part.reshape(n_full_chunks, window)

            # ⚡ Bolt: Use einsum for memory-efficient row-wise squared sum (avoid chunks**2)
            # local_rms shape: (n_full_chunks,)
            rms = np.sqrt(np.einsum('ij,ij->i', chunks, chunks) / window) + 1e-6

            # Threshold detection: (n_full_chunks, window)
            thresholds = rms[:, np.newaxis] * 10
            spikes = np.abs(chunks) > thresholds

            if np.any(spikes):
                # Clamp values: (n_full_chunks,)
                clamp_vals = rms * 3

                # Get indices where spikes occur to map clamp_vals back to 2D shape
                row_idx, _ = np.where(spikes)

                # Reshape for assignment
                out_full = out[:n_full_chunks * window].reshape(n_full_chunks, window)
                out_full[spikes] = np.sign(chunks[spikes]) * clamp_vals[row_idx]
                out[:n_full_chunks * window] = out_full.ravel()

        # Handle remainder if it's at least 2 samples (matching original logic)
        if remainder_len >= 2:
            remainder = wav[-remainder_len:]
            rem_rms = np.sqrt(np.mean(remainder**2)) + 1e-6
            rem_spikes = np.abs(remainder) > (rem_rms * 10)
            if np.any(rem_spikes):
                out[-remainder_len:][rem_spikes] = np.sign(remainder[rem_spikes]) * rem_rms * 3

        return out
    except Exception as e:
        print(f"De-click failed: {e}")
        return wav.copy()

def test_parity():
    test_cases = [
        ("Mono Small", np.random.uniform(-0.1, 0.1, 100), 24000),
        ("Mono Medium", np.random.uniform(-0.1, 0.1, 10000), 24000),
        ("Mono with Spikes", None, 24000),
        ("Stereo", np.random.uniform(-0.1, 0.1, (2, 5000)), 24000),
        ("Exact Multiple", np.random.uniform(-0.1, 0.1, 48 * 10), 24000), # 24000 * 0.002 = 48
        ("Tiny", np.random.uniform(-0.1, 0.1, 1), 24000),
        ("Empty", np.array([], dtype=np.float32), 24000),
    ]

    for name, wav, sr in test_cases:
        if name == "Mono with Spikes":
            wav = np.random.uniform(-0.1, 0.1, 5000).astype(np.float32)
            wav[100] = 0.9
            wav[1000] = -0.8
            wav[2500:2505] = 0.95

        old_out = old_apply_declick(wav, sr)
        new_out = new_apply_declick(wav, sr)

        # Check identity
        try:
            np.testing.assert_allclose(old_out, new_out, rtol=1e-5, atol=1e-8)
            print(f"✅ {name}: PASSED")
        except AssertionError as e:
            print(f"❌ {name}: FAILED")
            # print(e)

if __name__ == "__main__":
    test_parity()
