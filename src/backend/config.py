import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Configure logging
LOG_DIR = BASE_DIR / "logs"
if not LOG_DIR.exists():
    LOG_DIR.mkdir(parents=True)

log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log_file = LOG_DIR / "studio.log"

# Rotating file handler (10MB per file, keep 5 backups)
file_handler = RotatingFileHandler(str(log_file), maxBytes=10*1024*1024, backupCount=5, encoding='utf-8')
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
console_handler.setLevel(logging.INFO)

# Root-like logger for the whole backend
logger = logging.getLogger("studio")
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

logger.info("--- Logging initialized ---")

# Default model path: 'models' directory in project root
DEFAULT_MODEL_DIR = BASE_DIR / "models"

# Get from env (prioritize new generic name, then old comfy name) or default
MODELS_DIR_ENV = os.getenv("QWEN_MODELS_DIR", os.getenv("COMFY_QWEN_MODELS_DIR", str(DEFAULT_MODEL_DIR)))
MODELS_PATH = Path(MODELS_DIR_ENV)

if not MODELS_PATH.exists():
    logger.warning(f"Models directory not found at {MODELS_PATH}")
    logger.info("Please set QWEN_MODELS_DIR in .env to point to your Qwen-TTS models folder.")
    # Create the local models folder as a placeholder if it's the default
    if str(MODELS_PATH) == str(DEFAULT_MODEL_DIR):
        MODELS_PATH.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created local models directory at {MODELS_PATH}")
else:
    logger.info(f"Models directory found at {MODELS_PATH}")

def find_model_path(model_name: str) -> Path:
    """
    Find a specific model path (e.g., 'Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign')
    It checks if the full path exists, or if it is inside the models folder.
    """
    # 1. Check direct path
    p = MODELS_PATH / model_name
    if p.exists():
        logger.info(f"Model found at direct path: {p}")
        return p
    
    # 2. Check flattened path (some users unzip directly)
    flat_name = model_name.split("/")[-1]
    p_flat = MODELS_PATH / flat_name
    if p_flat.exists():
        logger.info(f"Model found at flattened path: {p_flat}")
        return p_flat
    
    logger.error(f"Model {model_name} NOT found in {MODELS_PATH}")
    return None

def verify_system_paths():
    """Diagnostic check for essential paths and files.

    Returns:
        dict: A dictionary containing:
            - models_dir_exists (bool): True if the base models directory exists.
            - models_dir_path (str): The absolute path to the models directory.
            - found_models (list): A list of model keys (e.g., '1.7B_VoiceDesign') that were successfully located.
    """
    results = {
        "models_dir_exists": MODELS_PATH.exists(),
        "models_dir_path": str(MODELS_PATH),
        "found_models": []
    }
    
    if MODELS_PATH.exists():
        for m_key, m_name in MODELS.items():
            path = find_model_path(m_name)
            if path:
                results["found_models"].append(m_key)
                
    return results

# Dictionary of model names
MODELS = {
    "1.7B_VoiceDesign": "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign",
    "1.7B_Base": "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
    "0.6B_Base": "Qwen/Qwen3-TTS-12Hz-0.6B-Base",
    "CustomVoice_1.7B": "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice", 
    "Tokenizer": "Qwen/Qwen3-TTS-Tokenizer-12Hz"
}

LTX_MODELS = {
    "LTX_Video_2B": "Lightricks/LTX-Video",  # For checkpoint v0.9
}

# Data paths
PROJECTS_DIR = BASE_DIR / "projects"
PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
VOICE_LIBRARY_FILE = PROJECTS_DIR / "voices.json"

VIDEO_DIR = PROJECTS_DIR / "videos"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)
VOICE_IMAGES_DIR = PROJECTS_DIR / "voice_images"
VOICE_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# Shared assets for BGM/SFX
SHARED_ASSETS_DIR = BASE_DIR / "shared_assets"
SHARED_ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# --- LTX Video Generation Config ---
VIDEO_OUTPUT_DIR = PROJECTS_DIR / "generated_videos"
VIDEO_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

LTX_MODELS_PATH = MODELS_PATH / "LTX-Video"

def is_ltx_available() -> bool:
    """Check if any LTX model checkpoints are present."""
    if not LTX_MODELS_PATH.exists():
        return False
    # Check for either LTX-2 (checkpoint + gemma) or LTX-Video (safetensors)
    return (find_ltx_model("checkpoint") is not None and find_ltx_model("gemma_dir") is not None) or \
           find_ltx_model("ltxv_checkpoint") is not None

def find_ltx_model(key: str) -> Optional[Path]:
    """Resolve specific LTX model components within LTX_MODELS_PATH."""
    if not LTX_MODELS_PATH.exists():
        return None
        
    patterns = {
        "checkpoint": "**/ltx2_distill_checkpoint.pth",
        "gemma_dir": "**/gemma_2b_distill",
        "spatial_upsampler": "**/ltx2_spatial_upsampler.pth",
        "distilled_lora": "**/ltx2_distilled_lora.safetensors",
        "ltxv_checkpoint": "**/ltx-video-2b-v0.9.safetensors", # Smallest model
    }
    
    if key not in patterns:
        return None
        
    matches = list(LTX_MODELS_PATH.glob(patterns[key]))
    if matches:
        # Return the first match (usually there should only be one)
        return matches[0]
        
    # Also check if it's a directory (for gemma_dir)
    if key == "gemma_dir":
        for p in LTX_MODELS_PATH.rglob("*"):
            if p.is_dir() and p.name == "gemma_2b_distill":
                return p
                
    return None
