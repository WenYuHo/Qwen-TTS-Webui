import numpy as np
import time
import sys
import os

# Import the actual implementation
from backend.utils import AudioPostProcessor

def apply_declick_original(wav: np.ndarray, sr: int) -> np.ndarray:
    """Simple heuristic de-clicker: clamps spikes > 10x local RMS."""
    try:
        if len(wav.shape) > 1:
            out = np.zeros_like(wav)
            for i in range(wav.shape[0]):
                out[i] = apply_declick_original(wav[i], sr)
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
        print(f"De-click failed: {e}")
        return wav

def main():
    sr = 24000
    duration = 60 # 60 seconds
    wav = np.random.randn(sr * duration).astype(np.float32)
    # Add some spikes
    wav[1000] = 50.0
    wav[5000] = -40.0

    start = time.time()
    out_orig = apply_declick_original(wav, sr)
    end = time.time()
    print(f"Original de-click (60s mono) took: {end - start:.4f}s")

    start = time.time()
    out_vec = AudioPostProcessor.apply_declick(wav, sr)
    end = time.time()
    print(f"Optimized de-click (60s mono) took: {end - start:.4f}s")

    # Verify identity
    np.testing.assert_allclose(out_orig, out_vec, atol=1e-6)
    print("Verification passed (mono)!")

    # Stereo
    wav_stereo = np.random.randn(2, sr * duration).astype(np.float32)
    wav_stereo[0, 2000] = 100.0
    wav_stereo[1, 3000] = -100.0

    start = time.time()
    out_stereo_orig = apply_declick_original(wav_stereo, sr)
    end = time.time()
    print(f"Original de-click (60s stereo) took: {end - start:.4f}s")

    start = time.time()
    out_stereo_vec = AudioPostProcessor.apply_declick(wav_stereo, sr)
    end = time.time()
    print(f"Optimized de-click (60s stereo) took: {end - start:.4f}s")

    # Verify identity
    np.testing.assert_allclose(out_stereo_orig, out_stereo_vec, atol=1e-6)
    print("Verification passed (stereo)!")

if __name__ == "__main__":
    main()
