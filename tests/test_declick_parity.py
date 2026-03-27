import numpy as np
import sys
import os

# Add src to path
sys.path.append(os.path.abspath("src"))
from backend.utils import AudioPostProcessor

def original_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """Original implementation for parity checking."""
    out = wav.copy()
    window = int(sr * 0.002) # 2ms
    if window < 2: return wav

    for i in range(0, len(wav), window):
        chunk = wav[i:i+window]
        if len(chunk) < 2: continue
        local_rms = np.sqrt(np.mean(chunk**2)) + 1e-6
        spikes = np.abs(chunk) > (local_rms * 10)
        if np.any(spikes):
            sign = np.sign(chunk[spikes])
            out[i:i+window][spikes] = sign * local_rms * 3
    return out

def test_parity():
    sr = 24000
    # Test different lengths including remainders
    for length in [1000, 1001, 24000, 24000 + 5]:
        print(f"Testing length {length}...")
        wav = np.random.normal(0, 0.1, length).astype(np.float32)
        # Add some spikes
        wav[np.random.choice(length, 10, replace=False)] = 0.9

        expected = original_apply_declick(wav, sr)
        actual = AudioPostProcessor.apply_declick(wav, sr)

        np.testing.assert_allclose(actual, expected, atol=1e-6)
    print("Parity test passed!")

if __name__ == "__main__":
    test_parity()
