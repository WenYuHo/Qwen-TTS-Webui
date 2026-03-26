import numpy as np
import pytest
from backend.utils import AudioPostProcessor

def apply_declick_original(wav: np.ndarray, sr: int) -> np.ndarray:
    """Original loop-based de-clicker for parity testing."""
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
    """Vectorized heuristic de-clicker."""
    if len(wav.shape) > 1:
        return np.stack([apply_declick_vectorized(ch, sr) for ch in wav])

    window = int(sr * 0.002)  # 2ms
    if window < 2 or len(wav) < window:
        # Note: Original implementation skips processing for < window if window < 2
        # If window >= 2 but len(wav) < window, it also skips because of range(0, len(wav), window)
        # where the first chunk would be wav[0:window] which might be less than window.
        # Let's re-examine original:
        # for i in range(0, len(wav), window): chunk = wav[i:i+window]
        # if len(chunk) < 2: continue
        # So it processes the last chunk if it has at least 2 samples.
        pass

    out = wav.copy()
    n_chunks = len(wav) // window

    if n_chunks > 0:
        main_body = wav[:n_chunks * window].reshape(n_chunks, window)
        # ⚡ Bolt: Use np.einsum for row-wise squared sum to avoid large temporary array from main_body**2
        rms = np.sqrt(np.einsum('ij,ij->i', main_body, main_body) / window) + 1e-6
        spikes = np.abs(main_body) > (rms[:, None] * 10)

        if np.any(spikes):
            row_idx, _ = np.where(spikes)
            out_view = out[:n_chunks * window].reshape(n_chunks, window)
            out_view[spikes] = np.sign(main_body[spikes]) * rms[row_idx] * 3

    # Handle remainder (last partial chunk)
    remainder_start = n_chunks * window
    remainder = wav[remainder_start:]
    if len(remainder) >= 2:
        # np.vdot is efficient for RMS of a single vector
        rem_rms = np.sqrt(np.vdot(remainder, remainder) / len(remainder)) + 1e-6
        rem_spikes = np.abs(remainder) > (rem_rms * 10)
        if np.any(rem_spikes):
            out[remainder_start:][rem_spikes] = np.sign(remainder[rem_spikes]) * rem_rms * 3

    return out

@pytest.mark.parametrize("sr", [24000, 44100, 48000])
@pytest.mark.parametrize("duration", [0.1, 0.5, 1.0])
@pytest.mark.parametrize("channels", [1, 2])
def test_declick_parity(sr, duration, channels):
    n_samples = int(sr * duration)
    if channels == 1:
        wav = np.random.normal(0, 0.1, n_samples).astype(np.float32)
    else:
        wav = np.random.normal(0, 0.1, (channels, n_samples)).astype(np.float32)

    # Add some spikes
    if channels == 1:
        spike_indices = np.random.choice(n_samples, 20, replace=False)
        wav[spike_indices] = np.random.choice([-1.0, 1.0], 20) * 0.9
    else:
        for c in range(channels):
            spike_indices = np.random.choice(n_samples, 20, replace=False)
            wav[c, spike_indices] = np.random.choice([-1.0, 1.0], 20) * 0.9

    original = apply_declick_original(wav, sr)
    vectorized = apply_declick_vectorized(wav, sr)

    np.testing.assert_allclose(original, vectorized, atol=1e-6)

def test_declick_edge_cases():
    sr = 24000
    # Very short buffer
    wav_short = np.array([0.1, 0.9, 0.1], dtype=np.float32)
    assert np.array_equal(apply_declick_original(wav_short, sr), apply_declick_vectorized(wav_short, sr))

    # Empty buffer
    wav_empty = np.array([], dtype=np.float32)
    assert np.array_equal(apply_declick_original(wav_empty, sr), apply_declick_vectorized(wav_empty, sr))

    # No spikes
    wav_clean = np.linspace(0, 0.5, 1000).astype(np.float32)
    assert np.array_equal(apply_declick_original(wav_clean, sr), apply_declick_vectorized(wav_clean, sr))
