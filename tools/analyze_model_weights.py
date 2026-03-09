import torch
import os
import sys
from pathlib import Path
import numpy as np

def analyze_sparsity(state_dict, threshold=1e-4):
    print(f"{'Layer Name':<60} | {'Sparsity (%)':<10} | {'Mean Abs':<10}")
    print("-" * 85)
    
    total_params = 0
    total_zero = 0
    
    for name, param in state_dict.items():
        if 'weight' in name and len(param.shape) >= 2:
            num_params = param.numel()
            num_zero = (param.abs() < threshold).sum().item()
            sparsity = (num_zero / num_params) * 100
            mean_abs = param.abs().mean().item()
            
            print(f"{name[:60]:<60} | {sparsity:<12.2f} | {mean_abs:<10.4e}")
            
            total_params += num_params
            total_zero += num_zero
            
    total_sparsity = (total_zero / total_params) * 100 if total_params > 0 else 0
    print("-" * 85)
    print(f"{'TOTAL':<60} | {total_sparsity:<12.2f} | N/A")

if __name__ == "__main__":
    # Check if a model path is provided
    if len(sys.argv) > 1:
        model_path = Path(sys.argv[1])
    else:
        # Default to the Base model in ComfyUI path found earlier
        model_path = Path(r"C:\Users\tony5\Downloads\ComfyUI\models\qwen-tts\Qwen3-TTS-12Hz-1.7B-Base")
    
    # Try to find weights file
    weights_files = list(model_path.glob("*.safetensors")) + list(model_path.glob("*.bin"))
    
    if not weights_files:
        print(f"No weights found in {model_path}")
        sys.exit(1)
        
    for wf in weights_files:
        print(f"\nAnalyzing: {wf.name}")
        try:
            if wf.suffix == ".safetensors":
                from safetensors.torch import load_file
                state_dict = load_file(str(wf))
            else:
                state_dict = torch.load(str(wf), map_location="cpu", weights_only=True)
            
            analyze_sparsity(state_dict)
        except Exception as e:
            print(f"Failed to analyze {wf.name}: {e}")
