import numpy as np
import sys
import os

# Add src to path
sys.path.append(os.path.abspath("src"))

from backend.utils import AudioPostProcessor

def original_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """Original loop-based de-clicker logic for parity testing."""
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

def test_parity():
    sr = 24000
    # Test cases
    test_configs = [
        ("Mono Small", np.random.uniform(-0.1, 0.1, 1000).astype(np.float32)),
        ("Mono Large", np.random.uniform(-0.1, 0.1, 24000).astype(np.float32)),
        ("Stereo", np.random.uniform(-0.1, 0.1, (2, 24000)).astype(np.float32)),
        ("With Clicks", None) # Special case
    ]

    # Generate clicks for the special case
    wav_clicks = np.random.uniform(-0.1, 0.1, 24000).astype(np.float32)
    indices = np.random.randint(0, len(wav_clicks), 50)
    wav_clicks[indices] = np.random.uniform(0.8, 1.0, 50) * np.sign(np.random.uniform(-1, 1, 50))
    test_configs[3] = ("With Clicks", wav_clicks)

    for name, wav in test_configs:
        print(f"Testing parity for: {name}")
        expected = original_apply_declick(wav, sr)
        actual = AudioPostProcessor.apply_declick(wav, sr)

        # Check if identical
        np.testing.assert_allclose(actual, expected, rtol=1e-5, atol=1e-7, err_msg=f"Parity failed for {name}")
        print(f"  ✅ {name} passed parity check.")

if __name__ == "__main__":
    try:
        test_parity()
        print("\nAll parity tests passed!")
    except Exception as e:
        print(f"\n❌ Parity test failed: {e}")
        sys.exit(1)
