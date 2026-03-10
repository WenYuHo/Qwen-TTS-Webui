import numpy as np
import sys
from pathlib import Path

# Ensure src is in path
ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = str(ROOT_DIR / "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from backend.utils import AudioPostProcessor

def original_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """Manual implementation of the original logic for verification."""
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

def verify_identity():
    print("--- Verifying Vectorized apply_declick Identity ---")
    sr = 24000
    # Use a shorter buffer for identity check
    num_samples = sr * 2 # 2 seconds
    wav = np.random.uniform(-0.1, 0.1, num_samples).astype(np.float32)

    # Add spikes
    spike_indices = np.random.randint(0, num_samples, 20)
    for idx in spike_indices:
        wav[idx] = 0.9 * np.random.choice([-1, 1])

    out_orig = original_apply_declick(wav, sr)
    out_vec = AudioPostProcessor.apply_declick(wav, sr)

    # Check shape
    assert out_orig.shape == out_vec.shape, f"Shape mismatch: {out_orig.shape} vs {out_vec.shape}"

    # Check identity
    np.testing.assert_allclose(out_orig, out_vec, atol=1e-6, err_msg="Output mismatch!")
    print("Identity verified (within float precision).")

    # Test stereo
    wav_stereo = np.stack([wav, wav * 0.5])
    out_stereo_orig = original_apply_declick(wav_stereo, sr)
    out_stereo_vec = AudioPostProcessor.apply_declick(wav_stereo, sr)
    np.testing.assert_allclose(out_stereo_orig, out_stereo_vec, atol=1e-6, err_msg="Stereo output mismatch!")
    print("Stereo identity verified.")

if __name__ == "__main__":
    verify_identity()
