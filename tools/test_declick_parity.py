import numpy as np
import sys
import os

# Original loop-based implementation for parity checking
def original_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
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
    # Add src to path
    sys.path.append(os.path.abspath("src"))
    from backend.utils import AudioPostProcessor

    sr = 24000

    # Test cases
    test_cases = [
        ("Mono Small", np.random.uniform(-0.1, 0.1, 1000).astype(np.float32)),
        ("Mono Large", np.random.uniform(-0.1, 0.1, 24000).astype(np.float32)),
        ("Stereo", np.random.uniform(-0.1, 0.1, (2, 5000)).astype(np.float32)),
        ("With Clicks", np.random.uniform(-0.1, 0.1, 1000).astype(np.float32)),
    ]

    # Add a big click to the last one
    test_cases[3][1][500] = 1.0

    for name, wav in test_cases:
        print(f"Testing parity for: {name}")
        orig_out = original_apply_declick(wav, sr)
        new_out = AudioPostProcessor.apply_declick(wav, sr)

        # Check if they are identical
        np.testing.assert_allclose(orig_out, new_out, atol=1e-7, err_msg=f"Parity failed for {name}")
        print(f"  {name} PASSED")

if __name__ == "__main__":
    test_parity()
