import numpy as np
import sys
import os

# Add src to path for imports
sys.path.append(os.path.abspath("src"))
from backend.utils import AudioPostProcessor

def original_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """Original loop-based de-clicker for parity testing."""
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

def test_declick_parity():
    print("Testing de-click parity between original and vectorized versions...")

    sr = 24000
    durations = [0.1, 1.0, 5.0]

    for duration in durations:
        n_samples = int(duration * sr)
        # Ensure some interesting cases (remainder handling)
        n_samples += 7

        wav = np.random.normal(0, 0.1, n_samples).astype(np.float32)

        # Add some spikes
        spike_indices = np.random.choice(n_samples, 20, replace=False)
        wav[spike_indices] = np.random.choice([-1.0, 1.0], 20) * 0.9

        out_orig = original_apply_declick(wav, sr)
        out_vec = AudioPostProcessor.apply_declick(wav, sr)

        # Check for identity (with small epsilon for float precision differences in math patterns)
        # np.einsum and np.mean(chunk**2) should be very close but might have tiny differences
        diff = np.abs(out_orig - out_vec)
        max_diff = np.max(diff)

        if max_diff > 1e-6:
            print(f"FAILED parity for duration {duration}s. Max diff: {max_diff}")
            return False
        else:
            print(f"PASSED parity for duration {duration}s. Max diff: {max_diff}")

    # Test Stereo
    wav_stereo = np.random.normal(0, 0.1, (2, sr)).astype(np.float32)
    wav_stereo[0, 100] = 0.9
    wav_stereo[1, 500] = -0.9

    out_orig_stereo = original_apply_declick(wav_stereo, sr)
    out_vec_stereo = AudioPostProcessor.apply_declick(wav_stereo, sr)

    diff_stereo = np.abs(out_orig_stereo - out_vec_stereo)
    if np.max(diff_stereo) > 1e-6:
        print(f"FAILED parity for stereo. Max diff: {np.max(diff_stereo)}")
        return False
    else:
        print(f"PASSED parity for stereo. Max diff: {np.max(diff_stereo)}")

    return True

if __name__ == "__main__":
    if test_declick_parity():
        print("All parity tests PASSED!")
    else:
        sys.exit(1)
