import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
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

COMFY_ROOT_GUESS = BASE_DIR.parent.parent.parent

# Default model path
DEFAULT_MODEL_DIR = COMFY_ROOT_GUESS / "models" / "qwen-tts"

# Get from env or default
COMFY_MODELS_DIR = os.getenv("COMFY_QWEN_MODELS_DIR", str(DEFAULT_MODEL_DIR))
MODELS_PATH = Path(COMFY_MODELS_DIR)

if not MODELS_PATH.exists():
    logger.warning(f"Models directory not found at {MODELS_PATH}")
    logger.info("Please set COMFY_QWEN_MODELS_DIR in .env to point to your ComfyUI models/qwen-tts folder.")
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
