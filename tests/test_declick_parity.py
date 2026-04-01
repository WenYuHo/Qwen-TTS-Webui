import numpy as np
import sys
from pathlib import Path

# Add src to path
ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = str(ROOT_DIR / "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from backend.utils import AudioPostProcessor

def original_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """Original loop-based de-clicker for parity testing."""
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

def test_declick_parity():
    sr = 24000
    # Test with various lengths, including non-multiples of window
    lengths = [sr, sr + 1, sr + int(sr*0.002)//2, sr * 2]

    for length in lengths:
        print(f"Testing length: {length}")
        wav = np.random.uniform(-0.1, 0.1, length).astype(np.float32)
        # Add some spikes
        wav[np.random.randint(0, length, 10)] = 1.0
        wav[np.random.randint(0, length, 10)] = -1.0

        expected = original_apply_declick(wav, sr)
        actual = AudioPostProcessor.apply_declick(wav, sr)

        # Check parity
        np.testing.assert_allclose(actual, expected, atol=1e-7, err_msg=f"Failed for length {length}")

if __name__ == "__main__":
    try:
        test_declick_parity()
        print("Parity test passed!")
    except Exception as e:
        print(f"Parity test failed: {e}")
        sys.exit(1)
