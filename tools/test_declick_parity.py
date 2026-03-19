import numpy as np
import sys
import os

# Add src to path for imports
sys.path.append(os.path.abspath("src"))
from backend.utils import AudioPostProcessor

def original_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """Original loop-based de-clicker implementation for parity testing."""
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
    srs = [16000, 24000, 44100, 48000]
    durations = [0.1, 0.5, 1.0]

    for sr in srs:
        for duration in durations:
            n_samples = int(sr * duration)
            # Create audio with some guaranteed spikes
            wav = np.random.normal(0, 0.1, n_samples).astype(np.float32)
            spike_indices = np.random.choice(n_samples, min(n_samples, 20), replace=False)
            wav[spike_indices] = np.random.choice([-1.0, 1.0], len(spike_indices)) * 0.9

            # Test Mono
            res_orig = original_apply_declick(wav, sr)
            res_new = AudioPostProcessor.apply_declick(wav, sr)

            if not np.allclose(res_orig, res_new):
                print(f"FAILED Parity Mono: SR={sr}, Duration={duration}")
                return False

            # Test Stereo
            wav_stereo = np.stack([wav, wav * 0.5])
            res_orig_stereo = original_apply_declick(wav_stereo, sr)
            res_new_stereo = AudioPostProcessor.apply_declick(wav_stereo, sr)

            if not np.allclose(res_orig_stereo, res_new_stereo):
                print(f"FAILED Parity Stereo: SR={sr}, Duration={duration}")
                return False

    print("SUCCESS: Parity test passed (currently comparing original to original)")
    return True

if __name__ == "__main__":
    if test_parity():
        sys.exit(0)
    else:
        sys.exit(1)
