import numpy as np
import sys
import os

# Add src to path for imports
sys.path.append(os.path.abspath("src"))
from backend.utils import AudioPostProcessor

def reference_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """Original loop-based implementation for parity checking."""
    if len(wav.shape) > 1:
        out = np.zeros_like(wav)
        for i in range(wav.shape[0]):
            out[i] = reference_apply_declick(wav[i], sr)
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
    durations = [0.1, 0.5, 1.0, 2.3] # Including non-integer multiples of window

    for sr in srs:
        for duration in durations:
            print(f"Testing SR={sr}, duration={duration}s...")
            n_samples = int(duration * sr)
            wav = np.random.normal(0, 0.1, n_samples).astype(np.float32)

            # Add some spikes
            spike_indices = np.random.choice(n_samples, min(n_samples, 20), replace=False)
            wav[spike_indices] = np.random.choice([-1.0, 1.0], len(spike_indices)) * 0.9

            ref_out = reference_apply_declick(wav, sr)
            vec_out = AudioPostProcessor.apply_declick(wav, sr)

            # Check shape and values
            assert ref_out.shape == vec_out.shape, f"Shape mismatch: {ref_out.shape} vs {vec_out.shape}"
            np.testing.assert_allclose(ref_out, vec_out, rtol=1e-5, atol=1e-7, err_msg=f"Parity failed for SR={sr}, duration={duration}s")

    # Test multi-channel
    print("Testing multi-channel (stereo)...")
    sr = 24000
    wav_stereo = np.random.normal(0, 0.1, (2, 24000)).astype(np.float32)
    ref_stereo = reference_apply_declick(wav_stereo, sr)
    vec_stereo = AudioPostProcessor.apply_declick(wav_stereo, sr)
    np.testing.assert_allclose(ref_stereo, vec_stereo, rtol=1e-5, atol=1e-7)

    print("✅ All parity tests passed!")

if __name__ == "__main__":
    test_parity()
