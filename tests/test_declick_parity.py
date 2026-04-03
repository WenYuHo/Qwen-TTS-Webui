import numpy as np
import sys
import os

# Add src to path for imports
sys.path.append(os.path.abspath("src"))
from backend.utils import AudioPostProcessor

def original_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """Original loop-based implementation for parity checking."""
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
    sr = 24000
    duration = 1.0
    n_samples = int(sr * duration)

    # Test with random audio and some forced spikes
    np.random.seed(42)
    wav = np.random.normal(0, 0.1, n_samples).astype(np.float32)

    # Add some spikes
    wav[1000] = 0.9
    wav[5000] = -0.8
    wav[10000:10005] = 0.9 # multiple spikes in a window

    expected = original_apply_declick(wav, sr)
    actual = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_allclose(actual, expected, atol=1e-6)
    print("Parity test passed!")

if __name__ == "__main__":
    try:
        test_declick_parity()
    except Exception as e:
        print(f"Parity test failed: {e}")
        sys.exit(1)
