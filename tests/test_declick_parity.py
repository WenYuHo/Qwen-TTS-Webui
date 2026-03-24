import numpy as np
import pytest

def original_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """Original loop-based de-clicker for parity testing."""
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

def vectorized_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """Vectorized de-clicker for parity testing."""
    if len(wav.shape) > 1:
        out = np.zeros_like(wav)
        for i in range(wav.shape[0]):
            out[i] = vectorized_apply_declick(wav[i], sr)
        return out

    window = int(sr * 0.002) # 2ms
    if window < 2 or len(wav) < window:
        return wav.copy()

    # 1. Prepare chunks (vectorized)
    n_chunks = len(wav) // window
    main_part = wav[:n_chunks * window]
    remainder = wav[n_chunks * window:]

    chunks = main_part.reshape(n_chunks, window)

    # 2. Calculate RMS per chunk (vectorized)
    # np.einsum('ij,ij->i', chunks, chunks) is a fast way to get row-wise sum of squares
    rms = np.sqrt(np.einsum('ij,ij->i', chunks, chunks) / window) + 1e-6

    # 3. Identify and clamp spikes (vectorized)
    # Expand rms to match chunks shape for comparison
    thresholds = rms[:, np.newaxis] * 10
    spikes = np.abs(chunks) > thresholds

    if np.any(spikes):
        out_chunks = chunks.copy()
        # Clamp values: 3x local RMS with original sign
        clamp_vals = rms[:, np.newaxis] * 3
        # Apply clamping only where spikes are detected
        out_chunks[spikes] = np.sign(chunks[spikes]) * clamp_vals[np.where(spikes)[0]]
        out_main = out_chunks.flatten()
    else:
        out_main = main_part.copy()

    # 4. Handle remainder (if any)
    if len(remainder) >= 2:
        out_rem = remainder.copy()
        rem_rms = np.sqrt(np.vdot(remainder, remainder) / len(remainder)) + 1e-6
        rem_spikes = np.abs(remainder) > (rem_rms * 10)
        if np.any(rem_spikes):
            out_rem[rem_spikes] = np.sign(remainder[rem_spikes]) * rem_rms * 3
        return np.concatenate([out_main, out_rem])
    else:
        return np.concatenate([out_main, remainder])

@pytest.mark.parametrize("sr", [24000, 44100, 48000])
@pytest.mark.parametrize("is_stereo", [False, True])
def test_declick_parity(sr, is_stereo):
    duration_sec = 0.1 # Small buffer for testing
    n_samples = int(duration_sec * sr)

    if is_stereo:
        wav = np.random.normal(0, 0.1, (2, n_samples)).astype(np.float32)
        # Add some spikes
        wav[0, n_samples // 10] = 0.9
        wav[1, n_samples // 5] = -0.8
    else:
        wav = np.random.normal(0, 0.1, n_samples).astype(np.float32)
        # Add some spikes
        wav[n_samples // 10] = 0.9
        wav[n_samples // 5] = -0.8

    out_original = original_apply_declick(wav, sr)
    out_vectorized = vectorized_apply_declick(wav, sr)

    # Check shape
    assert out_original.shape == out_vectorized.shape
    # Check identity
    np.testing.assert_allclose(out_original, out_vectorized, rtol=1e-5, atol=1e-5)

def test_declick_no_spikes():
    sr = 24000
    wav = np.random.normal(0, 0.01, sr).astype(np.float32)

    out_original = original_apply_declick(wav, sr)
    out_vectorized = vectorized_apply_declick(wav, sr)

    np.testing.assert_allclose(out_original, out_vectorized, rtol=1e-7, atol=1e-7)

def test_declick_short_buffer():
    sr = 24000
    wav = np.array([0.1, 0.2], dtype=np.float32) # Shorter than 2ms window

    out_original = original_apply_declick(wav, sr)
    out_vectorized = vectorized_apply_declick(wav, sr)

    np.testing.assert_allclose(out_original, out_vectorized, rtol=1e-7, atol=1e-7)
