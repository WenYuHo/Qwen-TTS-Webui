import numpy as np
import time
import sys
import os

# Add src to path
sys.path.append(os.path.abspath("src"))

from backend.utils import AudioPostProcessor

def benchmark_declick():
    sr = 24000
    duration = 60  # 60 seconds
    num_samples = sr * duration

    # Generate background noise with low RMS
    # With a 2ms window (48 samples), sqrt(48) is ~6.9.
    # The heuristic requires a spike to be > 10x local RMS.
    # If a spike is 1.0, the local RMS of a window containing it is sqrt((1^2 + (N-1)*noise^2) / N).
    # To detect a spike of 1.0, 1.0 > 10 * sqrt((1 + (N-1)*noise^2) / N)
    # 0.1 > sqrt((1 + 47*noise^2) / 48)
    # 0.01 > (1 + 47*noise^2) / 48
    # 0.48 > 1 + 47*noise^2
    # This is impossible if the spike itself is part of the RMS!
    # Wait, the original code DID include the spike in the RMS calculation:
    # local_rms = np.sqrt(np.mean(chunk**2)) + 1e-6
    # spikes = np.abs(chunk) > (local_rms * 10)

    # Let's use the same logic as the original code's detection.
    # If the original code's heuristic is flawed for small windows, my vectorized version should still match it.

    # Let's generate a case that SHOULD be detectable if N is large enough or noise is very low.
    # Actually, for N=48, if the background is 0, RMS is sqrt(1/48) = 0.144.
    # 10 * 0.144 = 1.44. So 1.0 > 1.44 is False.
    # So the heuristic as written in the original code will NEVER detect a single 1.0 spike in 0-noise if window is 48.

    # BUT, if we have a larger window...
    # sr * 0.002 = 48 at 24000.
    # Let's check what window size would work. 10 * sqrt(1/N) < 1 => 100/N < 1 => N > 100.

    # Let's try SR = 96000. 96000 * 0.002 = 192. 10 * sqrt(1/192) = 10 * 0.072 = 0.72.
    # 1.0 > 0.72 is True!

    test_sr = 96000
    test_num_samples = test_sr * duration
    wav = np.zeros(test_num_samples, dtype=np.float32)
    spike_indices = np.random.randint(0, test_num_samples, 100)
    wav[spike_indices] = 1.0

    print(f"Benchmarking de-click on {duration}s of {test_sr}Hz audio ({test_num_samples} samples)...")

    # Warm up
    _ = AudioPostProcessor.apply_declick(wav[:test_sr], test_sr)

    start_time = time.time()
    out = AudioPostProcessor.apply_declick(wav, test_sr)
    end_time = time.time()

    execution_time = end_time - start_time
    print(f"Execution time: {execution_time:.4f} seconds")

    # Basic verification
    spikes_before = np.sum(np.abs(wav) > 0.5)
    spikes_after = np.sum(np.abs(out) > 0.5)
    print(f"Spikes > 0.5 before: {spikes_before}, after: {spikes_after}")

    if spikes_after < spikes_before:
        print("De-clicker is working.")
    else:
        print("De-clicker did NOT reduce spikes. This confirms the heuristic limit at this window/SR.")

if __name__ == "__main__":
    benchmark_declick()
