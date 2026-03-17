import numpy as np
import sys
import os

# Add src to path
sys.path.append(os.path.abspath("src"))

from backend.utils import AudioPostProcessor

def original_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """Original loop-based de-clicker logic for parity testing."""
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

def test_parity():
    sr = 24000
    # Use a size that is NOT a multiple of window to test remainder handling
    window = int(sr * 0.002)
    duration_samples = window * 10 + 5

    # Test cases: mono, stereo, zeros, all spikes
    test_cases = [
        ("mono", np.random.randn(duration_samples).astype(np.float32) * 0.1),
        ("stereo", np.random.randn(2, duration_samples).astype(np.float32) * 0.1),
        ("zeros", np.zeros(duration_samples, dtype=np.float32)),
        ("small", np.random.randn(window // 2).astype(np.float32))
    ]

    # Add some spikes to mono/stereo cases
    test_cases[0][1][window * 2 + 5] = 2.0
    test_cases[1][1][0, window * 3 + 2] = 2.0
    test_cases[1][1][1, window * 5 + 1] = -2.0

    print("Running parity tests...")
    all_passed = True
    for name, wav in test_cases:
        expected = original_apply_declick(wav, sr)
        actual = AudioPostProcessor.apply_declick(wav, sr)

        if np.allclose(expected, actual):
            print(f"✅ {name}: Passed")
        else:
            diff = np.abs(expected - actual).max()
            print(f"❌ {name}: Failed (Max diff: {diff})")
            all_passed = False

    if not all_passed:
        sys.exit(1)

if __name__ == "__main__":
    test_parity()
