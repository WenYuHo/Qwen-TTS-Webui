import numpy as np
import pytest

def apply_declick_loop(wav: np.ndarray, sr: int) -> np.ndarray:
    """Original loop-based de-clicker for parity testing."""
    if len(wav.shape) > 1:
        out = np.zeros_like(wav)
        for i in range(wav.shape[0]):
            out[i] = apply_declick_loop(wav[i], sr)
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
    """Proposed vectorized de-clicker."""
    if len(wav.shape) > 1:
        return np.stack([apply_declick_vectorized(ch, sr) for ch in wav])

    window = int(sr * 0.002) # 2ms
    if window < 2 or len(wav) < window:
        return wav.copy()

    n_full_chunks = len(wav) // window
    full_part_len = n_full_chunks * window

    # Reshape into chunks: (n_chunks, window)
    chunks = wav[:full_part_len].reshape(n_full_chunks, window)

    # Calculate RMS for each chunk
    # ⚡ Bolt: Use einsum for squared sum to avoid O(N) allocation for chunks**2
    rms = np.sqrt(np.einsum('ij,ij->i', chunks, chunks) / window) + 1e-6

    # Identify spikes: (n_chunks, window)
    # Broadcasting rms: (n_chunks, 1)
    spikes = np.abs(chunks) > (rms[:, None] * 10)

    out = wav.copy()
    if np.any(spikes):
        # ⚡ Bolt: Use boolean indexing for selective clamping
        out_full = out[:full_part_len].reshape(n_full_chunks, window)
        # We need to broadcast rms back to (n_chunks, window) for the spikes mask
        rms_expanded = np.broadcast_to(rms[:, None], (n_full_chunks, window))

        # Apply clamping
        out_full[spikes] = np.sign(out_full[spikes]) * rms_expanded[spikes] * 3

    # Handle remainder
    if full_part_len < len(wav):
        remainder = wav[full_part_len:]
        if len(remainder) >= 2:
            rem_rms = np.sqrt(np.vdot(remainder, remainder) / len(remainder)) + 1e-6
            rem_spikes = np.abs(remainder) > (rem_rms * 10)
            if np.any(rem_spikes):
                out[full_part_len:][rem_spikes] = np.sign(remainder[rem_spikes]) * rem_rms * 3

    return out

@pytest.mark.parametrize("sr", [16000, 24000, 44100])
@pytest.mark.parametrize("channels", [1, 2])
def test_declick_parity(sr, channels):
    duration = 0.5
    n_samples = int(sr * duration)
    if channels == 1:
        wav = np.random.normal(0, 0.1, n_samples).astype(np.float32)
    else:
        wav = np.random.normal(0, 0.1, (channels, n_samples)).astype(np.float32)

    # Add some spikes
    if channels == 1:
        wav[np.random.randint(0, n_samples, 50)] = 0.9
    else:
        for c in range(channels):
            wav[c, np.random.randint(0, n_samples, 50)] = 0.9

    out_loop = apply_declick_loop(wav, sr)
    out_vec = apply_declick_vectorized(wav, sr)

    assert np.allclose(out_loop, out_vec, atol=1e-7)

def test_small_buffer():
    sr = 24000
    wav = np.array([0.1, 0.9, 0.1], dtype=np.float32) # Very small
    out_loop = apply_declick_loop(wav, sr)
    out_vec = apply_declick_vectorized(wav, sr)
    assert np.allclose(out_loop, out_vec)

def test_no_spikes():
    sr = 24000
    wav = np.zeros(1000, dtype=np.float32)
    out_loop = apply_declick_loop(wav, sr)
    out_vec = apply_declick_vectorized(wav, sr)
    assert np.allclose(out_loop, out_vec)
