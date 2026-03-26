import numpy as np
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.append(os.path.abspath("src"))
from backend.utils import AudioPostProcessor

def original_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """Original implementation of de-clicker for parity testing."""
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
    print("Running de-click parity tests...")
    sr = 24000
    durations = [0.1, 1.0, 5.0]

    for dur in durations:
        n_samples = int(dur * sr)
        wav = np.random.normal(0, 0.1, n_samples).astype(np.float32)

        # Add some spikes
        n_spikes = int(dur * 100)
        spike_indices = np.random.choice(n_samples, n_spikes, replace=False)
        wav[spike_indices] = np.random.choice([-1.0, 1.0], n_spikes) * 0.9

        out_orig = original_apply_declick(wav, sr)
        out_optimized = AudioPostProcessor.apply_declick(wav, sr)

        # Check parity
        np.testing.assert_allclose(out_orig, out_optimized, atol=1e-6, err_msg=f"Parity failed for duration {dur}s")
        print(f"  - Duration {dur}s: PASS")

    # Test stereo
    wav_stereo = np.random.normal(0, 0.1, (2, sr)).astype(np.float32)
    wav_stereo[:, 100] = 0.9
    out_orig_stereo = original_apply_declick(wav_stereo, sr)
    out_optimized_stereo = AudioPostProcessor.apply_declick(wav_stereo, sr)
    np.testing.assert_allclose(out_orig_stereo, out_optimized_stereo, atol=1e-6, err_msg="Parity failed for stereo")
    print("  - Stereo: PASS")

    # Test small buffer
    wav_small = np.random.normal(0, 0.1, 10).astype(np.float32)
    out_orig_small = original_apply_declick(wav_small, sr)
    out_optimized_small = AudioPostProcessor.apply_declick(wav_small, sr)
    np.testing.assert_allclose(out_orig_small, out_optimized_small, atol=1e-6, err_msg="Parity failed for small buffer")
    print("  - Small buffer: PASS")

if __name__ == "__main__":
    test_declick_parity()
