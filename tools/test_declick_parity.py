import numpy as np
import logging

# Mock logger
logger = logging.getLogger("studio")

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
    except Exception as e:
        return wav

def test_parity():
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent / "src"))
    from backend.utils import AudioPostProcessor

    sr = 24000
    # Create test signal with deliberate clicks
    wav = np.random.randn(sr * 5).astype(np.float32) * 0.1
    # Add clicks in both main and remainder parts
    wav[100] = 5.0
    wav[5000] = -4.0
    wav[-1] = 6.0 # Remainder spike

    # Also test stereo
    stereo_wav = np.stack([wav, wav[::-1]])

    print("Testing parity for mono signal...")
    out_old = original_apply_declick(wav, sr)
    out_new = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_allclose(out_old, out_new, rtol=1e-5, atol=1e-5)
    print("✅ Mono parity passed!")

    print("Testing parity for stereo signal...")
    out_old_s = original_apply_declick(stereo_wav, sr)
    out_new_s = AudioPostProcessor.apply_declick(stereo_wav, sr)

    np.testing.assert_allclose(out_old_s, out_new_s, rtol=1e-5, atol=1e-5)
    print("✅ Stereo parity passed!")

    # Test edge case: small buffer
    print("Testing small buffer...")
    small = np.array([1.0, 0.0, 5.0], dtype=np.float32)
    out_small_old = original_apply_declick(small, sr)
    out_small_new = AudioPostProcessor.apply_declick(small, sr)
    np.testing.assert_allclose(out_small_old, out_small_new)
    print("✅ Small buffer parity passed!")

if __name__ == "__main__":
    test_parity()
