import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

# Mock torch and qwen_tts before importing model_loader
mock_torch = MagicMock()
mock_torch.cuda.is_available.return_value = False
mock_torch.__version__ = '2.0.0'
sys.modules['torch'] = mock_torch

mock_qwen = MagicMock()
sys.modules['qwen_tts'] = mock_qwen

# Mock config
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
import backend.model_loader as model_loader

# Mock find_model_path to return a dummy path
with patch('backend.model_loader.find_model_path', return_value=Path("/tmp/dummy_model")):
    manager = model_loader.ModelManager()

    print("--- Test 1: First load ---")
    manager.load_model("VoiceDesign")
    print(f"Current models in manager: {getattr(manager, 'current_model_type', 'N/A')}")

    print("\n--- Test 2: Switch load ---")
    manager.load_model("CustomVoice")
    print(f"Current models in manager: {getattr(manager, 'current_model_type', 'N/A')}")

    print("\n--- Test 3: Reload first (should be cached after fix) ---")
    # In original code, this would trigger a reload
    with patch.object(model_loader.logger, 'info') as mock_logger:
        manager.load_model("VoiceDesign")
        # Check if "Loading Qwen-TTS model" was called again
        loading_calls = [call for call in mock_logger.call_args_list if "Loading Qwen-TTS model" in str(call)]
        if loading_calls:
            print("RELOAD DETECTED (Bottleneck exists)")
        else:
            print("NO RELOAD (Cache hit!)")
