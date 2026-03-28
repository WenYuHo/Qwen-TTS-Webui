
import numpy as np
import sys
import os

# Add src to path
sys.path.append(os.path.abspath("src"))

from backend.utils import AudioPostProcessor

def original_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """Simple heuristic de-clicker: clamps spikes > 10x local RMS."""
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

def vectorized_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """Vectorized version of the heuristic de-clicker."""
    try:
        if len(wav.shape) > 1:
            # Handle multi-channel
            return np.stack([vectorized_apply_declick(ch, sr) for ch in wav])

        window = int(sr * 0.002) # 2ms
        if window < 2 or len(wav) < 2:
            return wav

        out = wav.copy()
        n_samples = len(wav)
        n_chunks = n_samples // window

        if n_chunks > 0:
            main_len = n_chunks * window
            # Reshape into chunks
            chunks = wav[:main_len].reshape(n_chunks, window)

            # ⚡ Bolt: Use np.einsum for row-wise dot product (squared sum) to avoid O(N) temp array
            sq_sum = np.einsum('ij,ij->i', chunks, chunks)
            rms = np.sqrt(sq_sum / window) + 1e-6

            # Identify spikes: spikes is (n_chunks, window)
            # Broadcasting rms (n_chunks,) to (n_chunks, window)
            spikes = np.abs(chunks) > (rms[:, np.newaxis] * 10)

            if np.any(spikes):
                row_idx, col_idx = np.where(spikes)
                # Update out via view
                out_view = out[:main_len].reshape(n_chunks, window)
                out_view[row_idx, col_idx] = np.sign(out_view[row_idx, col_idx]) * rms[row_idx] * 3

        # Handle remainder
        remainder_start = n_chunks * window
        remainder_len = n_samples - remainder_start
        if remainder_len >= 2:
            chunk = wav[remainder_start:]
            local_rms = np.sqrt(np.mean(chunk**2)) + 1e-6
            spikes = np.abs(chunk) > (local_rms * 10)
            if np.any(spikes):
                sign = np.sign(chunk[spikes])
                out[remainder_start:][spikes] = sign * local_rms * 3

        return out
    except Exception as e:
        print(f"Error in vectorized_apply_declick: {e}")
        return wav

def test_parity():
    sr = 24000
    duration = 1.0 # 1s
    n_samples = int(sr * duration)

    # Test cases
    cases = [
        ("Random Noise", np.random.uniform(-0.1, 0.1, n_samples).astype(np.float32)),
        ("With Spikes", None),
        ("Stereo", None),
        ("Small Buffer", np.random.uniform(-0.1, 0.1, 10).astype(np.float32)),
        ("Remainder Buffer", np.random.uniform(-0.1, 0.1, 48 * 10 + 5).astype(np.float32))
    ]

    for name, wav in cases:
        if name == "With Spikes":
            wav = np.random.uniform(-0.1, 0.1, n_samples).astype(np.float32)
            spike_indices = np.random.choice(n_samples, 10, replace=False)
            wav[spike_indices] = np.random.uniform(0.5, 1.0, 10) * np.random.choice([-1, 1], 10)
        elif name == "Stereo":
            wav = np.random.uniform(-0.1, 0.1, (2, n_samples)).astype(np.float32)
            wav[0, 100] = 0.9
            wav[1, 200] = -0.9

        res_orig = original_apply_declick(wav, sr)
        res_vec = vectorized_apply_declick(wav, sr)

        diff = np.max(np.abs(res_orig - res_vec))
        print(f"Test {name}: Max diff = {diff}")
        assert diff < 1e-7, f"Parity failed for {name}"

if __name__ == "__main__":
    test_parity()
    print("Parity test passed!")
