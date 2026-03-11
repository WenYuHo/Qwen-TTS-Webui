import numpy as np
import time
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))

from backend.utils import AudioPostProcessor

def original_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """The original loop-based implementation."""
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

def benchmark():
    sr = 24000
    duration_sec = 300 # 5 minutes
    wav = np.random.uniform(-0.1, 0.1, sr * duration_sec).astype(np.float32)

    # Add some spikes
    for _ in range(500):
        idx = np.random.randint(0, len(wav))
        wav[idx] = 1.0

    print(f"Benchmarking with {duration_sec}s audio ({len(wav)} samples)...")

    print("Running original implementation...")
    start = time.time()
    _ = original_apply_declick(wav, sr)
    end = time.time()
    orig_time = end - start
    print(f"Original Time: {orig_time:.4f}s")

    print("Running optimized implementation...")
    start = time.time()
    _ = AudioPostProcessor.apply_declick(wav, sr)
    end = time.time()
    opt_time = end - start
    print(f"Optimized Time: {opt_time:.4f}s")

    print(f"Speedup: {orig_time / opt_time:.2f}x")

if __name__ == "__main__":
    benchmark()
