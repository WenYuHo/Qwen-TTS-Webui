import sys
import os
from pathlib import Path

# Add src to path
current_dir = Path(__file__).resolve().parent
src_dir = current_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

print("Checking imports...")
try:
    from backend.config import MODELS_PATH, find_model_path, MODELS
    # Check if models path exists
    if not MODELS_PATH.exists():
        print(f"[WARN] Models directory not found at: {MODELS_PATH}")
        print("   This is expected if you haven't downloaded the models yet.")
        print("   Please run 'python ../download_models.py' to download them.")
        print("   Or set COMFY_QWEN_MODELS_DIR in .env if they are elsewhere.")
    else:
        print(f"[OK] Models directory found: {MODELS_PATH}")

    try:
        import torch
        print(f"[OK] Torch is installed: {torch.__version__}")
        from backend.podcast_engine import PodcastEngine
        print("[OK] PodcastEngine imported successfully.")
    except ImportError as e:
        print(f"[WARN] Torch not found in current environment: {e}")
        print("   If you are running this check with system python, this is expected.")
        print("   Make sure to run the server with the python environment where ComfyUI is installed.")
        print("      e.g. ..\\..\\..\\python_embeded\\python.exe src\\server.py")
    
except ImportError as e:
    print(f"[ERROR] Import failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] Error: {e}")
    sys.exit(1)
    
print("\nAll checks passed! You can run the server with: python src/server.py")
