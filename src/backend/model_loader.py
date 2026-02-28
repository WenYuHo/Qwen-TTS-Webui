import sys
import os
import torch
import threading
from pathlib import Path

# Fix import path for qwen_tts
current_file = Path(__file__).resolve()
backend_dir = current_file.parent
project_root = backend_dir.parent # src

if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from collections import OrderedDict
from .config import find_model_path, MODELS, logger

# Lazy-loaded reference (set on first use, not at import time)
_Qwen3TTSModel = None
_qwen_tts_imported = False


def _ensure_qwen_tts():
    """Lazy import qwen_tts + sox shim. Only runs once."""
    global _Qwen3TTSModel, _qwen_tts_imported
    if _qwen_tts_imported:
        return
    _qwen_tts_imported = True
    logger.info("Initializing Qwen-TTS environment...")

    # Apply sox shim for Windows (must happen before qwen_tts import)
    try:
        import sox
        # Even if installed, check if it's the real one or needs shim (some sox wheels are broken on Win)
        if not hasattr(sox, "Transformer"):
            raise ImportError("Incomplete sox installation")
    except ImportError:
        from .sox_shim import mock_sox
        logger.info("Applying sox shim for Windows environment")
        mock_sox()

    try:
        from qwen_tts import Qwen3TTSModel
        _Qwen3TTSModel = Qwen3TTSModel
        logger.info("Successfully imported qwen_tts core")
    except ImportError as e:
        logger.error(f"Error importing qwen_tts: {e}")
        import traceback
        traceback.print_exc()
        _Qwen3TTSModel = None


class ModelManager:
    def __init__(self, cache_size=3):
        self.models = OrderedDict()
        self.cache_size = cache_size
        self.device = self._get_best_device()
        self.lock = threading.Lock()
        
    def _get_best_device(self):
        """Identify best available device and log diagnostics."""
        cuda_available = torch.cuda.is_available()
        logger.info(f"PyTorch version: {torch.__version__}")
        logger.info(f"CUDA available: {cuda_available}")
        
        if cuda_available:
            device_name = torch.cuda.get_device_name(0)
            mem_total = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            logger.info(f"Using GPU: {device_name} ({mem_total:.1f} GB total memory)")
            return "cuda"
        else:
            logger.warning("CUDA not available. Falling back to CPU. Performance will be slower.")
            return "cpu"

    def load_model(self, model_type="VoiceDesign", size="1.7B"):
        """Loads a model with LRU caching to prevent multi-second reload overhead."""
        _ensure_qwen_tts()
        if _Qwen3TTSModel is None:
            logger.error("qwen_tts package failed to import. Check installation.")
            raise RuntimeError("qwen_tts package failed to import. Check installation.")

        with self.lock:
            key = f"{size}_{model_type}"

            # 1. Check if model is in cache (LRU hit)
            if key in self.models:
                logger.info(f"⚡ Bolt: Model cache hit for {key}. Reusing existing instance.")
                # Move to end to mark as most recently used
                self.models.move_to_end(key)
                return self.models[key]
                
            # 2. Resolve model name
            if model_type == "VoiceDesign":
                model_name = MODELS["1.7B_VoiceDesign"]
            elif model_type == "CustomVoice":
                model_name = MODELS["CustomVoice_1.7B"]
            elif model_type == "Base":
                model_name = MODELS["1.7B_Base"]
            else:
                logger.error(f"Unknown model type requested: {model_type}")
                raise ValueError(f"Unknown model type: {model_type}")
                 
            model_path = find_model_path(model_name)
            if not model_path:
                logger.critical(f"Model {model_name} NOT FOUND. Initialization failed.")
                raise FileNotFoundError(f"Model {model_name} not found.")

            # 3. Handle cache eviction if full
            if len(self.models) >= self.cache_size:
                oldest_key, oldest_model = self.models.popitem(last=False)
                logger.info(f"⚡ Bolt: Evicting LRU model from cache: {oldest_key}")
                del oldest_model
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

            # 4. Load the new model
            logger.info(f"Loading Qwen-TTS model: {model_name} on {self.device}")
            try:
                model = _Qwen3TTSModel.from_pretrained(
                    str(model_path), 
                    device_map=self.device,
                    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                    local_files_only=True
                )
                self.models[key] = model
                logger.info(f"Model {key} loaded successfully and added to cache.")
                return model
            except Exception as e:
                logger.critical(f"CRITICAL ERROR loading model: {e}")
                import traceback
                traceback.print_exc()
                raise e

# Global instance
manager = ModelManager()

def get_model(model_type="VoiceDesign"):
    return manager.load_model(model_type)
