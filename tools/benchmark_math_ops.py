import numpy as np
import time

def benchmark_rms():
    # 10 minutes of 44.1kHz stereo audio
    size = 44100 * 60 * 10 * 2
    # Use float64 for better precision and more obvious difference if any
    wav = np.random.uniform(-1, 1, size).astype(np.float64)

    print(f"Benchmarking RMS on {size} samples ({wav.nbytes / 1024 / 1024:.2f} MB)")

    # Standard way
    start = time.perf_counter()
    for _ in range(10):
        # wav ** 2 creates a new large array
        rms1 = np.sqrt(np.mean(wav ** 2))
    end = time.perf_counter()
    print(f"Standard (np.mean(wav**2)): {(end - start) / 10:.4f}s")

    # Optimized way (vdot returns a scalar)
    start = time.perf_counter()
    for _ in range(10):
        # np.vdot is more direct
        # Note: np.vdot on 1D arrays is equivalent to dot product
        rms2 = np.sqrt(np.vdot(wav, wav) / wav.size)
    end = time.perf_counter()
    print(f"Optimized (np.vdot): {(end - start) / 10:.4f}s")

    print(f"RMS1: {rms1}, RMS2: {rms2}")
    assert np.allclose(rms1, rms2)

def benchmark_peak():
    # 10 minutes of 44.1kHz stereo audio
    size = 44100 * 60 * 10 * 2
    wav = np.random.uniform(-1, 1, size).astype(np.float64)

    print(f"\nBenchmarking Peak on {size} samples ({wav.nbytes / 1024 / 1024:.2f} MB)")

    # Standard way
    start = time.perf_counter()
    for _ in range(10):
        peak1 = np.max(np.abs(wav))
    end = time.perf_counter()
    print(f"Standard (np.max(np.abs(wav))): {(end - start) / 10:.4f}s")

    # Optimized way
    start = time.perf_counter()
    for _ in range(10):
        peak2 = max(np.max(wav), -np.min(wav))
    end = time.perf_counter()
    print(f"Optimized (max(np.max, -np.min)): {(end - start) / 10:.4f}s")

    print(f"Peak1: {peak1}, Peak2: {peak2}")
    assert np.allclose(peak1, peak2)

if __name__ == "__main__":
    benchmark_rms()
    benchmark_peak()
