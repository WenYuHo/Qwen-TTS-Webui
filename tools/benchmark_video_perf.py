"""Benchmark script for LTX-Video generation."""
import os
import sys
import time
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.backend.config import logger
from src.backend.engines.ltx_video_engine import LTXVideoEngine
import torch

def run_benchmark():
    print("--- Starting LTX-Video Benchmark ---")
    
    engine = LTXVideoEngine()
    if not engine.available:
        print("LTX-Video is not available. Ensure models are downloaded.")
        return
        
    prompt = "A cinematic shot of a coffee cup on a wooden table, steam rising, early morning light."
    print(f"Prompt: {prompt}")
    
    # 1. Measure Initialization Time
    t0 = time.time()
    engine._ensure_pipeline()
    init_time = time.time() - t0
    print(f"Pipeline Initialization Time: {init_time:.2f}s")
    
    if torch.cuda.is_available():
        memory_allocated = torch.cuda.memory_allocated() / (1024**3)
        print(f"VRAM after init: {memory_allocated:.2f} GB")
    
    # 2. Measure Generation Time (Run 1 - includes torch.compile overhead)
    print("\n--- Generation Run 1 (Cold Start / Compilation) ---")
    t0 = time.time()
    result = engine.generate_video(prompt=prompt, num_frames=9, num_inference_steps=10)
    gen_time_1 = time.time() - t0
    print(f"Run 1 Time: {gen_time_1:.2f}s")
    
    if torch.cuda.is_available():
        memory_allocated = torch.cuda.memory_allocated() / (1024**3)
        peak_memory = torch.cuda.max_memory_allocated() / (1024**3)
        print(f"VRAM after Run 1: {memory_allocated:.2f} GB")
        print(f"Peak VRAM during Run 1: {peak_memory:.2f} GB")
    
    # 3. Measure Generation Time (Run 2 - Warm)
    print("\n--- Generation Run 2 (Warm Start) ---")
    t0 = time.time()
    result = engine.generate_video(prompt=prompt, num_frames=9, num_inference_steps=10)
    gen_time_2 = time.time() - t0
    print(f"Run 2 Time: {gen_time_2:.2f}s")
    
    if torch.cuda.is_available():
        memory_allocated = torch.cuda.memory_allocated() / (1024**3)
        peak_memory = torch.cuda.max_memory_allocated() / (1024**3)
        print(f"VRAM after Run 2: {memory_allocated:.2f} GB")
        print(f"Peak VRAM during Run 2: {peak_memory:.2f} GB")
        
    print("\n--- Benchmark Complete ---")
    print(f"Note: Run 2 time (warm) represents actual steady-state performance.")
    print(f"Video saved to: {result['path']}")

if __name__ == "__main__":
    # Suppress verbose module logging for the benchmark
    logging.getLogger("diffusers").setLevel(logging.ERROR)
    run_benchmark()
