import numpy as np
import sys
import os

# Add src to path for imports
sys.path.append(os.path.abspath("src"))
from backend.utils import AudioPostProcessor

def original_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """Original loop-based de-clicker for parity testing."""
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
    """Proposed vectorized de-clicker."""
    try:
        if len(wav.shape) > 1:
            return np.stack([vectorized_apply_declick(ch, sr) for ch in wav])

        window = int(sr * 0.002)
        if window < 2 or len(wav) < window:
            return wav.copy()

        n_full_windows = len(wav) // window
        full_len = n_full_windows * window

        # Reshape into windows
        chunks = wav[:full_len].reshape(n_full_windows, window)

        # Vectorized RMS: sqrt(mean(chunk^2))
        # Use einsum for memory-efficient squared sum
        ms = np.einsum('ij,ij->i', chunks, chunks) / window
        rms = np.sqrt(ms) + 1e-6

        # Find spikes: abs(chunk) > (rms * 10)
        # rms needs to be broadcasted to (n_full_windows, window)
        spikes = np.abs(chunks) > (rms[:, None] * 10)

        out_chunks = chunks.copy()
        if np.any(spikes):
            # Clamp spikes to local RMS * 3
            # We need to broadcast rms correctly for the assignment
            # sign = np.sign(chunks[spikes])
            # out_chunks[spikes] = sign * (rms[:, None] * 3)[spikes]

            # Alternative: find where spikes are and apply
            row_idx, col_idx = np.where(spikes)
            out_chunks[row_idx, col_idx] = np.sign(chunks[row_idx, col_idx]) * rms[row_idx] * 3

        # Combine with remainder
        out = out_chunks.flatten()
        if len(wav) > full_len:
            remainder = wav[full_len:]
            if len(remainder) >= 2:
                rem_rms = np.sqrt(np.mean(remainder**2)) + 1e-6
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
    except Exception:
        return wav.copy()

def test_parity():
    sr = 24000
    durations = [0.1, 1.0, 5.0]

    for dur in durations:
        print(f"Testing parity for {dur}s...")
        n_samples = int(dur * sr)
        wav = np.random.normal(0, 0.1, n_samples).astype(np.float32)

        # Add some spikes
        spike_indices = np.random.choice(n_samples, int(n_samples * 0.01), replace=False)
        wav[spike_indices] = np.random.choice([-1.0, 1.0], len(spike_indices)) * 0.9

        orig_out = original_apply_declick(wav, sr)
        vect_out = vectorized_apply_declick(wav, sr)

        if np.allclose(orig_out, vect_out):
            print(f"PASS: {dur}s")
        else:
            diff = np.max(np.abs(orig_out - vect_out))
            print(f"FAIL: {dur}s (max diff: {diff})")
            # Debug first difference
            idx = np.where(~np.isclose(orig_out, vect_out))[0]
            if len(idx) > 0:
                print(f"First diff at {idx[0]}: orig={orig_out[idx[0]]}, vect={vect_out[idx[0]]}")

if __name__ == "__main__":
    test_parity()
