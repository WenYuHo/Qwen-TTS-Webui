import sys
import os
from pathlib import Path

import subprocess
import shutil

# Add src to path
current_dir = Path(__file__).resolve().parent
src_dir = current_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

def check_binary(name):
    path = shutil.which(name)
    if path:
        print(f"[OK] {name} found: {path}")
        return True
    else:
        print(f"[WARN] {name} not found in PATH.")
        return False

print("=== Qwen-TTS Environment Verification ===\n")

print("Checking system binaries...")
has_ffmpeg = check_binary("ffmpeg")
has_sox = check_binary("sox")
if not has_ffmpeg or not has_sox:
    print("   Note: Missing binaries may limit some audio processing features.")
    print("   Download them from: https://ffmpeg.org/ and https://sourceforge.net/projects/sox/")

print("\nChecking imports and models...")
try:
    import moviepy
    print("[OK] MoviePy version: " + moviepy.__version__)
except ImportError:
    print("[FAIL] MoviePy not found. Install with: pip install moviepy")

try:
    from PIL import Image
    print("[OK] Pillow found.")
except ImportError:
    print("[FAIL] Pillow not found. Install with: pip install Pillow")

try:
    from backend.config import (
        MODELS_PATH, find_model_path, MODELS, VIDEO_DIR, 
        LTX_MODELS_PATH, is_ltx_available, find_ltx_model
    )
    from backend.config import BASE_DIR
    BGM_PATH = BASE_DIR / "bgm"

    # Check if models path exists
    if not MODELS_PATH.exists():
        print(f"[FAIL] Models directory NOT found at: {MODELS_PATH}")
    else:
        print(f"[OK] Models directory found: {MODELS_PATH}")

    # --- Video Generation Check ---
    print("\nChecking Video Generation (LTX-2)...")
    try:
        import ltx_pipelines
        print(f"[OK] LTX Pipelines found.")

        if is_ltx_available():
            print(f"[OK] LTX-2 model checkpoints found at {LTX_MODELS_PATH}")
            # Detail which models are found
            for key in ["checkpoint", "gemma_dir", "ltxv_checkpoint"]:
                found = find_ltx_model(key)
                if found:
                    print(f"   - {key}: {found.name}")
        else:
            print(f"[WARN] LTX-2 models NOT found in {LTX_MODELS_PATH}")
            print("   Go to System > Model Inventory in the WebUI to download them.")
    except ImportError:
        print("[INFO] LTX Pipelines not installed. Video generation will be disabled.")
        print("   To enable, install with: pip install ltx-pipelines diffusers opencv-python")

    if not BGM_PATH.exists() or not any(BGM_PATH.iterdir()):

        print(f"[WARN] BGM directory is missing or empty at: {BGM_PATH}")
        print("   Mood-based mixing may not work without BGM files (mystery.mp3, tech.mp3, etc.)")
    else:
        print(f"[OK] BGM directory contains assets.")

    try:
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[OK] Torch version: {torch.__version__}")
        print(f"[OK] Computing Device: {device.upper()}")
        
        from backend.podcast_engine import PodcastEngine
        print("[OK] PodcastEngine initialized successfully.")
    except Exception as e:
        print(f"[FAIL] Backend initialization failed: {e}")
    
except ImportError as e:
    print(f"[ERROR] Import failed: {e}")
    sys.exit(1)
    
print("\nVerification complete!")
