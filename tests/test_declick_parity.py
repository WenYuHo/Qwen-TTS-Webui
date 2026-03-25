import numpy as np
import pytest
import sys
import os

# Add src to path for imports
sys.path.append(os.path.abspath("src"))
from backend.utils import AudioPostProcessor

def original_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """The original loop-based implementation to use as a baseline."""
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
        spike_indices = np.random.choice(n_samples, 20, replace=False)
        wav[spike_indices] = np.random.choice([-1.0, 1.0], 20) * 0.9
    else:
        for c in range(channels):
            spike_indices = np.random.choice(n_samples, 20, replace=False)
            wav[c, spike_indices] = np.random.choice([-1.0, 1.0], 20) * 0.9

    original_out = original_apply_declick(wav, sr)
    optimized_out = AudioPostProcessor.apply_declick(wav, sr)

    # Use allclose with a small tolerance for floating point variations if any
    # But since it's the same logic, it should be exactly equal
    np.testing.assert_allclose(original_out, optimized_out, atol=1e-7)

def test_declick_edge_cases():
    sr = 24000
    # Very short buffer
    short_wav = np.array([0.1, 0.2], dtype=np.float32)
    np.testing.assert_allclose(original_apply_declick(short_wav, sr), AudioPostProcessor.apply_declick(short_wav, sr))

    # Buffer with no spikes
    flat_wav = np.zeros(1000, dtype=np.float32)
    np.testing.assert_allclose(original_apply_declick(flat_wav, sr), AudioPostProcessor.apply_declick(flat_wav, sr))

    # Buffer that is not a multiple of window size
    window = int(sr * 0.002)
    odd_wav = np.random.normal(0, 0.1, window * 2 + 5).astype(np.float32)
    np.testing.assert_allclose(original_apply_declick(odd_wav, sr), AudioPostProcessor.apply_declick(odd_wav, sr))

if __name__ == "__main__":
    # If run directly, run the parity check once
    test_declick_parity(24000, 1.0, 1)
    print("Parity check passed!")
