import pytest
import numpy as np
from backend.utils import AudioPostProcessor

def original_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """Original loop-based implementation for parity testing."""
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

def test_declick_parity():
    sr = 96000 # 192 samples per window
    duration = 0.5 # half second

    # Test 1: Clean audio (should be identical)
    clean_wav = np.sin(2 * np.pi * 440 * np.linspace(0, duration, int(sr * duration))).astype(np.float32) * 0.1
    orig_clean = original_apply_declick(clean_wav, sr)
    opt_clean = AudioPostProcessor.apply_declick(clean_wav, sr)
    np.testing.assert_allclose(orig_clean, opt_clean, atol=1e-7)

    # Test 2: Audio with spikes
    spiky_wav = clean_wav.copy()
    spiky_wav[100] = 1.0 # Huge spike relative to sine wave RMS (~0.07)
    spiky_wav[2000] = -1.0
    orig_spiky = original_apply_declick(spiky_wav, sr)
    opt_spiky = AudioPostProcessor.apply_declick(spiky_wav, sr)

    assert not np.array_equal(spiky_wav, orig_spiky), "Original code did not catch the spikes!"
    np.testing.assert_allclose(orig_spiky, opt_spiky, atol=1e-7)

    # Test 3: Stereo audio
    stereo_spiky = np.stack([spiky_wav, spiky_wav])
    orig_stereo = original_apply_declick(stereo_spiky, sr)
    opt_stereo = AudioPostProcessor.apply_declick(stereo_spiky, sr)
    np.testing.assert_allclose(orig_stereo, opt_stereo, atol=1e-7)

    # Test 4: Remainder handling (tail of the signal)
    # A tail of 101 samples is enough for the spike detection heuristic at 96kHz.
    window = int(sr * 0.002) # 192
    short_wav = np.zeros(window * 2 + 101).astype(np.float32)
    short_wav[window*2 + 50] = 1.0 # Spike in the tail

    orig_short = original_apply_declick(short_wav, sr)
    opt_short = AudioPostProcessor.apply_declick(short_wav, sr)

    assert not np.array_equal(short_wav, orig_short), "Original code did not catch the tail spike!"
    np.testing.assert_allclose(orig_short, opt_short, atol=1e-7)

if __name__ == "__main__":
    test_declick_parity()
