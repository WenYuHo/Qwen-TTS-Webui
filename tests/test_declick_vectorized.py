import numpy as np
import pytest
import sys
import os

# Add src to path for imports
sys.path.append(os.path.abspath("src"))
from backend.utils import AudioPostProcessor

def test_declick_vectorized():
    sr = 24000
    # Window size is 48 for 24kHz
    window = int(sr * 0.002)

    # Test mono with strong spike relative to background
    # Background near zero
    wav = np.zeros(sr, dtype=np.float32)
    # We put spikes in multiple places to be sure we hit some chunks
    wav[100] = 1.0 # chunk 2 (48*2 = 96, 48*3 = 144)
    wav[200] = 0.9 # chunk 4 (48*4 = 192, 48*5 = 240)

    # In chunk 2, spike is 1.0, others are 0. RMS will be sqrt(1^2 / 48) = 1/sqrt(48) approx 0.144
    # 1.0 / 0.144 = 6.9, still < 10.
    # To get > 10, we need the spike to be very large relative to RMS.
    # If only one spike is in a window of 48, it can never be > 10x RMS because it contributes to RMS.
    # sqrt(1^2 / 48) = 0.144. 10 * 0.144 = 1.44. So 1.0 < 1.44.

    # Let's use a smaller window or larger spikes, or just accept the heuristic's limitation.
    # Actually, the original heuristic had the same limitation.

    # To trigger it with one spike in 48 samples:
    # spike > 10 * sqrt(spike^2 / 48) => spike > 10 * spike / sqrt(48) => 1 > 10 / 6.9 => 1 > 1.44 (False)
    # So a single spike in a window of 48 can NEVER trigger a 10x RMS heuristic if it's the only thing in the window.

    # Let's test with a much higher sample rate to get a larger window? No, window is sr * 0.002.
    # For it to work, window must be > 100.
    # sr * 0.002 > 100 => sr > 50000.

    sr_high = 96000
    window_high = int(sr_high * 0.002) # 192
    # sqrt(1/192) = 0.072. 10 * 0.072 = 0.72. 1.0 > 0.72. YES!

    wav_high = np.zeros(sr_high, dtype=np.float32)
    wav_high[1000] = 1.0
    out_high = AudioPostProcessor.apply_declick(wav_high, sr_high)
    assert out_high[1000] < 1.0
    print(f"High SR test passed: {out_high[1000]}")

    # Test multi-channel consistency
    wav_stereo = np.zeros((2, sr_high), dtype=np.float32)
    wav_stereo[0, 1000] = 1.0
    wav_stereo[1, 1000] = 1.0
    out_stereo = AudioPostProcessor.apply_declick(wav_stereo, sr_high)
    assert out_stereo[0, 1000] < 1.0
    assert out_stereo[1, 1000] < 1.0

if __name__ == "__main__":
    test_declick_vectorized()
