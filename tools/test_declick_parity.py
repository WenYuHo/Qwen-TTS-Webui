
import numpy as np
import sys
import os

# Add src to path
sys.path.append(os.path.abspath("src"))

from backend.utils import AudioPostProcessor

def original_declick(wav, sr):
    """The original loop-based implementation."""
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
    # Test mono
    wav_mono = np.random.normal(0, 0.1, 1000).astype(np.float32)
    wav_mono[100] = 1.0
    wav_mono[500] = -0.9

    expected_mono = original_declick(wav_mono, sr)
    actual_mono = AudioPostProcessor.apply_declick(wav_mono, sr)

    np.testing.assert_allclose(actual_mono, expected_mono, rtol=1e-5, err_msg="Mono parity failed")
    print("Mono parity passed!")

    # Test stereo
    wav_stereo = np.random.normal(0, 0.1, (2, 1000)).astype(np.float32)
    wav_stereo[0, 100] = 1.0
    wav_stereo[1, 500] = -0.9

    expected_stereo = original_declick(wav_stereo, sr)
    actual_stereo = AudioPostProcessor.apply_declick(wav_stereo, sr)

    np.testing.assert_allclose(actual_stereo, expected_stereo, rtol=1e-5, err_msg="Stereo parity failed")
    print("Stereo parity passed!")

    # Test remainder case
    wav_rem = np.random.normal(0, 0.1, 1001).astype(np.float32)
    wav_rem[-1] = 1.0

    expected_rem = original_declick(wav_rem, sr)
    actual_rem = AudioPostProcessor.apply_declick(wav_rem, sr)

    np.testing.assert_allclose(actual_rem, expected_rem, rtol=1e-5, err_msg="Remainder parity failed")
    print("Remainder parity passed!")

if __name__ == "__main__":
    test_parity()
