import numpy as np
import sys
import os

# Add src to path
sys.path.append(os.path.abspath("src"))

from backend.utils import AudioPostProcessor

def original_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """Original loop-based implementation for parity check."""
    if len(wav.shape) > 1:
        out = np.zeros_like(wav)
        for i in range(wav.shape[0]):
            out[i] = original_declick(wav[i], sr)
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

def test_parity():
    sr = 24000
    # Test with different lengths
    for length in [100, 1000, 1024, 10000]:
        wav = np.random.randn(length).astype(np.float32)
        # Add some spikes that should be detected
        wav[np.random.randint(0, length, 5)] *= 100

        res_orig = original_declick(wav, sr)
        res_vect = AudioPostProcessor.apply_declick(wav, sr)

        np.testing.assert_allclose(res_orig, res_vect, rtol=1e-5, atol=1e-5)
        print(f"Parity check passed for length {length}")

if __name__ == "__main__":
    test_parity()
