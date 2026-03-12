import numpy as np
import time

def apply_declick_original(wav: np.ndarray, sr: int) -> np.ndarray:
    """Simple heuristic de-clicker: clamps spikes > 10x local RMS. (Original Loop Version)"""
    try:
        if len(wav.shape) > 1:
            out = np.zeros_like(wav)
            for i in range(wav.shape[0]):
                out[i] = apply_declick_original(wav[i], sr)
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

def apply_declick_vectorized(wav: np.ndarray, sr: int) -> np.ndarray:
    """Vectorized version of the de-clicker."""
    try:
        if len(wav.shape) > 1:
            return np.stack([apply_declick_vectorized(ch, sr) for ch in wav])

        window = int(sr * 0.002) # 2ms
        if window < 2 or len(wav) < window:
            return wav.copy()

        num_chunks = len(wav) // window
        remainder = len(wav) % window

        chunks = wav[:num_chunks * window].reshape(num_chunks, window)

        # ⚡ Bolt: Use np.einsum for fast sum of squares across chunks
        sq_sum = np.einsum('ij,ij->i', chunks, chunks)
        rms = np.sqrt(sq_sum / window) + 1e-6

        thresholds = rms[:, None] * 10
        spikes = np.abs(chunks) > thresholds

        out_chunks = chunks.copy()
        if np.any(spikes):
            clamp_values = (rms[:, None] * 3)
            out_chunks[spikes] = np.sign(chunks[spikes]) * np.broadcast_to(clamp_values, chunks.shape)[spikes]

        if remainder > 0:
            rem_chunk = wav[-remainder:]
            rem_rms = np.sqrt(np.mean(rem_chunk**2)) + 1e-6
            rem_spikes = np.abs(rem_chunk) > (rem_rms * 10)
            if np.any(rem_spikes):
                rem_chunk = rem_chunk.copy()
                rem_chunk[rem_spikes] = np.sign(rem_chunk[rem_spikes]) * rem_rms * 3
            return np.concatenate([out_chunks.flatten(), rem_chunk])
        else:
            return out_chunks.flatten()

    except Exception as e:
        print(f"Vectorized de-click failed: {e}")
        return wav

def run_benchmark():
    sr = 24000
    duration = 60 # 60 seconds
    wav = np.random.randn(sr * duration).astype(np.float32) * 0.1
    # Add some clicks
    clicks = np.random.randint(0, len(wav), 1000)
    wav[clicks] *= 50

    # We read the source file content to verify it's there
    with open("src/backend/utils/__init__.py", "r") as f:
        content = f.read()
        if "np.einsum('ij,ij->i', chunks, chunks)" in content:
            print("SOURCE VERIFICATION: Vectorized implementation found in src/backend/utils/__init__.py")
        else:
            print("SOURCE VERIFICATION FAILURE: Vectorized implementation NOT found in src/backend/utils/__init__.py")
            return

    print(f"Benchmarking de-click logic on {duration}s of audio at {sr}Hz...")

    start = time.time()
    res_orig = apply_declick_original(wav, sr)
    end = time.time()
    time_orig = end - start
    print(f"Original (Loop) time: {time_orig:.4f}s")

    start = time.time()
    res_vec = apply_declick_vectorized(wav, sr)
    end = time.time()
    time_vec = end - start
    print(f"Vectorized time: {time_vec:.4f}s")

    print(f"Speedup: {time_orig / time_vec:.2f}x")

    if np.allclose(res_orig, res_vec):
        print("VERIFICATION SUCCESS: Results are identical.")
    else:
        diff = np.abs(res_orig - res_vec)
        print(f"VERIFICATION FAILURE: Max difference {np.max(diff)}")

if __name__ == "__main__":
    run_benchmark()
