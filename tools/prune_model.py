import torch
import torch.nn.utils.prune as prune
import os
import sys
from pathlib import Path
from safetensors.torch import load_file, save_file

def prune_model(model_path, output_path, amount=0.1):
    print(f"Loading model from {model_path}...")
    weights_files = list(model_path.glob("*.safetensors"))
    if not weights_files:
        print("No safetensors found.")
        return

    # For simplicity, we assume one weights file for now (common for 1.7B)
    wf = weights_files[0]
    state_dict = load_file(str(wf))
    
    print(f"Applying magnitude pruning (amount={amount})...")
    
    new_state_dict = {}
    total_pruned = 0
    total_params = 0
    
    for name, tensor in state_dict.items():
        if 'weight' in name and any(x in name for x in ['mlp', 'proj']) and tensor.ndim >= 2:
            # Simple manual magnitude pruning to avoid full model loading
            flat = tensor.view(-1)
            num_params = flat.numel()
            k = int(amount * num_params)
            if k > 0:
                threshold = torch.topk(flat.abs(), k, largest=False).values.max()
                mask = (tensor.abs() > threshold)
                tensor = tensor * mask
                total_pruned += k
            total_params += num_params
        new_state_dict[name] = tensor
        
    print(f"Pruned {total_pruned} / {total_params} target parameters ({total_pruned/total_params*100:.2f}%).")
    
    os.makedirs(output_path, exist_ok=True)
    save_file(new_state_dict, str(output_path / wf.name))
    
    # Copy other files and directories (config, tokenizer, etc)
    for f in model_path.glob("*"):
        if f.name == ".cache":
            continue
        if f.suffix in ['.safetensors', '.bin']:
            continue
            
        dst_f = output_path / f.name
        import shutil
        if f.is_dir():
            if dst_f.exists():
                shutil.rmtree(str(dst_f))
            shutil.copytree(str(f), str(dst_f))
        else:
            shutil.copy(str(f), str(dst_f))
            
    print(f"Pruned model saved to {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python tools/prune_model.py <src_dir> <dst_dir> [amount]")
        sys.exit(1)
        
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])
    amt = float(sys.argv[3]) if len(sys.argv) > 3 else 0.1
    
    prune_model(src, dst, amt)
