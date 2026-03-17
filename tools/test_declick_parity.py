import numpy as np
import sys
import os

# Add src to path
sys.path.append(os.path.abspath("src"))

from backend.utils import AudioPostProcessor

def apply_declick_original(wav: np.ndarray, sr: int) -> np.ndarray:
    """Original loop-based de-clicker."""
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

def run_tests():
    sr = 24000
    test_cases = [
        ("Short (0.1s)", np.random.uniform(-0.1, 0.1, int(0.1 * sr))),
        ("Exact window", np.random.uniform(-0.1, 0.1, int(sr * 0.002))),
        ("Remainder", np.random.uniform(-0.1, 0.1, int(sr * 0.002) + 10)),
        ("Small (< 2 samples)", np.random.uniform(-0.1, 0.1, 1)),
        ("Empty", np.array([], dtype=np.float32)),
        ("Stereo", np.random.uniform(-0.1, 0.1, (2, int(0.1 * sr)))),
    ]

    for name, wav in test_cases:
        # Add some spikes
        if wav.size > 0:
            indices = np.random.randint(0, wav.size)
            if len(wav.shape) > 1:
                wav[indices // wav.shape[1], indices % wav.shape[1]] *= 50
            else:
                wav[indices] *= 50

        orig = apply_declick_original(wav, sr)
        # ⚡ Bolt: Use the actual implementation from backend.utils
        vec = AudioPostProcessor.apply_declick(wav, sr)

        try:
            np.testing.assert_allclose(orig, vec, rtol=1e-5, atol=1e-8)
            print(f"PASSED: {name}")
        except AssertionError as e:
            print(f"FAILED: {name}")
            print(e)
            sys.exit(1)

if __name__ == "__main__":
    run_tests()
