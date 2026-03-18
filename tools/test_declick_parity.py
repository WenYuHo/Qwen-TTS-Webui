import numpy as np
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from backend.utils import AudioPostProcessor

def original_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """Original implementation with loops."""
    try:
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
    except Exception:
        return wav

def test_parity():
    sr = 24000
    # Create audio with known spikes
    wav = np.random.normal(0, 0.1, sr * 5).astype(np.float32)
    spikes_indices = np.random.choice(len(wav), 100, replace=False)
    wav[spikes_indices] *= 50

    # Also test multi-channel
    wav_stereo = np.stack([wav, wav * 0.5])

    print("Testing mono parity...")
    res_orig = original_declick(wav, sr)
    res_curr = AudioPostProcessor.apply_declick(wav, sr)

    if np.allclose(res_orig, res_curr):
        print("Mono parity check PASSED")
    else:
        print("Mono parity check FAILED")
        diff = np.abs(res_orig - res_curr)
        print(f"Max diff: {np.max(diff)}")

    print("\nTesting stereo parity...")
    res_orig_s = original_declick(wav_stereo, sr)
    res_curr_s = AudioPostProcessor.apply_declick(wav_stereo, sr)

    if np.allclose(res_orig_s, res_curr_s):
        print("Stereo parity check PASSED")
    else:
        print("Stereo parity check FAILED")
        diff = np.abs(res_orig_s - res_curr_s)
        print(f"Max diff: {np.max(diff)}")

if __name__ == "__main__":
    test_parity()
