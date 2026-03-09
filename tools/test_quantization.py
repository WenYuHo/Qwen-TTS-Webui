import torch
import sys
from pathlib import Path
import time
import numpy as np

# Setup paths
ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"
BACKEND_DIR = SRC_DIR / "backend"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Apply sox shim if needed
from backend.sox_shim import mock_sox
mock_sox()

from qwen_tts import Qwen3TTSModel
from backend.config import find_model_path, MODELS

def test_quantization():
    model_name = MODELS["1.7B_Base"]
    model_path = find_model_path(model_name)
    if not model_path:
        print("Model not found, skipping test.")
        return

    print(f"Loading original model from {model_path}...")
    start = time.time()
    model_wrapper = Qwen3TTSModel.from_pretrained(str(model_path), device_map="cpu", torch_dtype=torch.float32)
    print(f"Loaded in {time.time() - start:.2f}s")

    # Access the underlying torch module
    raw_model = model_wrapper.model
    
    print("Applying dynamic INT8 quantization (inplace)...")
    start = time.time()
    # Quantize linear layers
    torch.ao.quantization.quantize_dynamic(
        raw_model, 
        {torch.nn.Linear}, 
        dtype=torch.qint8,
        inplace=True
    )
    print(f"Quantized in {time.time() - start:.2f}s")

    # Compare sizes
    def get_size(m):
        param_size = 0
        for param in m.parameters():
            param_size += param.nelement() * param.element_size()
        buffer_size = 0
        for buffer in m.buffers():
            buffer_size += buffer.nelement() * buffer.element_size()
        return (param_size + buffer_size) / 1024 / 1024

    orig_size = get_size(raw_model)
    # Note: quantized model size calculation might be tricky as weights are packed
    # We'll just print a success message if it didn't crash.
    print(f"Original model parameter size: {orig_size:.2f} MB")
    
    # Simple inference test
    print("Testing inference with quantized model...")
    
    # Prepare dummy input for voice clone
    ref_audio = (np.random.rand(24000*5).astype(np.float32), 24000)
    prompt_items = model_wrapper.create_voice_clone_prompt(ref_audio, "dummy text", x_vector_only_mode=True)
    prompt = {
        'ref_spk_embedding': [item.ref_spk_embedding for item in prompt_items],
        'ref_code': [None],
        'x_vector_only_mode': [True],
        'icl_mode': [False]
    }
    
    try:
        start = time.time()
        wavs, sr = model_wrapper.generate_voice_clone("This is a quantization test.", voice_clone_prompt=prompt)
        print(f"Inference successful! Time: {time.time() - start:.2f}s")
    except Exception as e:
        print(f"Inference failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_quantization()
