import numpy as np
import sys
import os

# Add src to path for imports
sys.path.append(os.path.abspath("src"))
from backend.utils import AudioPostProcessor

def original_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """Original loop-based de-clicker implementation."""
    if len(wav.shape) > 1:
        out = np.zeros_like(wav)
        for i in range(wav.shape[0]):
            out[i] = original_apply_declick(wav[i], sr)
        return out

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
    duration_sec = 1
    n_samples = duration_sec * sr

    # Test cases
    cases = [
        ("Random Noise", np.random.normal(0, 0.1, n_samples).astype(np.float32)),
        ("Mono with Spikes", np.zeros(n_samples, dtype=np.float32)),
        ("Stereo with Spikes", np.zeros((2, n_samples), dtype=np.float32)),
        ("Short Buffer", np.random.normal(0, 0.1, 100).astype(np.float32)),
        ("Remainder Buffer", np.random.normal(0, 0.1, window := int(sr*0.002) + 5).astype(np.float32))
    ]

    # Add spikes to spikes cases
    cases[1][1] [1000] = 1.0
    cases[1][1] [5000] = -0.9

    cases[2][1] [0, 1000] = 1.0
    cases[2][1] [1, 5000] = -0.9

    for name, wav in cases:
        print(f"Testing parity for: {name}...")

        # We need to test against the CURRENT implementation in backend.utils
        # Before optimization, this should pass trivially.
        # After optimization, it will verify the new logic.

        expected = original_apply_declick(wav, sr)
        actual = AudioPostProcessor.apply_declick(wav, sr)

        # Use allclose for float comparisons
        if np.allclose(expected, actual, atol=1e-7):
            print(f"✅ {name} passed!")
        else:
            diff = np.max(np.abs(expected - actual))
            print(f"❌ {name} failed! Max diff: {diff}")
            sys.exit(1)

if __name__ == "__main__":
    test_parity()
