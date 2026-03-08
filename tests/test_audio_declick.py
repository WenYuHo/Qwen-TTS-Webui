import numpy as np
import sys
from pathlib import Path

# Add src to path
ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = str(ROOT_DIR / "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from backend.utils import AudioPostProcessor

def test_audio_post_processor_declick():
    # Use 96000Hz to trigger the "10x local RMS" heuristic
    sr = 96000
    # W = 192.
    wav = np.random.uniform(-0.001, 0.001, sr).astype(np.float32)
    wav[1000] = 0.5  # Spike in main chunks
    wav[5000] = -0.5 # Spike in main chunks

    # Test mono
    out_mono = AudioPostProcessor.apply_declick(wav, sr)
    assert not np.array_equal(wav, out_mono), "Mono should be changed at 96kHz"
    assert np.abs(out_mono[1000]) < 0.5
    assert np.abs(out_mono[5000]) < 0.5

    # Test remainder spike ONLY
    wav_rem = np.random.uniform(-0.001, 0.001, sr).astype(np.float32)
    # Put spike in the last few samples
    window = int(sr * 0.002)
    n_chunks = len(wav_rem) // window
    truncated_len = n_chunks * window
    # Remainder length at 96kHz for 96000 is 0 since 96000 % 192 = 0.
    # Let's adjust duration.
    sr = 44100 # W = 88. 44100 % 88 = 12 samples of remainder.
    wav_rem = np.random.uniform(-0.0001, 0.0001, 44100).astype(np.float32)
    wav_rem[-5] = 0.1 # Spike in remainder
    # Check if this spike triggers 10x RMS for the remainder
    # Remainder RMS approx 0.1 / sqrt(12) = 0.0288. Threshold = 0.288.
    # Ah, need a smaller noise or larger spike for remainder.
    wav_rem = np.random.uniform(-0.00001, 0.00001, 44100).astype(np.float32)
    wav_rem[-5] = 0.01
    # Remainder RMS approx 0.01 / sqrt(12) = 0.00288. Threshold = 0.0288.
    # Still not triggering. Need sqrt(12) > 10 which is False.
    # For remainder to trigger S > 10 * local_rms, we need W_rem > 100.
    # But remainder is by definition < W.
    # If W < 100, then W_rem < 100.
    # So the remainder spike will NEVER trigger at common sample rates either.

    # Let's use 192000Hz. W = 384. Remainder can be up to 383.
    sr = 192000
    # Dur = 1.0s. 192000 samples. 192000 % 384 = 0.
    # Let's use 192000 + 200 samples.
    total_samples = 192000 + 200
    wav_rem = np.random.uniform(-0.00001, 0.00001, total_samples).astype(np.float32)
    wav_rem[-5] = 0.1
    # W_rem = 200. S = 0.1. RMS = sqrt((199 * 1e-10 + 0.01)/200) = 0.007
    # Threshold = 0.07. 0.1 > 0.07. Triggers!

    out_rem = AudioPostProcessor.apply_declick(wav_rem, sr)
    assert not np.array_equal(wav_rem, out_rem), "Remainder spike should be changed"
    assert np.abs(out_rem[-5]) < 0.1

    # Test stereo
    sr = 96000
    wav = np.random.uniform(-0.001, 0.001, sr).astype(np.float32)
    wav[1000] = 0.5
    wav_stereo = np.stack([wav, wav])
    out_stereo = AudioPostProcessor.apply_declick(wav_stereo, sr)
    assert out_stereo.shape == (2, sr)
    assert not np.array_equal(wav_stereo, out_stereo)

    # Test no spikes
    wav_clean = np.zeros(sr, dtype=np.float32)
    out_clean = AudioPostProcessor.apply_declick(wav_clean, sr)
    assert np.array_equal(wav_clean, out_clean)

    # Test small waveform
    wav_small = np.random.uniform(-0.001, 0.001, 10).astype(np.float32)
    out_small = AudioPostProcessor.apply_declick(wav_small, sr)
    assert np.array_equal(wav_small, out_small)
