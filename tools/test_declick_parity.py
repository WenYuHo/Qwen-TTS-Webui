import numpy as np
import sys
import os

# Add src to path for imports
sys.path.append(os.path.abspath("src"))
from backend.utils import AudioPostProcessor

def apply_declick_original(wav: np.ndarray, sr: int) -> np.ndarray:
    """Original loop-based de-clicker for parity testing."""
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

def test_parity():
    sr = 24000
    # Test mono
    wav_mono = np.random.normal(0, 0.1, 48000).astype(np.float32)
    # Add spikes
    wav_mono[1000] = 0.9
    wav_mono[20000] = -0.8

    out_orig = apply_declick_original(wav_mono, sr)
    out_vec = AudioPostProcessor.apply_declick(wav_mono, sr)

    # Check shape
    assert out_orig.shape == out_vec.shape, "Shape mismatch mono"
    # Check values (allow for minor float diffs due to einsum vs mean(square))
    np.testing.assert_allclose(out_orig, out_vec, atol=1e-6, err_msg="Mono parity failed")
    print("✅ Mono parity passed")

    # Test stereo
    wav_stereo = np.random.normal(0, 0.1, (2, 48000)).astype(np.float32)
    wav_stereo[0, 500] = 0.9
    wav_stereo[1, 1500] = -0.9

    out_orig_s = apply_declick_original(wav_stereo, sr)
    out_vec_s = AudioPostProcessor.apply_declick(wav_stereo, sr)

    assert out_orig_s.shape == out_vec_s.shape, "Shape mismatch stereo"
    np.testing.assert_allclose(out_orig_s, out_vec_s, atol=1e-6, err_msg="Stereo parity failed")
    print("✅ Stereo parity passed")

    # Test remainder
    wav_rem = np.random.normal(0, 0.1, 100).astype(np.float32) # window is 48
    wav_rem[2] = 0.9 # In first chunk (0-48)
    wav_rem[50] = -0.9 # In second chunk (48-96)
    wav_rem[98] = 0.8 # In remainder (96-100)

    out_orig_r = apply_declick_original(wav_rem, sr)
    out_vec_r = AudioPostProcessor.apply_declick(wav_rem, sr)

    np.testing.assert_allclose(out_orig_r, out_vec_r, atol=1e-6, err_msg="Remainder parity failed")
    print("✅ Remainder parity passed")

if __name__ == "__main__":
    test_parity()
