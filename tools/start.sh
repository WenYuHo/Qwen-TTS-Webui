#!/bin/bash
# Auto-kill any process on port 8080 to prevent conflicts
lsof -ti:8080 | xargs kill -9 2>/dev/null

echo "Starting Qwen-TTS Podcast Studio..."

if [ ! -d ".venv" ]; then
    echo "[ERROR] Virtual environment not found."
    echo "Please run './setup_env.sh' first!"
    $E 1
fi

# Activate local environment and run
source .venv/bin/activate
echo "Checking environment..."
python3 verify_setup.py
echo
echo "Starting server..."
python3 src/server.py
