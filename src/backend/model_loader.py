import sys
import os
import torch
from pathlib import Path

# Fix import path for qwen_tts (it is now local in backend/qwen_tts)
# We need 'import qwen_tts' to work for internal references
current_file = Path(__file__).resolve()
backend_dir = current_file.parent

if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

try:
    import qwen_tts
    from qwen_tts import Qwen3TTSModel
except ImportError as e:
    print(f"Error importing qwen_tts: {e}")
    Qwen3TTSModel = None

from .config import find_model_path, MODELS

class ModelManager:
    def __init__(self):
        self.model = None
        self.current_model_type = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
    def load_model(self, model_type="VoiceDesign", size="1.7B"):
        """
        Load the appropriate model.
        model_type: 'VoiceDesign', 'Base', 'CustomVoice'
        size: '1.7B' or '0.6B'
        """
        key = f"{size}_{model_type}"
        # For base, it is just "1.7B_Base"
        # For VoiceDesign "1.7B_VoiceDesign"
        
        # Check if already loaded
        if self.model and self.current_model_type == key:
            return self.model
            
        # Find path
        if model_type == "VoiceDesign":
            model_name = MODELS["1.7B_VoiceDesign"] # VoiceDesign only 1.7B
        elif model_type == "CustomVoice":
             model_name = MODELS["CustomVoice_1.7B"] # Default to 1.7B for custom
        else:
             model_name = MODELS["1.7B_Base"] # Default base
             
        model_path = find_model_path(model_name)
        if not model_path:
            raise FileNotFoundError(f"Model {model_name} not found in configured paths.")

        print(f"Loading model: {model_name} from {model_path}")
        
        # Unload previous to save VRAM
        if self.model:
            del self.model
            torch.cuda.empty_cache()
            
        self.model = Qwen3TTSModel.from_pretrained(
            str(model_path), 
            device_map=self.device,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
        )
        self.current_model_type = key
        
        return self.model

# Global instance
manager = ModelManager()

def get_model(model_type="VoiceDesign"):
    return manager.load_model(model_type)
