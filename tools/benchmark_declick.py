import numpy as np
import time
import sys
import os

# Mock logger for the benchmark
class MockLogger:
    def error(self, msg):
        print(f"ERROR: {msg}")

logger = MockLogger()

class OriginalProcessor:
    @staticmethod
    def apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
        """Original loop-based de-clicker."""
        try:
            if len(wav.shape) > 1:
                out = np.zeros_like(wav)
                for i in range(wav.shape[0]):
                    out[i] = OriginalProcessor.apply_declick(wav[i], sr)
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
            logger.error(f"De-click failed: {e}")
            return wav

class OptimizedProcessor:
    @staticmethod
    def apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
        """Proposed vectorized de-clicker."""
        try:
            if len(wav.shape) > 1:
                # ⚡ Bolt: Vectorized multi-channel handling via list comprehension + np.array
                # This maintains parity with the original's recursive behavior but is slightly more idiomatic.
                return np.array([OptimizedProcessor.apply_declick(ch, sr) for ch in wav])

            window = int(sr * 0.002)
            if window < 2 or len(wav) < window:
                return wav.copy()

            # 1. Main body: Process all full windows at once
            num_full_windows = len(wav) // window
            main_len = num_full_windows * window
            main_part = wav[:main_len].reshape(num_full_windows, window)

            # ⚡ Bolt: Calculate row-wise RMS using einsum to avoid O(N) temporary squares
            # Squared sum of each row (window)
            sq_sums = np.einsum('ij,ij->i', main_part, main_part)
            local_rms = np.sqrt(sq_sums / window) + 1e-6

            # Broadcast RMS to match chunk shape (num_windows, 1)
            rms_vec = local_rms[:, np.newaxis]

            # Identify spikes: |val| > 10 * local_rms
            spikes = np.abs(main_part) > (rms_vec * 10)

            out_main = main_part.copy()
            if np.any(spikes):
                # Clamp spikes to local RMS * 3
                # We broadcast the clamping value across the window
                clamp_vals = rms_vec * 3
                # Fancy indexing with the boolean mask
                out_main[spikes] = np.sign(main_part[spikes]) * np.broadcast_to(clamp_vals, main_part.shape)[spikes]

            out = out_main.ravel() # flatten()

            # 2. Remainder: Process the last few samples that didn't fit a full window
            remainder = wav[main_len:]
            if len(remainder) >= 2:
                rem_rms = np.sqrt(np.mean(remainder**2)) + 1e-6
                rem_spikes = np.abs(remainder) > (rem_rms * 10)
                if np.any(rem_spikes):
                    rem_out = remainder.copy()
                    rem_out[rem_spikes] = np.sign(remainder[rem_spikes]) * rem_rms * 3
                    out = np.concatenate([out, rem_out])
                else:
                    out = np.concatenate([out, remainder])
            elif len(remainder) > 0:
                out = np.concatenate([out, remainder])

            return out
        except Exception as e:
            logger.error(f"Vectorized De-click failed: {e}")
            return wav.copy()

def run_benchmark():
    sr = 24000
    duration_sec = 300 # 5 minutes
    num_samples = sr * duration_sec

    print(f"Generating {duration_sec}s of audio ({num_samples} samples)...")
    # Generate white noise
    wav = np.random.uniform(-0.1, 0.1, num_samples).astype(np.float32)
    # Inject some clicks (spikes)
    num_clicks = 1000
    click_indices = np.random.randint(0, num_samples, num_clicks)
    wav[click_indices] = np.random.uniform(0.8, 1.0, num_clicks) * np.random.choice([-1, 1], num_clicks)

    # Mono Test
    print("\n--- Mono Benchmark ---")
    start = time.time()
    original_out = OriginalProcessor.apply_declick(wav, sr)
    original_time = time.time() - start
    print(f"Original (Loop): {original_time:.4f}s")

    start = time.time()
    optimized_out = OptimizedProcessor.apply_declick(wav, sr)
    optimized_time = time.time() - start
    print(f"Optimized (Vectorized): {optimized_time:.4f}s")
    print(f"Speedup: {original_time / optimized_time:.2f}x")

    # Correctness check
    diff = np.max(np.abs(original_out - optimized_out))
    print(f"Max difference: {diff:.2e}")
    if diff < 1e-7:
        print("✅ Correctness verified (Mono)")
    else:
        print("❌ Correctness failed (Mono)")

    # Stereo Test
    print("\n--- Stereo Benchmark ---")
    wav_stereo = np.stack([wav, wav * 0.5])
    start = time.time()
    original_out_s = OriginalProcessor.apply_declick(wav_stereo, sr)
    original_time_s = time.time() - start
    print(f"Original (Loop): {original_time_s:.4f}s")

    start = time.time()
    optimized_out_s = OptimizedProcessor.apply_declick(wav_stereo, sr)
    optimized_time_s = time.time() - start
    print(f"Optimized (Vectorized): {optimized_time_s:.4f}s")
    print(f"Speedup: {original_time_s / optimized_time_s:.2f}x")

    diff_s = np.max(np.abs(original_out_s - optimized_out_s))
    print(f"Max difference: {diff_s:.2e}")
    if diff_s < 1e-7:
        print("✅ Correctness verified (Stereo)")
    else:
        print("❌ Correctness failed (Stereo)")

    # Remainder Test (audio length not multiple of window)
    print("\n--- Remainder Parity Test ---")
    window = int(sr * 0.002)
    wav_rem = wav[:window * 10 + 5] # 10 full windows + 5 samples
    orig_rem = OriginalProcessor.apply_declick(wav_rem, sr)
    opt_rem = OptimizedProcessor.apply_declick(wav_rem, sr)
    diff_rem = np.max(np.abs(orig_rem - opt_rem))
    print(f"Max difference (Remainder): {diff_rem:.2e}")
    if diff_rem < 1e-7:
        print("✅ Correctness verified (Remainder)")
    else:
        print("❌ Correctness failed (Remainder)")

if __name__ == "__main__":
    run_benchmark()
