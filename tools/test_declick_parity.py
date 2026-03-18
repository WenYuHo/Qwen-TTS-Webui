import numpy as np
from backend.utils import AudioPostProcessor

def original_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """Original loop-based implementation for parity checking."""
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

def test_parity():
    # ⚡ Bolt: Use a high sample rate to ensure window size is large enough
    # for single spikes to trigger the 10x RMS heuristic.
    # At 2ms window, sqrt(window) must be > 10. sqrt(121) = 11.
    # 121 samples @ 2ms = 60500 Hz.
    sr = 96000

    # Test cases: mono, stereo, with remainder, small buffer
    test_cases = [
        ("Mono 1s", np.random.randn(sr).astype(np.float32) * 0.01),
        ("Mono with remainder", np.random.randn(sr + 107).astype(np.float32) * 0.01),
        ("Stereo 1s", np.random.randn(2, sr).astype(np.float32) * 0.01),
        ("Small buffer", np.random.randn(10).astype(np.float32) * 0.01),
        ("Zero buffer", np.array([], dtype=np.float32)),
    ]

    for name, wav in test_cases:
        # Add some spikes
        if wav.size > 0:
            # Flatten for easy indexing
            flat_wav = wav.ravel()
            # Ensure we have at least one spike in the main section and one in remainder
            if flat_wav.size > 500:
                flat_wav[100] = 1.0 # Main
                flat_wav[-5] = 1.0  # Remainder
            else:
                flat_wav[min(5, flat_wav.size-1)] = 1.0

        print(f"Testing {name}...")
        expected = original_apply_declick(wav, sr)
        actual = AudioPostProcessor.apply_declick(wav, sr)

        # Check identity
        np.testing.assert_allclose(actual, expected, atol=1e-6, err_msg=f"Parity failed for {name}")

        # Verify that de-clicking actually occurred if there was a spike
        if wav.size > 500:
            assert not np.array_equal(actual, wav), f"De-clicker did not modify signal in {name}"

        print(f"PASSED: {name}")

if __name__ == "__main__":
    try:
        test_parity()
        print("\nAll parity tests passed!")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\nParity test failed: {e}")
        exit(1)
