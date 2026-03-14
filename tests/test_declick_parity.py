import numpy as np
from backend.utils import AudioPostProcessor

class OriginalProcessor:
    @staticmethod
    def apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
        try:
            if len(wav.shape) > 1:
                out = np.zeros_like(wav)
                for i in range(wav.shape[0]):
                    out[i] = OriginalProcessor.apply_declick(wav[i], sr)
                return out
            out = wav.copy()
            window = int(sr * 0.002)
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
        except Exception:
            return wav

def test_declick_parity_random():
    sr = 24000
    wav = np.random.uniform(-1, 1, 100000).astype(np.float32)
    out_orig = OriginalProcessor.apply_declick(wav, sr)
    out_opt = AudioPostProcessor.apply_declick(wav, sr)
    assert np.allclose(out_orig, out_opt)

def test_declick_parity_stereo():
    sr = 24000
    wav = np.random.uniform(-1, 1, (2, 100000)).astype(np.float32)
    out_orig = OriginalProcessor.apply_declick(wav, sr)
    out_opt = AudioPostProcessor.apply_declick(wav, sr)
    assert np.allclose(out_orig, out_opt)

def test_declick_parity_with_spikes():
    sr = 24000
    wav = np.random.uniform(-0.1, 0.1, 100000).astype(np.float32)
    # Inject 100 spikes
    for _ in range(100):
        idx = np.random.randint(0, 100000)
        wav[idx] = np.random.choice([-1.0, 1.0]) * 0.9

    out_orig = OriginalProcessor.apply_declick(wav, sr)
    out_opt = AudioPostProcessor.apply_declick(wav, sr)

    # Check if any spikes were actually removed
    diff_from_orig_wav = np.abs(wav - out_opt)
    if np.any(diff_from_orig_wav > 0):
        print("Spikes were removed!")
    else:
        print("No spikes were removed - check heuristic parameters.")

    assert np.allclose(out_orig, out_opt)
