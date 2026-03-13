import numpy as np
import time
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

def apply_declick_original(wav: np.ndarray, sr: int) -> np.ndarray:
    """Original loop-based implementation."""
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
    except Exception:
        return wav

def apply_declick_vectorized(wav: np.ndarray, sr: int) -> np.ndarray:
    """New vectorized implementation."""
    try:
        if len(wav.shape) > 1:
            # Recursively handle multi-channel audio
            return np.stack([apply_declick_vectorized(ch, sr) for ch in wav])

        window = int(sr * 0.002)  # 2ms
        if window < 2 or len(wav) < window:
            return wav.copy()

        # Vectorized chunk processing
        n_chunks = len(wav) // window
        wav_trimmed = wav[:n_chunks * window]
        remainder = wav[n_chunks * window:]

        chunks = wav_trimmed.reshape(n_chunks, window)
        # Use einsum for efficient sum of squares across chunks
        chunk_rms = np.sqrt(np.einsum('ij,ij->i', chunks, chunks) / window) + 1e-6

        # Broadcast RMS back to chunk shape
        rms_expanded = chunk_rms[:, np.newaxis]
        spikes = np.abs(chunks) > (rms_expanded * 10)

        if np.any(spikes):
            out_chunks = chunks.copy()
            # Need to broadcast rms_expanded to use fancy indexing with spikes mask
            rms_full = np.broadcast_to(rms_expanded, chunks.shape)
            out_chunks[spikes] = np.sign(chunks[spikes]) * rms_full[spikes] * 3
            out_wav = out_chunks.ravel()
        else:
            out_wav = wav_trimmed.copy()

        if len(remainder) >= 2:
            rem_rms = np.sqrt(np.vdot(remainder, remainder) / len(remainder)) + 1e-6
            rem_spikes = np.abs(remainder) > (rem_rms * 10)
            if np.any(rem_spikes):
                rem_out = remainder.copy()
                rem_out[rem_spikes] = np.sign(remainder[rem_spikes]) * rem_rms * 3
                return np.concatenate([out_wav, rem_out])

        if len(remainder) > 0:
            return np.concatenate([out_wav, remainder])

        return out_wav
    except Exception:
        return wav

def benchmark():
    sr = 24000 # Standard SR
    duration = 300 # 5 minutes

    print(f"Creating test signal: {duration}s at {sr}Hz...")
    wav = np.random.uniform(-0.1, 0.1, sr * duration).astype(np.float32)
    # Add 1000 random spikes
    num_spikes = 1000
    spike_indices = np.random.choice(len(wav), num_spikes, replace=False)
    wav[spike_indices] = 1.0

    # 1. Benchmark Original
    print("Running original implementation...")
    start = time.time()
    out_orig = apply_declick_original(wav, sr)
    time_orig = time.time() - start
    print(f"Original took: {time_orig:.4f}s")

    # 2. Benchmark Vectorized
    print("Running vectorized implementation...")
    start = time.time()
    out_vec = apply_declick_vectorized(wav, sr)
    time_vec = time.time() - start
    print(f"Vectorized took: {time_vec:.4f}s")

    print(f"\nResults:")
    print(f"Speedup: {time_orig / time_vec:.2f}x")

    # Verification
    print(f"Max value after orig: {np.max(np.abs(out_orig)):.4f}")
    print(f"Max value after vec: {np.max(np.abs(out_vec)):.4f}")

    is_all_close = np.allclose(out_orig, out_vec, atol=1e-6)
    print(f"Are results identical (allclose)? {is_all_close}")

    # Check for stereo
    print("\nTesting stereo support...")
    stereo_wav = np.stack([wav, wav])
    start = time.time()
    out_stereo = apply_declick_vectorized(stereo_wav, sr)
    time_stereo = time.time() - start
    print(f"Stereo (vectorized) took: {time_stereo:.4f}s")
    assert out_stereo.shape == (2, len(wav))

if __name__ == "__main__":
    benchmark()
