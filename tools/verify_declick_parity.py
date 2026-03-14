import numpy as np
import sys
import os

# Add src to path
sys.path.append(os.path.abspath("src"))

def apply_declick_orig(wav, sr):
    """Original loop-based de-clicker for parity testing."""
    try:
        if len(wav.shape) > 1:
            out = np.zeros_like(wav)
            for i in range(wav.shape[0]):
                out[i] = apply_declick_orig(wav[i], sr)
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
    except Exception as e:
        print(f"Original De-click failed: {e}")
        return wav

def test_parity():
    from backend.utils import AudioPostProcessor

    sr = 24000

    test_cases = [
        ("Mono Small", np.random.randn(2400).astype(np.float32) * 0.1),
        ("Mono Large", np.random.randn(24000).astype(np.float32) * 0.1),
        ("Stereo", np.random.randn(2, 24000).astype(np.float32) * 0.1),
        ("With Spikes", (lambda: (w := np.random.randn(24000).astype(np.float32) * 0.1, w.__setitem__(100, 5.0), w)[2])()),
        ("Remainder", np.random.randn(2400 + 10).astype(np.float32) * 0.1),
    ]

    for name, wav in test_cases:
        print(f"Testing {name}...")
        expected = apply_declick_orig(wav, sr)
        actual = AudioPostProcessor.apply_declick(wav, sr)

        if not np.allclose(expected, actual, atol=1e-7):
            print(f"FAILED parity for {name}")
            # Optional: detailed diff
            max_diff = np.max(np.abs(expected - actual))
            print(f"Max diff: {max_diff}")
            sys.exit(1)
        else:
            print(f"PASSED parity for {name}")

if __name__ == "__main__":
    # This script should be run AFTER the implementation is updated.
    # But we can try it now to confirm it passes with itself (if we point actual to apply_declick_orig)
    try:
        from backend.utils import AudioPostProcessor
        test_parity()
    except ImportError:
        print("Backend utils not found. Run with PYTHONPATH=src")
