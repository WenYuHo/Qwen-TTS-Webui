import numpy as np
import sys
import os

# Add src to path
sys.path.append(os.path.abspath("src"))

from backend.utils import AudioPostProcessor

def original_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """Original loop-based implementation."""
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

def test_parity():
    sr = 24000
    test_cases = [
        # Mono, small
        np.random.uniform(-0.5, 0.5, 100).astype(np.float32),
        # Mono, exact window multiple
        np.random.uniform(-0.5, 0.5, int(sr * 0.002 * 10)).astype(np.float32),
        # Mono, with remainder
        np.random.uniform(-0.5, 0.5, int(sr * 0.002 * 10.5)).astype(np.float32),
        # Stereo
        np.random.uniform(-0.5, 0.5, (2, 1000)).astype(np.float32),
    ]

    # Add cases with spikes
    for case in list(test_cases):
        with_spikes = case.copy()
        if len(with_spikes.shape) == 1:
            if len(with_spikes) > 0:
                indices = np.random.randint(0, len(with_spikes), min(len(with_spikes), 5))
                with_spikes[indices] = 1.0 * np.sign(np.random.uniform(-1, 1, len(indices)))
        else:
            if with_spikes.shape[1] > 0:
                indices = np.random.randint(0, with_spikes.shape[1], min(with_spikes.shape[1], 5))
                with_spikes[:, indices] = 1.0 * np.sign(np.random.uniform(-1, 1, len(indices)))
        test_cases.append(with_spikes)

    success = True
    for i, wav in enumerate(test_cases):
        orig = original_apply_declick(wav, sr)
        opt = AudioPostProcessor.apply_declick(wav, sr)

        parity = np.allclose(orig, opt, atol=1e-7)
        print(f"Test case {i}: {'PASS' if parity else 'FAIL'} (shape: {wav.shape})")
        if not parity:
            diff = np.abs(orig - opt)
            print(f"Max diff: {np.max(diff)}")
            success = False

    if success:
        print("\nAll parity tests PASSED!")
    else:
        print("\nSome parity tests FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    test_parity()
