import os
import subprocess
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_gpu():
    try:
        import torch
        if torch.cuda.is_available():
            logger.info(f"GPU detected: {torch.cuda.get_device_name(0)}")
            return True
        else:
            logger.warning("No NVIDIA GPU detected via PyTorch.")
            return False
    except ImportError:
        logger.error("PyTorch not found.")
        return False

def check_dependencies():
    required = ["ltx-pipelines", "ltx-core", "diffusers", "accelerate", "moviepy", "av"]
    missing = []
    for pkg in required:
        try:
            # We use subprocess because some packages might be installed but not easily importable via __import__
            # due to naming conventions (e.g. ltx-pipelines vs ltx_pipelines)
            result = subprocess.run([sys.executable, "-m", "pip", "show", pkg], 
                                 capture_output=True, text=True)
            if result.returncode != 0:
                missing.append(pkg)
        except Exception as e:
            logger.error(f"Error checking {pkg}: {e}")
            missing.append(pkg)
    
    return missing

def install_dependencies(packages):
    if not packages:
        return True
    
    logger.info(f"Installing missing dependencies: {', '.join(packages)}")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + packages)
        logger.info("Installation successful.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Installation failed: {e}")
        return False

def main():
    logger.info("Starting Video Gen Auto-Setup...")
    
    if not check_gpu():
        logger.error("A GPU is required for LTX-2 video generation. Setup aborted.")
        sys.exit(1)
    
    missing = check_dependencies()
    if missing:
        if not install_dependencies(missing):
            sys.exit(1)
    else:
        logger.info("All video generation dependencies are already installed.")
    
    logger.info("Video Gen Setup Complete!")

if __name__ == "__main__":
    main()
