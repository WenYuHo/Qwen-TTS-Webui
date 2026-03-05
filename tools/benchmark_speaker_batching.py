import torch
import numpy as np
import time
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

# Mocking parts of the model that we don't need for the benchmark
# but are required for imports to work
with patch("transformers.AutoConfig.register"),      patch("transformers.AutoModel.register"),      patch("transformers.AutoProcessor.register"):
    from backend.qwen_tts.core.models.modeling_qwen3_tts import mel_spectrogram

def benchmark_mel_spectrogram():
    print("--- Benchmarking mel_spectrogram ---")
    sr = 24000
    n_fft = 1024
    num_mels = 128
    hop_size = 256
    win_size = 1024
    fmin = 0
    fmax = 12000

    # Test with different batch sizes
    for batch_size in [1, 4, 8, 16]:
        y = torch.randn(batch_size, sr).float()

        # Warmup
        _ = mel_spectrogram(y, n_fft, num_mels, sr, hop_size, win_size, fmin, fmax)

        start = time.time()
        for _ in range(10):
            _ = mel_spectrogram(y, n_fft, num_mels, sr, hop_size, win_size, fmin, fmax)
        end = time.time()

        avg_time = (end - start) / 10
        print(f"Batch Size {batch_size}: {avg_time:.4f}s per call ({(avg_time/batch_size)*1000:.2f}ms per sample)")

if __name__ == "__main__":
    try:
        benchmark_mel_spectrogram()
    except Exception as e:
        print(f"Benchmark failed: {e}")
        import traceback
        traceback.print_exc()
