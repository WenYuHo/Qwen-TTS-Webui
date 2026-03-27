import numpy as np
import pytest
import sys
import os

# Add src to path for imports
sys.path.append(os.path.abspath("src"))
from backend.utils import AudioPostProcessor

def original_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """Original loop-based implementation for parity check."""
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

@pytest.mark.parametrize("sr", [16000, 24000, 44100])
@pytest.mark.parametrize("duration", [0.1, 0.5, 1.0])
@pytest.mark.parametrize("channels", [1, 2])
def test_declick_parity(sr, duration, channels):
    n_samples = int(duration * sr)
    if channels == 1:
        wav = np.random.normal(0, 0.1, n_samples).astype(np.float32)
    else:
        wav = np.random.normal(0, 0.1, (channels, n_samples)).astype(np.float32)

    # Add some spikes
    if channels == 1:
        spike_indices = np.random.choice(n_samples, 10, replace=False)
        wav[spike_indices] = 0.9
    else:
        for c in range(channels):
            spike_indices = np.random.choice(n_samples, 10, replace=False)
            wav[c, spike_indices] = 0.9

    expected = original_apply_declick(wav, sr)
    actual = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_allclose(actual, expected, atol=1e-6)

if __name__ == "__main__":
    # Quick manual run
    test_declick_parity(24000, 1.0, 1)
    test_declick_parity(24000, 1.0, 2)
    print("Parity test passed!")
