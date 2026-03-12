import numpy as np
import time
import sys
import os

# Add src to path
sys.path.append(os.path.abspath("src"))

from backend.utils import AudioPostProcessor

def original_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """The original loop-based implementation."""
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

def main():
    sr = 24000
    # 5 minutes of audio
    duration = 300
    num_samples = sr * duration
    wav = np.random.uniform(-0.5, 0.5, num_samples).astype(np.float32)

    # Add some clicks
    for _ in range(100):
        pos = np.random.randint(0, num_samples)
        wav[pos] = 0.9 if np.random.random() > 0.5 else -0.9

    print(f"Benchmarking with {duration}s of audio ({num_samples} samples) at {sr}Hz")

    start = time.time()
    _ = original_apply_declick(wav, sr)
    end = time.time()
    print(f"Original (loop-based) took: {end - start:.4f}s")

    # Current implementation in utils
    start = time.time()
    _ = AudioPostProcessor.apply_declick(wav, sr)
    end = time.time()
    print(f"Current AudioPostProcessor.apply_declick took: {end - start:.4f}s")

if __name__ == "__main__":
    main()
