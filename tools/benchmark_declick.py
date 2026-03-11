import numpy as np
import time

def original_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """Simple heuristic de-clicker: clamps spikes > 10x local RMS."""
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
        print(f"De-click failed: {e}")
        return wav

def optimized_apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
    """Vectorized heuristic de-clicker."""
    try:
        if len(wav.shape) > 1:
            return np.stack([optimized_apply_declick(ch, sr) for ch in wav])

        window = int(sr * 0.002)
        if window < 2: return wav

        n = len(wav)
        num_chunks = n // window
        remainder = n % window

        out = wav.copy()

        if num_chunks > 0:
            chunks = out[:num_chunks*window].reshape(num_chunks, window)
            # Use np.vdot-like approach for RMS to avoid large temp arrays?
            # Actually np.mean(chunks**2, axis=1) is already much faster than a loop.
            # But let's follow Bolt's philosophy of avoiding large temp allocations if possible.
            # chunks**2 is O(N).
            rms = np.sqrt(np.mean(chunks**2, axis=1)) + 1e-6

            # Broadcase RMS for comparison
            thresholds = rms[:, np.newaxis] * 10
            spikes = np.abs(chunks) > thresholds

            if np.any(spikes):
                # Apply clamping
                clamp_values = (rms[:, np.newaxis] * 3).astype(wav.dtype)
                # We need to use the sign of the original values
                signs = np.sign(chunks)
                # Only update where spikes are True
                chunks[spikes] = (signs * clamp_values)[spikes]

        # Handle remainder
        if remainder >= 2:
            chunk = out[num_chunks*window:]
            local_rms = np.sqrt(np.mean(chunk**2)) + 1e-6
            spikes = np.abs(chunk) > (local_rms * 10)
            if np.any(spikes):
                out[num_chunks*window:][spikes] = np.sign(chunk[spikes]) * local_rms * 3

        return out
    except Exception as e:
        print(f"Optimized De-click failed: {e}")
        return wav

def benchmark():
    sr = 24000
    duration = 60 # seconds
    wav = np.random.randn(sr * duration).astype(np.float32) * 0.01
    # Add 100 random spikes
    for _ in range(100):
        idx = np.random.randint(0, len(wav))
        wav[idx] = 1.0

    print(f"Benchmarking with {duration}s audio...")

    start = time.time()
    res1 = original_apply_declick(wav, sr)
    t1 = time.time() - start
    print(f"Original: {t1:.4f}s")

    start = time.time()
    res2 = optimized_apply_declick(wav, sr)
    t2 = time.time() - start
    print(f"Optimized: {t2:.4f}s")

    print(f"Speedup: {t1/t2:.2f}x")

    # Verification
    clamped1 = np.sum(res1 != wav)
    clamped2 = np.sum(res2 != wav)
    print(f"Original clamped {clamped1} samples")
    print(f"Optimized clamped {clamped2} samples")

    np.testing.assert_allclose(res1, res2, atol=1e-6)
    print("Verification passed!")

if __name__ == "__main__":
    benchmark()
