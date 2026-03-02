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

# Mock config dependencies
import logging
sys.modules['dotenv'] = MagicMock()

# Mock src path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
import backend.model_loader as model_loader

# Mock find_model_path to return a dummy path
with patch('backend.model_loader.find_model_path', return_value=Path("/tmp/dummy_model")):
    manager = model_loader.ModelManager()
    manager.max_models = 2

    print("--- Test 1: First load (VoiceDesign) ---")
    manager.load_model("VoiceDesign")
    print(f"Models in cache: {list(manager.models.keys())}")

    print("\n--- Test 2: Second load (CustomVoice) ---")
    manager.load_model("CustomVoice")
    print(f"Models in cache: {list(manager.models.keys())}")

    print("\n--- Test 3: Cache Hit (Reload VoiceDesign) ---")
    with patch.object(model_loader.logger, 'info') as mock_logger:
        manager.load_model("VoiceDesign")
        loading_calls = [call for call in mock_logger.call_args_list if "Loading Qwen-TTS model" in str(call)]
        if loading_calls:
            print("FAILED: RELOAD DETECTED")
        else:
            print("SUCCESS: NO RELOAD (Cache hit!)")
            print(f"LRU Order (should have VoiceDesign at end): {manager.lru_order}")

    print("\n--- Test 4: Cache Eviction (Load Base) ---")
    # Current cache: [CustomVoice, VoiceDesign] (since VoiceDesign was touched last)
    # Eviction should target CustomVoice
    with patch.object(model_loader.logger, 'info') as mock_logger:
        manager.load_model("Base")
        eviction_calls = [call for call in mock_logger.call_args_list if "Evicting model" in str(call)]
        if eviction_calls:
            print(f"SUCCESS: Eviction detected: {eviction_calls[0]}")
        else:
            print("FAILED: No eviction detected")
        print(f"Models in cache: {list(manager.models.keys())}")
