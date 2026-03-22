import numpy as np
import pytest
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

@pytest.mark.parametrize("sr", [16000, 24000, 44100, 48000])
@pytest.mark.parametrize("duration", [0.1, 0.5])
@pytest.mark.parametrize("channels", [1, 2])
def test_declick_parity(sr, duration, channels):
    # Create test signal
    num_samples = int(sr * duration)
    if channels == 1:
        wav = np.random.uniform(-0.1, 0.1, num_samples).astype(np.float32)
        # Add some spikes
        wav[::sr//10] = 0.9
    else:
        wav = np.random.uniform(-0.1, 0.1, (channels, num_samples)).astype(np.float32)
        # Add some spikes
        wav[0, ::sr//10] = 0.9
        wav[1, 1::sr//10] = -0.9

    # Original
    expected = original_apply_declick(wav, sr)

    # Optimized (currently same as original)
    actual = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_allclose(actual, expected, atol=1e-7)

def test_declick_small_buffer():
    sr = 24000
    wav = np.array([0.1, 0.9, 0.1], dtype=np.float32)
    # Window will be 48 samples, but wav is only 3.
    # Original should return it unchanged as window is processed only if it contains enough samples.
    # Wait, the original loop: for i in range(0, len(wav), window): chunk = wav[i:i+window]
    # If len(wav) < window, it only runs once with a short chunk.
    # original_apply_declick has: if len(chunk) < 2: continue

    expected = original_apply_declick(wav, sr)
    actual = AudioPostProcessor.apply_declick(wav, sr)
    np.testing.assert_allclose(actual, expected, atol=1e-7)

def test_declick_remainder():
    sr = 24000
    window = int(sr * 0.002)
    # 2.5 windows
    wav = np.random.uniform(-0.1, 0.1, int(window * 2.5)).astype(np.float32)
    wav[int(window * 2.2)] = 0.9 # Spike in the remainder

    expected = original_apply_declick(wav, sr)
    actual = AudioPostProcessor.apply_declick(wav, sr)
    np.testing.assert_allclose(actual, expected, atol=1e-7)
