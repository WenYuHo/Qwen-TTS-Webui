import numpy as np
import pytest
from backend.utils import AudioPostProcessor

def original_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """Original loop-based implementation for parity testing."""
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
    except Exception:
        return wav

@pytest.mark.parametrize("sr", [24000, 44100, 48000])
@pytest.mark.parametrize("channels", [1, 2])
def test_declick_parity(sr, channels):
    duration = 0.5 # seconds
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

    expected = original_apply_declick(wav, sr)
    actual = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_allclose(actual, expected, rtol=1e-5, atol=1e-5)

def test_declick_tail_handling():
    sr = 24000
    window = int(sr * 0.002)
    # length that is not a multiple of window
    n_samples = window * 10 + 5
    wav = np.random.normal(0, 0.1, n_samples).astype(np.float32)

    # Add spike in the tail
    wav[-2] = 0.9

    expected = original_apply_declick(wav, sr)
    actual = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_allclose(actual, expected, rtol=1e-5, atol=1e-5)
