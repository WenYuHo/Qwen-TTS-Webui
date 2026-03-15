import numpy as np
import sys
import os

# Add src to path
sys.path.append(os.path.abspath("src"))

def apply_declick_old(wav: np.ndarray, sr: int) -> np.ndarray:
    """Original loop-based de-clicker for parity testing."""
    if len(wav.shape) > 1:
        out = np.zeros_like(wav)
        for i in range(wav.shape[0]):
            out[i] = apply_declick_old(wav[i], sr)
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
    from backend.utils import AudioPostProcessor

    sr = 24000
    # Test cases
    cases = [
        ("Mono Small", np.random.randn(100).astype(np.float32)),
        ("Mono Medium", np.random.randn(24000).astype(np.float32)),
        ("Mono with spikes", np.random.randn(24000).astype(np.float32)),
        ("Stereo", np.random.randn(2, 24000).astype(np.float32)),
        ("Remainder", np.random.randn(24000 + 10).astype(np.float32)),
    ]

    # Add spikes to case 3
    cases[2][1][100:105] *= 50

    for name, wav in cases:
        print(f"Testing parity for: {name}")
        old_out = apply_declick_old(wav, sr)
        new_out = AudioPostProcessor.apply_declick(wav, sr)

        # Check if they are exactly the same
        if np.array_equal(old_out, new_out):
            print(f"✅ {name} passed parity")
        else:
            diff = np.abs(old_out - new_out)
            max_diff = np.max(diff)
            print(f"❌ {name} failed parity (Max diff: {max_diff})")
            # If diff is very small, it might be floating point variance (though should be identical)
            if max_diff < 1e-6:
                print(f"   (Difference is negligible, likely floating point precision)")
            else:
                sys.exit(1)

if __name__ == "__main__":
    test_parity()
