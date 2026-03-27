import numpy as np
import pytest
from backend.utils import AudioPostProcessor

def apply_declick_original(wav: np.ndarray, sr: int) -> np.ndarray:
    """The original loop-based heuristic for parity testing."""
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
    """The proposed vectorized heuristic."""
    try:
        if len(wav.shape) > 1:
            return np.stack([apply_declick_vectorized(ch, sr) for ch in wav])

        window = int(sr * 0.002)  # 2ms
        if window < 2 or len(wav) < window:
            return wav.copy()

        # ⚡ Bolt: Vectorized spike detection using reshaping and einsum
        n_chunks = len(wav) // window
        main_part = wav[:n_chunks * window].reshape(n_chunks, window)

        # O(N) memory-efficient RMS: sqrt(sum(x^2)/N)
        # np.einsum('ij,ij->i', main_part, main_part) is faster than (main_part**2).sum(axis=1)
        sq_sums = np.einsum('ij,ij->i', main_part, main_part)
        rms = np.sqrt(sq_sums / window) + 1e-6

        # Identify spikes (n_chunks, window)
        spikes = np.abs(main_part) > (rms[:, None] * 10)

        out_main = main_part.copy()
        if np.any(spikes):
            # Clamp spikes to local RMS * 3
            # Use broadcasting to apply the per-chunk RMS limit
            out_main[spikes] = np.sign(main_part[spikes]) * (rms[:, None] * 3).repeat(window, axis=1).reshape(n_chunks, window)[spikes]

        out = out_main.ravel()

        # Handle remainder
        remainder = wav[n_chunks * window:]
        if len(remainder) >= 2:
            rem_rms = np.sqrt(np.vdot(remainder, remainder) / len(remainder)) + 1e-6
            rem_spikes = np.abs(remainder) > (rem_rms * 10)
            if np.any(rem_spikes):
                remainder = remainder.copy()
                remainder[rem_spikes] = np.sign(remainder[rem_spikes]) * rem_rms * 3
            out = np.concatenate([out, remainder])
        elif len(remainder) > 0:
            out = np.concatenate([out, remainder])

        return out
    except Exception:
        return wav.copy()

@pytest.mark.parametrize("sr", [16000, 24000, 44100])
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
        spike_indices = np.random.choice(n_samples, min(10, n_samples), replace=False)
        wav[spike_indices] = 0.9
    else:
        for c in range(channels):
            spike_indices = np.random.choice(n_samples, min(10, n_samples), replace=False)
            wav[c, spike_indices] = 0.9

    original = apply_declick_original(wav, sr)
    vectorized = AudioPostProcessor.apply_declick(wav, sr)

    assert np.allclose(original, vectorized, atol=1e-6)

def test_declick_edge_cases():
    sr = 24000
    # Very small buffer
    wav = np.array([0.1, 0.9, 0.1], dtype=np.float32)
    assert np.allclose(apply_declick_original(wav, sr), AudioPostProcessor.apply_declick(wav, sr))

    # Buffer exactly window size
    window = int(sr * 0.002)
    wav = np.random.normal(0, 0.1, window).astype(np.float32)
    wav[0] = 1.0 # spike
    assert np.allclose(apply_declick_original(wav, sr), AudioPostProcessor.apply_declick(wav, sr))

    # Empty buffer
    wav = np.array([], dtype=np.float32)
    assert np.allclose(apply_declick_original(wav, sr), AudioPostProcessor.apply_declick(wav, sr))
