#!/bin/bash

VENV_DIR=".venv"

echo "=========================================="
echo "Qwen-TTS Podcast Studio: Integrated Launcher"
echo "=========================================="
echo

# 1. Auto-kill stale process on port 8080
STALE_PID=$(lsof -t -i:8080)
if [ ! -z "$STALE_PID" ]; then
    echo "[INFO] Freeing port 8080 (PID $STALE_PID)..."
    kill -9 $STALE_PID 2>/dev/null
fi

# 2. Check for Virtual Environment
if [ ! -d "$VENV_DIR" ]; then
    echo "[SETUP] Creating virtual environment..."
    python3 -m venv $VENV_DIR
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to create venv. Is python3-venv installed?"
        exit 1
    fi
    echo "[OK] Venv created."
    
    source $VENV_DIR/bin/activate
    echo "[SETUP] Upgrading pip..."
    pip install --upgrade pip
    
    echo "[SETUP] Detecting CUDA..."
    if command -v nvidia-smi &> /dev/null; then
        echo "[OK] NVIDIA GPU detected. Installing Torch with CUDA..."
        pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
    else
        echo "[INFO] No GPU detected. Installing CPU Torch..."
        pip install torch torchaudio
    fi
    
    echo "[SETUP] Installing core dependencies..."
    pip install -r requirements.txt
    
    echo
    echo "=========================================="
    echo "OPTIONAL: Video Generation (LTX-Video)"
    echo "=========================================="
    echo "This requires a strong GPU (8GB+ VRAM)."
    read -p "Install video dependencies now? (y/n): " install_video
    if [[ $install_video == "y" || $install_video == "Y" ]]; then
        echo "[SETUP] Installing LTX requirements..."
        pip install ltx-pipelines diffusers opencv-python tqdm
    fi
else
    source $VENV_DIR/bin/activate
fi

# 3. Verify and Start
echo
echo "[INFO] Verifying system health..."
python3 verify_setup.py
if [ $? -ne 0 ]; then
    echo
    echo "[WARN] System verification had issues. Attempting to start anyway..."
fi

echo
echo "[LAUNCH] Starting Studio Server on http://localhost:8080 ..."
python3 src/server.py
