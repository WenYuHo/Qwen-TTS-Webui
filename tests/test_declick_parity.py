import numpy as np
import pytest
import sys
import os

# Add src to path for imports
sys.path.append(os.path.abspath("src"))
from backend.utils import AudioPostProcessor

def original_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """The original loop-based implementation."""
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
    except Exception as e:
        return wav

def test_declick_parity():
    sr = 24000
    durations = [0.01, 0.05, 0.1, 1.0] # seconds

    for dur in durations:
        n_samples = int(dur * sr)
        # Random noise
        wav = np.random.normal(0, 0.1, n_samples).astype(np.float32)

        # Add some spikes
        n_spikes = max(1, n_samples // 100)
        spike_indices = np.random.choice(n_samples, n_spikes, replace=False)
        wav[spike_indices] = np.random.choice([-1.0, 1.0], n_spikes) * 0.9

        # Test mono
        expected = original_apply_declick(wav, sr)
        actual = AudioPostProcessor.apply_declick(wav, sr)

        np.testing.assert_allclose(actual, expected, atol=1e-7, err_msg=f"Mono parity failed for duration {dur}")

        # Test stereo
        wav_stereo = np.stack([wav, wav[::-1].copy()])
        expected_stereo = original_apply_declick(wav_stereo, sr)
        actual_stereo = AudioPostProcessor.apply_declick(wav_stereo, sr)

        np.testing.assert_allclose(actual_stereo, expected_stereo, atol=1e-7, err_msg=f"Stereo parity failed for duration {dur}")

def test_declick_edge_cases():
    sr = 24000

    # Very small buffer
    wav = np.zeros(10, dtype=np.float32)
    expected = original_apply_declick(wav, sr)
    actual = AudioPostProcessor.apply_declick(wav, sr)
    np.testing.assert_allclose(actual, expected, atol=1e-7)

    # Buffer that is not a multiple of window size
    window = int(sr * 0.002)
    n_samples = window * 5 + window // 2
    wav = np.random.normal(0, 0.1, n_samples).astype(np.float32)
    wav[n_samples - 2] = 1.0 # Spike in the remainder

    expected = original_apply_declick(wav, sr)
    actual = AudioPostProcessor.apply_declick(wav, sr)
    np.testing.assert_allclose(actual, expected, atol=1e-7, err_msg="Remainder parity failed")

if __name__ == "__main__":
    test_declick_parity()
    test_declick_edge_cases()
    print("All parity tests passed!")
