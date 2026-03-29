import numpy as np
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from backend.utils import AudioPostProcessor

def test_declick_parity():
    sr = 44100
    duration_sec = 1
    n_samples = duration_sec * sr
    wav = np.random.normal(0, 0.1, n_samples).astype(np.float32)

    # Add some spikes
    wav[n_samples // 10] = 1.0
    wav[n_samples // 2] = -1.0

    # Original implementation (re-implemented here for comparison)
    def original_apply_declick(wav, sr):
        out = wav.copy()
        window = int(sr * 0.002) # 2ms
        if window < 2: return wav
        for i in range(0, len(wav), window):
            chunk = wav[i:i+window]
            if len(chunk) < 2: continue
            local_rms = np.sqrt(np.mean(chunk**2)) + 1e-6
            spikes = np.abs(chunk) > (local_rms * 10)
            if np.any(spikes):
                sign = np.sign(chunk[spikes])
                out[i:i+window][spikes] = sign * local_rms * 3
        return out

    expected = original_apply_declick(wav, sr)
    actual = AudioPostProcessor.apply_declick(wav, sr)

    np.testing.assert_allclose(actual, expected, atol=1e-7)
    print("Parity check passed!")

if __name__ == "__main__":
    test_declick_parity()
