import numpy as np
import time
import sys
import os

# Ensure we can import from src
sys.path.append(os.path.abspath("src"))

from backend.utils import AudioPostProcessor

def original_declick(wav, sr):
    try:
        if len(wav.shape) > 1:
            out = np.zeros_like(wav)
            for i in range(wav.shape[0]):
                out[i] = original_declick(wav[i], sr)
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

def vectorized_declick(wav, sr):
    try:
        if len(wav.shape) > 1:
            out = np.zeros_like(wav)
            for i in range(wav.shape[0]):
                out[i] = vectorized_declick(wav[i], sr)
            return out

        window = int(sr * 0.002) # 2ms
        if window < 2 or len(wav) < window:
            return wav.copy()

        n_chunks = len(wav) // window
        main_len = n_chunks * window
        main_part = wav[:main_len].reshape(n_chunks, window)

        # Use einsum for memory efficiency (no temporary chunks**2)
        squared_sum = np.einsum('ij,ij->i', main_part, main_part)
        rms = np.sqrt(squared_sum / window) + 1e-6

        thresholds = rms * 10
        spikes = np.abs(main_part) > thresholds[:, np.newaxis]

        out = wav.copy()
        out_main = out[:main_len].reshape(n_chunks, window)

        if np.any(spikes):
            chunk_indices, sample_indices = np.where(spikes)
            clamp_values = rms[chunk_indices] * 3
            out_main[chunk_indices, sample_indices] = np.sign(out_main[chunk_indices, sample_indices]) * clamp_values

        # Handle remainder
        if main_len < len(wav):
            remainder = wav[main_len:]
            if len(remainder) >= 2:
                rem_rms = np.sqrt(np.vdot(remainder, remainder) / len(remainder)) + 1e-6
                rem_spikes = np.abs(remainder) > (rem_rms * 10)
                if np.any(rem_spikes):
                    out[main_len:][rem_spikes] = np.sign(remainder[rem_spikes]) * rem_rms * 3

        return out
    except Exception:
        return wav.copy()

def benchmark():
    sr = 24000
    duration = 60 # 1 minute
    # Create background noise that is VERY low so spikes are detectable
    wav = np.random.uniform(-0.001, 0.001, sr * duration).astype(np.float32)

    # Add clicks that are clearly > 10x RMS
    # 1 click per chunk to make detection easier
    window = int(sr * 0.002)
    clicks = np.arange(0, len(wav), window)
    wav[clicks] = 0.1

    print(f"Benchmarking with {duration}s of audio at {sr}Hz...")

    start = time.time()
    out1 = original_declick(wav, sr)
    t1 = time.time() - start
    print(f"Original: {t1:.4f}s")

    start = time.time()
    out2 = vectorized_declick(wav, sr)
    t2 = time.time() - start
    print(f"Vectorized: {t2:.4f}s")

    print(f"Speedup: {t1/t2:.2f}x")

    # Parity check
    parity = np.allclose(out1, out2)
    print(f"Mathematical parity: {parity}")
    if not parity:
        diff = np.abs(out1 - out2)
        print(f"Max diff: {np.max(diff)}")

    # Check if clicks were actually removed
    max_after = np.max(np.abs(out2[clicks]))
    print(f"Max click amplitude after: {max_after:.4f} (Original was 0.1)")

if __name__ == "__main__":
    benchmark()
