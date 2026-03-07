import time
import torch
import numpy as np
import json
import sys
from pathlib import Path
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from backend.config import logger, BIN_DIR
from backend.podcast_engine import PodcastEngine
from backend.model_loader import get_model

# Ensure uploads directory exists for temp files
uploads_dir = Path("uploads")
uploads_dir.mkdir(exist_ok=True)

# Add bin directory to PATH for sox/ffmpeg on Windows
bin_dir = str(Path(__file__).resolve().parent.parent / "bin")
if bin_dir not in os.environ["PATH"]:
    os.environ["PATH"] = bin_dir + os.pathsep + os.environ["PATH"]

def run_benchmark():
    engine = PodcastEngine()
    
    # Even shorter test sentence to avoid timeouts
    TEST_TEXT = "Hello world, this is a benchmark."
    
    # Ensure a test.wav exists for clone benchmarks
    test_wav_path = uploads_dir / "test.wav"
    if not test_wav_path.exists():
        # Create a dummy 3-second silent wav for benchmarking if it doesn't exist
        import soundfile as sf
        dummy_audio = np.zeros(24000 * 3)
        sf.write(test_wav_path, dummy_audio, 24000)

    VOICE_TYPES = [
        {"name": "Preset",    "profile": {"type": "preset", "value": "ryan"}},
    ]

    results = []
    print(f"\n{'Voice Type':<12} | {'Elapsed':<8} | {'Audio Dur':<10} | {'RTF':<6} | {'VRAM (GB)':<10}")
    print("-" * 65)

    for vt in VOICE_TYPES:
        try:
            if torch.cuda.is_available():
                torch.cuda.reset_peak_memory_stats()
                torch.cuda.empty_cache()
            
            start = time.perf_counter()
            # Warm up or first run
            wav, sr = engine.generate_segment(TEST_TEXT, profile=vt["profile"])
            elapsed = time.perf_counter() - start
            
            peak_vram = torch.cuda.max_memory_allocated() / 1e9 if torch.cuda.is_available() else 0
            duration = len(wav) / sr
            rtf = elapsed / duration if duration > 0 else 0
            
            print(f"{vt['name']:<12} | {elapsed:>7.2f}s | {duration:>9.2f}s | {rtf:>5.2f} | {peak_vram:>9.2f}")
            
            results.append({
                "name": vt["name"],
                "elapsed": elapsed,
                "duration": duration,
                "rtf": rtf,
                "vram_gb": peak_vram,
                "timestamp": time.time()
            })
        except Exception as e:
            print(f"{vt['name']:<12} | FAILED: {str(e)[:40]}...")

    # Save results
    output_path = Path("tools/benchmark_results.json")
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {output_path}")

if __name__ == "__main__":
    run_benchmark()
