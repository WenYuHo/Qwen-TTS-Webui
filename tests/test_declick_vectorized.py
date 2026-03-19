import pytest
import numpy as np
from backend.utils import AudioPostProcessor

def test_declick_vectorized_parity():
    sr = 24000
    lengths = [sr, sr + 1, sr + 47, sr + 48, sr * 2 + 10]

    for length in lengths:
        wav = np.random.randn(length).astype(np.float32) * 0.1
        # Add some spikes
        for _ in range(10):
            idx = np.random.randint(0, length)
            wav[idx] *= 20

        # Original logic for comparison
        expected = wav.copy()
        window = int(sr * 0.002)
        if window >= 2:
            for i in range(0, len(wav), window):
                chunk = wav[i:i+window]
                if len(chunk) < 2: continue
                local_rms = np.sqrt(np.mean(chunk**2)) + 1e-6
                spikes = np.abs(chunk) > (local_rms * 10)
                if np.any(spikes):
                    sign = np.sign(chunk[spikes])
                    expected[i:i+window][spikes] = sign * local_rms * 3

        actual = AudioPostProcessor.apply_declick(wav, sr)
        assert np.allclose(expected, actual, atol=1e-7)

def test_declick_stereo():
    sr = 24000
    length = sr
    # Heuristic: spike > 10x local RMS.
    # For a spike at index 100 in a window of 48 (96..144),
    # if it's the only value, RMS is 5 / sqrt(48) ~ 0.72. 10x RMS is 7.2 > 5. NO CLAMP.
    # So we need it to be more extreme or have a lower 10x threshold.
    # Let's use a very large spike.
    wav_stereo = np.zeros((2, length), dtype=np.float32)
    wav_stereo[0, 100] = 100.0 # Extreme spike

    out = AudioPostProcessor.apply_declick(wav_stereo, sr)
    assert out.shape == (2, length)
    # Spike should be detected: RMS ~ 100 / 6.9 ~ 14.4. 10x RMS ~ 144 > 100. STILL NO?
    # Actually, if only one spike: RMS = sqrt(spike^2 / N) = spike / sqrt(N).
    # spike > 10 * spike / sqrt(N)  => 1 > 10 / sqrt(N) => sqrt(N) > 10 => N > 100.
    # Our window is 48. So a single spike in a silent window CANNOT be detected by this heuristic.
    # This is an interesting finding! The heuristic requires a larger window or a lower threshold.
    # But I should stay faithful to the original logic.

    # Let's test with a window where there is some background noise to lower the relative impact of the spike on RMS,
    # OR use a case where the spike is truly huge but the window is large.
    # Wait, if N=48, sqrt(N) = 6.9.
    # Let's just verify parity with the loop implementation which has the same "flaw".

    # If I use sr=96000, window=192. sqrt(192) ~ 13.8. 13.8 > 10.
    sr_high = 96000
    wav_high = np.zeros(sr_high, dtype=np.float32)
    wav_high[200] = 1.0
    out_high = AudioPostProcessor.apply_declick(wav_high, sr_high)
    assert abs(out_high[200]) < 0.5 # Should be clamped
