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
    from backend.config import MODELS_PATH, find_model_path, MODELS
    # Check if models path exists
    if not MODELS_PATH.exists():
        print(f"[FAIL] Models directory NOT found at: {MODELS_PATH}")
        print("   Please set COMFY_QWEN_MODELS_DIR in .env to point to your ComfyUI models/qwen-tts folder.")
    else:
        print(f"[OK] Models directory found: {MODELS_PATH}")
        # Verify at least one model
        test_model = MODELS["1.7B_VoiceDesign"]
        p = find_model_path(test_model)
        if p:
            print(f"[OK] Found model: {test_model}")
        else:
            print(f"[WARN] Model '{test_model}' not found in the directory.")

    try:
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[OK] Torch version: {torch.__version__}")
        print(f"[OK] Computing Device: {device.upper()}")
        if device == "cpu":
            print("   CAUTION: Running on CPU will be significantly slower.")
        
        from backend.podcast_engine import PodcastEngine
        print("[OK] PodcastEngine initialized successfully.")
    except Exception as e:
        print(f"[FAIL] Backend initialization failed: {e}")
        import traceback
        traceback.print_exc()
    
except ImportError as e:
    print(f"[ERROR] Import failed: {e}")
    sys.exit(1)
    
print("\nVerification complete!")
