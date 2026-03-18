import numpy as np
import time
import timeit

def rms_original(wav):
    return np.sqrt(np.mean(wav ** 2))

def rms_optimized(wav):
    return np.sqrt(np.vdot(wav, wav) / wav.size)

def peak_original(wav):
    return np.max(np.abs(wav))

def peak_optimized(wav):
    return max(np.max(wav), -np.min(wav))

# Create a large audio buffer (10 minutes at 24kHz)
sr = 24000
duration = 600
wav = np.random.uniform(-1, 1, sr * duration)

print(f"Buffer size: {wav.size / 1e6:.2f}M samples")

# Benchmark RMS
n_runs = 100
t_rms_orig = timeit.timeit(lambda: rms_original(wav), number=n_runs)
t_rms_opt = timeit.timeit(lambda: rms_optimized(wav), number=n_runs)

print(f"RMS Original: {t_rms_orig/n_runs*1000:.4f} ms")
print(f"RMS Optimized: {t_rms_opt/n_runs*1000:.4f} ms")
print(f"RMS Speedup: {t_rms_orig / t_rms_opt:.2f}x")

# Benchmark Peak
t_peak_orig = timeit.timeit(lambda: peak_original(wav), number=n_runs)
t_peak_opt = timeit.timeit(lambda: peak_optimized(wav), number=n_runs)

print(f"Peak Original: {t_peak_orig/n_runs*1000:.4f} ms")
print(f"Peak Optimized: {t_peak_opt/n_runs*1000:.4f} ms")
print(f"Peak Speedup: {t_peak_orig / t_peak_opt:.2f}x")

# Verify correctness
assert np.allclose(rms_original(wav), rms_optimized(wav))
assert np.allclose(peak_original(wav), peak_optimized(wav))
print("Verification passed!")
