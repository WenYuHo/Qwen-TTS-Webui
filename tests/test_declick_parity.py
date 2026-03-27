import numpy as np
import pytest
from backend.utils import AudioPostProcessor

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
    """Proposed vectorized de-clicker for parity testing."""
    if len(wav.shape) > 1:
        # ⚡ Bolt: Process channels independently using vectorized logic
        return np.stack([vectorized_apply_declick(ch, sr) for ch in wav])

    n_samples = wav.shape[0]
    window = int(sr * 0.002) # 2ms
    if window < 2 or n_samples < window:
        return wav.copy()

    # Process in chunks using reshaping
    n_chunks = n_samples // window
    main_body_len = n_chunks * window
    main_body = wav[:main_body_len].reshape(n_chunks, window)

    # ⚡ Bolt: Use einsum for memory-efficient row-wise squared sums (RMS)
    sq_sums = np.einsum('ij,ij->i', main_body, main_body)
    rms = np.sqrt(sq_sums / window) + 1e-6

    # ⚡ Bolt: Detect spikes using broadcasting
    spikes = np.abs(main_body) > (rms[:, None] * 10)

    out = wav.copy()
    if np.any(spikes):
        main_out = out[:main_body_len].reshape(n_chunks, window)
        # Apply clamping only where spikes are detected
        row_idx, col_idx = np.where(spikes)
        main_out[row_idx, col_idx] = np.sign(main_out[row_idx, col_idx]) * (rms[row_idx] * 3)

    # Handle remainder
    if main_body_len < n_samples:
        remainder = wav[main_body_len:]
        if len(remainder) >= 2:
            rem_rms = np.sqrt(np.vdot(remainder, remainder) / len(remainder)) + 1e-6
            rem_spikes = np.abs(remainder) > (rem_rms * 10)
            if np.any(rem_spikes):
                out[main_body_len:][rem_spikes] = np.sign(remainder[rem_spikes]) * (rem_rms * 3)

    return out

@pytest.mark.parametrize("sr", [16000, 24000, 44100])
@pytest.mark.parametrize("duration_ms", [10, 50, 100])
@pytest.mark.parametrize("channels", [1, 2])
def test_declick_parity(sr, duration_ms, channels):
    n_samples = int(sr * (duration_ms / 1000.0))
    if channels == 1:
        wav = np.random.normal(0, 0.1, n_samples).astype(np.float32)
    else:
        wav = np.random.normal(0, 0.1, (channels, n_samples)).astype(np.float32)

    # Add some spikes
    if channels == 1:
        indices = np.random.choice(n_samples, min(10, n_samples), replace=False)
        wav[indices] = np.random.choice([-1.0, 1.0], len(indices))
    else:
        for c in range(channels):
            indices = np.random.choice(n_samples, min(10, n_samples), replace=False)
            wav[c, indices] = np.random.choice([-1.0, 1.0], len(indices))

    expected = original_apply_declick(wav, sr)
    actual = vectorized_apply_declick(wav, sr)

    np.testing.assert_allclose(actual, expected, rtol=1e-5, atol=1e-7)

def test_declick_small_buffer():
    sr = 24000
    wav = np.array([0.1, 0.9, 0.1], dtype=np.float32) # Very small

    expected = original_apply_declick(wav, sr)
    actual = vectorized_apply_declick(wav, sr)

    np.testing.assert_allclose(actual, expected)

def test_declick_no_spikes():
    sr = 24000
    wav = np.zeros(1000, dtype=np.float32)

    expected = original_apply_declick(wav, sr)
    actual = vectorized_apply_declick(wav, sr)

    np.testing.assert_allclose(actual, expected)

def test_declick_remainder_spike():
    sr = 24000
    window = int(sr * 0.002)
    # 1.5 windows
    n_samples = int(window * 1.5)
    wav = np.random.normal(0, 0.01, n_samples).astype(np.float32)
    # Add spike in the remainder
    wav[-1] = 1.0

    expected = original_apply_declick(wav, sr)
    actual = vectorized_apply_declick(wav, sr)

    np.testing.assert_allclose(actual, expected)
