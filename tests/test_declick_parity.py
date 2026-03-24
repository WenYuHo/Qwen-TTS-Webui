import numpy as np
import sys
import os

# Add src to path for imports
sys.path.append(os.path.abspath("src"))
from backend.utils import AudioPostProcessor

def original_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """Original implementation with loop."""
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

def test_declick_parity():
    sr = 24000
    duration = 1.0 # 1 second
    n_samples = int(sr * duration)

    # Test Mono
    wav_mono = np.random.normal(0, 0.1, n_samples).astype(np.float32)
    # Add some spikes
    wav_mono[100] = 0.9
    wav_mono[500] = -0.8
    wav_mono[1000:1005] = 0.95 # Multi-sample spike

    expected_mono = original_apply_declick(wav_mono, sr)
    actual_mono = AudioPostProcessor.apply_declick(wav_mono, sr)

    np.testing.assert_allclose(actual_mono, expected_mono, rtol=1e-5, err_msg="Mono parity failed")
    print("Mono parity passed")

    # Test Stereo
    wav_stereo = np.random.normal(0, 0.1, (2, n_samples)).astype(np.float32)
    wav_stereo[0, 100] = 0.9
    wav_stereo[1, 200] = -0.8

    expected_stereo = original_apply_declick(wav_stereo, sr)
    actual_stereo = AudioPostProcessor.apply_declick(wav_stereo, sr)

    np.testing.assert_allclose(actual_stereo, expected_stereo, rtol=1e-5, err_msg="Stereo parity failed")
    print("Stereo parity passed")

    # Test Small Buffer
    wav_small = np.random.normal(0, 0.1, 10).astype(np.float32)
    expected_small = original_apply_declick(wav_small, sr)
    actual_small = AudioPostProcessor.apply_declick(wav_small, sr)
    np.testing.assert_allclose(actual_small, expected_small, rtol=1e-5, err_msg="Small buffer parity failed")
    print("Small buffer parity passed")

if __name__ == "__main__":
    test_declick_parity()
