#!/bin/bash
echo "=========================================="
echo "Qwen-TTS Podcast Studio: Local Setup"
echo "=========================================="
echo

# 1. Create Virtual Environment
if [ ! -d ".venv" ]; then
    echo "[1/3] Creating virtual environment..."
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment."
        echo "Ensure python3-venv is installed."
        $E 1
    fi
else
    echo "[1/3] Virtual environment already exists."
fi

# 2. Upgrade pip
echo "[2/3] Preparing environment..."
source .venv/bin/activate
pip install --upgrade pip

# 3. Install Dependencies
echo "[3/3] Installing libraries (including Torch)..."
echo "This may take a %s (approx 2GB download)." "minutes"
pip install -r requirements.txt

echo
echo "=========================================="
echo "SUCCESS: Environment is ready!"
echo "=========================================="
echo "Use ./start.sh to launch the studio."
echo
