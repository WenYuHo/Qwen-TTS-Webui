import os
import sys
import subprocess
from pathlib import Path

def check_nvidia_gpu():
    """Check for NVIDIA GPU using nvidia-smi."""
    try:
        subprocess.run(["nvidia-smi"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def check_torch_cuda():
    """Check if installed torch has CUDA support."""
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False

def install_cuda_torch():
    """Install CUDA-enabled PyTorch."""
    print("âš¡ NVIDIA GPU detected, but PyTorch is not CUDA-enabled (or version mismatch).")
    print("Installing PyTorch 2.6.0 with CUDA 12.4 support...")
    
    python_exe = sys.executable
    # Using cu124 as it is stable and widely compatible with modern drivers
    cmd = [
        python_exe, "-m", "pip", "install", 
        "torch==2.6.0+cu124", "torchvision==0.21.0+cu124", "torchaudio==2.6.0+cu124", 
        "--index-url", "https://download.pytorch.org/whl/cu124",
        "--force-reinstall", "--no-cache-dir"
    ]
    
    try:
        subprocess.check_call(cmd)
        print("âœ… PyTorch with CUDA support installed.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"âŒ Failed to install CUDA PyTorch: {e}")
        return False

def install_video_dependencies():
    """Install ltx-pipelines and related packages."""
    # Note: we pin xformers to a version compatible with torch 2.6.0
    packages = [
        "diffusers",
        "opencv-python",
        "xformers==0.0.28.post1",
        "accelerate",
        "tqdm",
        "sentencepiece"
    ]
    
    python_exe = sys.executable
    print(f"Installing base video dependencies: {', '.join(packages)}...")
    
    try:
        # Install standard packages
        subprocess.check_call([python_exe, "-m", "pip", "install"] + packages)
        
        # Install ltx-pipelines from GitHub source as it's not on PyPI
        print("Installing ltx-pipelines from GitHub source (Lightricks/LTX-2)...")
        # Install core first, then pipelines
        # Using LTX-2 repo as confirmed by web_fetch
        subprocess.check_call([
            python_exe, "-m", "pip", "install", 
            "git+https://github.com/Lightricks/LTX-2.git#subdirectory=packages/ltx-core"
        ])
        subprocess.check_call([
            python_exe, "-m", "pip", "install", 
            "git+https://github.com/Lightricks/LTX-2.git#subdirectory=packages/ltx-pipelines"
        ])
        
        print("âœ… Video dependencies installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"âŒ Installation failed: {e}")
        return False

def verify_all():
    """Final verification of imports and CUDA."""
    print("\n--- Final Verification ---")
    try:
        import torch
        import ltx_pipelines
        import diffusers
        import cv2
        import xformers
        
        cuda_avail = torch.cuda.is_available()
        device_name = torch.cuda.get_device_name(0) if cuda_avail else "N/A"
        
        print(f"[OK] PyTorch version: {torch.__version__}")
        print(f"[OK] CUDA Available: {cuda_avail}")
        if cuda_avail:
            print(f"[OK] GPU: {device_name}")
        print("[OK] ltx-pipelines found.")
        print("[OK] diffusers found.")
        print("[OK] opencv-python (cv2) found.")
        print("[OK] xformers found.")
        
        return cuda_avail
    except ImportError as e:
        print(f"[FAIL] Missing dependency: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Verification error: {e}")
        return False

if __name__ == "__main__":
    print("==========================================")
    print("Video Generation Auto-Setup (LTX-Video)")
    print("==========================================\n")
    
    has_gpu = check_nvidia_gpu()
    
    if has_gpu:
        print("âœ… NVIDIA GPU detected via nvidia-smi.")
        if not check_torch_cuda():
            if not install_cuda_torch():
                print("âŒ Setup aborted due to PyTorch installation failure.")
                sys.exit(1)
        else:
            print("âœ… PyTorch already has CUDA support.")
            
        if install_video_dependencies():
            if verify_all():
                print("\nâœ… Video generation setup complete!")
            else:
                print("\nâš  Setup finished with verification warnings.")
        else:
            print("\nâŒ Failed to install video dependencies.")
            sys.exit(1)
    else:
        print("âŒ No NVIDIA GPU detected. Video generation is skipped.")
        print("Note: LTX-Video requires a strong NVIDIA GPU (8GB+ VRAM) for generation.")
