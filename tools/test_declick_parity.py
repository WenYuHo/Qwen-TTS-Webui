import numpy as np
import sys
import os

# Add src to path
sys.path.append(os.path.abspath("src"))

from backend.utils import AudioPostProcessor

def original_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """Original loop-based de-clicker for parity testing."""
    try:
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
    except Exception:
        return wav

def test_parity():
    sr = 24000
    # Test mono
    wav_mono = np.random.uniform(-0.5, 0.5, sr * 2).astype(np.float32)
    spike_indices = np.random.randint(0, len(wav_mono), 10)
    wav_mono[spike_indices] = 1.0

    out_orig = original_apply_declick(wav_mono, sr)
    out_new = AudioPostProcessor.apply_declick(wav_mono, sr)

    if np.allclose(out_orig, out_new):
        print("Mono parity: PASSED")
    else:
        diff = np.max(np.abs(out_orig - out_new))
        print(f"Mono parity: FAILED (max diff: {diff})")
        # Find where it differs
        diff_indices = np.where(~np.isclose(out_orig, out_new))[0]
        if len(diff_indices) > 0:
             print(f"First diff at index {diff_indices[0]}")

    # Test stereo
    wav_stereo = np.random.uniform(-0.5, 0.5, (2, sr * 2)).astype(np.float32)
    wav_stereo[0, 100] = 1.0
    wav_stereo[1, 500] = -1.0

    out_orig_stereo = original_apply_declick(wav_stereo, sr)
    out_new_stereo = AudioPostProcessor.apply_declick(wav_stereo, sr)

    if np.allclose(out_orig_stereo, out_new_stereo):
        print("Stereo parity: PASSED")
    else:
        print(f"Stereo parity: FAILED (max diff: {np.max(np.abs(out_orig_stereo - out_new_stereo))})")

if __name__ == "__main__":
    test_parity()
