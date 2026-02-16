import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Detect ComfyUI paths relative to this project (assuming inside custom_nodes)
# Current structure: ComfyUI/custom_nodes/ComfyUI-Qwen-TTS/Qwen-TTS-Webui/src/backend/config.py
# Models should be at: ComfyUI/models/qwen-tts
# We go up 5 levels? 
# config.py -> backend -> src -> Qwen-TTS-Webui -> ComfyUI-Qwen-TTS -> custom_nodes -> ComfyUI
# Actually 6 levels if we count the file itself?
# Let's count parents:
# 1. backend
# 2. src
# 3. Qwen-TTS-Webui
# 4. ComfyUI-Qwen-TTS
# 5. custom_nodes
# 6. ComfyUI

BASE_DIR = Path(__file__).resolve().parent.parent.parent
COMFY_ROOT_GUESS = BASE_DIR.parent.parent.parent

# Default model path
DEFAULT_MODEL_DIR = COMFY_ROOT_GUESS / "models" / "qwen-tts"

# Get from env or default
COMFY_MODELS_DIR = os.getenv("COMFY_QWEN_MODELS_DIR", str(DEFAULT_MODEL_DIR))
MODELS_PATH = Path(COMFY_MODELS_DIR)

if not MODELS_PATH.exists():
    print(f"WARNING: Models directory not found at {MODELS_PATH}")
    print("Please set COMFY_QWEN_MODELS_DIR in .env to point to your ComfyUI models/qwen-tts folder.")

# Model paths
# The standalone script and download usage usually put them in subfolders like "Qwen/..."
# We need to robustly find them.

def find_model_path(model_name: str) -> Path:
    """
    Find a specific model path (e.g., 'Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign')
    It checks if the full path exists, or if it is inside the models folder.
    """
    # 1. Check direct path
    p = MODELS_PATH / model_name
    if p.exists():
        return p
    
    # 2. Check flattened path (some users unzip directly)
    flat_name = model_name.split("/")[-1]
    p_flat = MODELS_PATH / flat_name
    if p_flat.exists():
        return p_flat
        
    return None

# Dictionary of model names
MODELS = {
    "1.7B_VoiceDesign": "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign",
    "1.7B_Base": "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
    "0.6B_Base": "Qwen/Qwen3-TTS-12Hz-0.6B-Base",
    "CustomVoice_1.7B": "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice", 
    "Tokenizer": "Qwen/Qwen3-TTS-Tokenizer-12Hz"
}
