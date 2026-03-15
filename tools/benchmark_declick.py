import numpy as np
import time
import sys
import os

# Add src to path
sys.path.append(os.path.abspath("src"))

from backend.utils import AudioPostProcessor

def original_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """Original loop-based implementation (re-implemented here for benchmarking if already changed in src)."""
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

def benchmark_declick():
    sr = 24000
    # 60 seconds of audio
    wav = np.random.uniform(-0.1, 0.1, sr * 60).astype(np.float32)
    # Add some spikes
    for i in range(100):
        wav[np.random.randint(0, len(wav))] *= 20

    print(f"Benchmarking apply_declick with {len(wav)} samples ({len(wav)/sr:.1f}s)...")

    # Baseline
    start = time.time()
    _ = original_apply_declick(wav, sr)
    baseline_time = time.time() - start
    print(f"Baseline (Loop) time: {baseline_time:.4f}s")

    # Current implementation in src
    start = time.time()
    _ = AudioPostProcessor.apply_declick(wav, sr)
    current_time = time.time() - start
    print(f"Current (in src) time: {current_time:.4f}s")

    if baseline_time > 0:
        speedup = baseline_time / current_time if current_time > 0 else float('inf')
        print(f"Speedup vs Baseline: {speedup:.2f}x")

if __name__ == "__main__":
    benchmark_declick()
