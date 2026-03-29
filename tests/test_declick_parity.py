import numpy as np
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from backend.utils import AudioPostProcessor

def original_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """Original implementation with Python loop."""
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
    except Exception as e:
        return wav

def optimized_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """Optimized implementation with NumPy vectorization."""
    try:
        if len(wav.shape) > 1:
            # ⚡ Bolt: Vectorized multi-channel processing
            return np.stack([optimized_apply_declick(ch, sr) for ch in wav])

        n_samples = len(wav)
        window = int(sr * 0.002) # 2ms
        if window < 2 or n_samples < 2: return wav

        if n_samples < window:
            # Handle very short buffers that were skipped in original loop
            # But the original loop would still calculate RMS for a short chunk if it entered the loop.
            # Actually, if 0 < len(wav) < window, the original loop runs once for i=0.
            # Let's adjust optimized to match.
            n_chunks = 0
            out = wav.copy()
        else:
            n_chunks = n_samples // window
            main_part = wav[:n_chunks * window].reshape(n_chunks, window)

            # ⚡ Bolt: Use np.einsum for row-wise dot product (squared sum) to avoid large temporary array
            rms = np.sqrt(np.einsum('ij,ij->i', main_part, main_part) / window) + 1e-6

            # Identify spikes
            spikes = np.abs(main_part) > (rms[:, None] * 10)

            out_main = main_part.copy()
            if np.any(spikes):
                row_idx, _ = np.where(spikes)
                # ⚡ Bolt: Vectorized clamping
                out_main[spikes] = np.sign(main_part[spikes]) * rms[row_idx] * 3

            out = np.concatenate([out_main.ravel(), wav[n_chunks * window:]])

        # Handle remainder (including case where n_samples < window)
        remainder_idx = n_chunks * window
        if n_samples - remainder_idx >= 2:
            remainder = wav[remainder_idx:]
            rem_rms = np.sqrt(np.vdot(remainder, remainder) / len(remainder)) + 1e-6
            rem_spikes = np.abs(remainder) > (rem_rms * 10)
            if np.any(rem_spikes):
                out[remainder_idx:][rem_spikes] = np.sign(remainder[rem_spikes]) * rem_rms * 3

        return out
    except Exception as e:
        return wav

def test_parity():
    sr = 48000

    test_cases = [
        ("Mono Standard", np.random.randn(sr).astype(np.float32)),
        ("Stereo Standard", np.random.randn(2, sr).astype(np.float32)),
        ("Short Buffer", np.random.randn(int(sr * 0.001)).astype(np.float32)),
        ("Empty Buffer", np.array([], dtype=np.float32)),
        ("Spiky Mono", np.zeros(sr, dtype=np.float32)),
        ("Remainder Spike", np.zeros(sr + 5, dtype=np.float32)),
    ]

    # Add spikes to Spiky cases
    test_cases[4][1][sr//2] = 100.0
    test_cases[5][1][sr + 2] = 100.0

    for name, wav in test_cases:
        print(f"Testing {name}...")
        res_orig = original_apply_declick(wav, sr)
        res_opt = optimized_apply_declick(wav, sr)

        try:
            np.testing.assert_allclose(res_orig, res_opt, atol=1e-6)
            print(f"  {name}: PASSED")
        except AssertionError as e:
            print(f"  {name}: FAILED")
            print(e)
            sys.exit(1)

if __name__ == "__main__":
    test_parity()
