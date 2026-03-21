import numpy as np
import sys
import os
from pathlib import Path

# Original implementation (for parity check)
def apply_declick_original(wav: np.ndarray, sr: int) -> np.ndarray:
    try:
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
    except Exception as e:
        print(f"Original de-click failed: {e}")
        return wav

# Add src to path for imports
sys.path.append(os.path.abspath("src"))
from backend.utils import AudioPostProcessor

def test_parity(duration_sec=5, sr=24000):
    print(f"Testing parity on {duration_sec}s of {sr}Hz audio...")

    # Generate random audio with some spikes
    n_samples = int(duration_sec * sr)
    # Add some non-integer samples to test remainder handling
    n_samples += 123

    wav = np.random.normal(0, 0.1, n_samples).astype(np.float32)

    # Add random spikes
    spike_indices = np.random.choice(n_samples, 50, replace=False)
    wav[spike_indices] = np.random.choice([-1.0, 1.0], 50) * 0.9

    # Original
    out_orig = apply_declick_original(wav, sr)

    # New Vectorized
    out_new = AudioPostProcessor.apply_declick(wav, sr)

    # Check parity
    if np.allclose(out_orig, out_new, atol=1e-7):
        print("✅ Parity test PASSED!")
    else:
        diff = np.abs(out_orig - out_new)
        max_diff = np.max(diff)
        print(f"❌ Parity test FAILED! Max diff: {max_diff}")
        # Find where it differs
        idx = np.where(diff > 1e-7)[0]
        if len(idx) > 0:
            print(f"First difference at index {idx[0]}: orig={out_orig[idx[0]]}, new={out_new[idx[0]]}")
        sys.exit(1)

    # Test Stereo
    print("Testing stereo parity...")
    wav_stereo = np.stack([wav, wav * 0.5])
    out_orig_stereo = apply_declick_original(wav_stereo, sr)
    out_new_stereo = AudioPostProcessor.apply_declick(wav_stereo, sr)

    if np.allclose(out_orig_stereo, out_new_stereo, atol=1e-7):
        print("✅ Stereo parity test PASSED!")
    else:
        print("❌ Stereo parity test FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    test_parity()
