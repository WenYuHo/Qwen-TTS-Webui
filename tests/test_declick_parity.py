import numpy as np
import pytest
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(os.path.abspath("src"))

def apply_declick_original(wav: np.ndarray, sr: int) -> np.ndarray:
    """Original loop-based implementation."""
    try:
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
    except Exception:
        return wav

def apply_declick_vectorized(wav: np.ndarray, sr: int) -> np.ndarray:
    """Proposed vectorized implementation."""
    try:
        if len(wav.shape) > 1:
            # Multi-channel
            return np.stack([apply_declick_vectorized(ch, sr) for ch in wav])

        window = int(sr * 0.002) # 2ms
        if window < 2 or len(wav) < window: return wav.copy()

        n_windows = len(wav) // window
        prefix_len = n_windows * window

        # Reshape into windows
        chunks = wav[:prefix_len].reshape(n_windows, window)

        # Calculate RMS for each window using einsum for speed and memory efficiency
        rms = np.sqrt(np.einsum('ij,ij->i', chunks, chunks) / window) + 1e-6

        # Detect spikes
        spikes = np.abs(chunks) > (rms[:, np.newaxis] * 10)

        if np.any(spikes):
            out_chunks = chunks.copy()
            row_idx, col_idx = np.where(spikes)
            # Clamp spikes
            out_chunks[row_idx, col_idx] = np.sign(chunks[row_idx, col_idx]) * rms[row_idx] * 3
            out_prefix = out_chunks.ravel()
        else:
            out_prefix = wav[:prefix_len].copy()

        # Handle remainder
        remainder = wav[prefix_len:]
        if len(remainder) >= 2:
            rem_out = remainder.copy()
            rem_rms = np.sqrt(np.mean(remainder**2)) + 1e-6
            rem_spikes = np.abs(remainder) > (rem_rms * 10)
            if np.any(rem_spikes):
                rem_out[rem_spikes] = np.sign(remainder[rem_spikes]) * rem_rms * 3
            return np.concatenate([out_prefix, rem_out])

        return np.concatenate([out_prefix, remainder])
    except Exception:
        return wav.copy()

@pytest.mark.parametrize("sr", [16000, 24000, 44100, 48000])
@pytest.mark.parametrize("channels", [1, 2])
def test_declick_parity(sr, channels):
    # Duration 1 second
    duration = 1.0
    n_samples = int(sr * duration)

    if channels == 1:
        wav = np.random.normal(0, 0.1, n_samples).astype(np.float32)
    else:
        wav = np.random.normal(0, 0.1, (channels, n_samples)).astype(np.float32)

    # Add some spikes
    if channels == 1:
        indices = np.random.choice(n_samples, 20, replace=False)
        wav[indices] = np.random.choice([-1.0, 1.0], 20) * 0.9
    else:
        for c in range(channels):
            indices = np.random.choice(n_samples, 20, replace=False)
            wav[c, indices] = np.random.choice([-1.0, 1.0], 20) * 0.9

    original_out = apply_declick_original(wav, sr)
    vectorized_out = apply_declick_vectorized(wav, sr)

    # Use small tolerance due to potential floating point differences in RMS calculation methods
    # np.mean(chunk**2) vs np.einsum('ij,ij->i', chunks, chunks) / window
    np.testing.assert_allclose(original_out, vectorized_out, rtol=1e-5, atol=1e-7)

def test_declick_short_buffer():
    sr = 24000
    wav = np.array([0.5, -0.5], dtype=np.float32) # Shorter than window

    orig = apply_declick_original(wav, sr)
    vec = apply_declick_vectorized(wav, sr)

    np.testing.assert_array_equal(orig, vec)

def test_declick_no_spikes():
    sr = 24000
    wav = np.zeros(1000, dtype=np.float32)

    orig = apply_declick_original(wav, sr)
    vec = apply_declick_vectorized(wav, sr)

    np.testing.assert_array_equal(orig, vec)

if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__])
