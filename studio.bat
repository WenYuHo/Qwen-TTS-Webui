@echo off
setlocal
set "VENV_DIR=.venv"

echo ==========================================
echo Qwen-TTS Podcast Studio: Integrated Launcher
echo ==========================================
echo.

:: 1. Auto-kill stale process on port 8080
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8080 ^| findstr LISTENING') do taskkill /f /pid %%a >nul 2>&1

:: 2. Check for Virtual Environment
if exist "%VENV_DIR%" goto :START_APP

echo [SETUP] Creating virtual environment...
python -m venv %VENV_DIR%
if errorlevel 1 (
    echo [ERROR] Failed to create venv. Is Python installed?
    pause
    exit /b
)
echo [OK] Venv created.

echo [SETUP] Upgrading pip...
call %VENV_DIR%\Scripts\activate
python -m pip install --upgrade pip

echo [SETUP] Detecting CUDA...
nvidia-smi >nul 2>&1
if errorlevel 1 (
    echo [INFO] No GPU detected. Installing CPU Torch...
    pip install torch torchaudio
) else (
    echo [OK] NVIDIA GPU detected. Installing Torch with CUDA...
    pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
)

echo [SETUP] Installing core dependencies...
pip install -r requirements.txt

echo.
echo ==========================================
echo OPTIONAL: Video Generation (LTX-Video)
echo ==========================================
echo This requires a strong GPU (8GB+ VRAM).
set /p install_video="Install video dependencies now? (y/n): "
if /i "%install_video%"=="y" (
    echo [SETUP] Installing LTX requirements...
    pip install ltx-pipelines diffusers opencv-python tqdm
)

:START_APP
call %VENV_DIR%\Scripts\activate.bat

:: 3. Verify and Start
echo.
echo [INFO] Verifying system health...
"%VENV_DIR%\Scripts\python.exe" verify_setup.py

echo.
echo [LAUNCH] Starting Studio Server on http://localhost:8080 ...
"%VENV_DIR%\Scripts\python.exe" src\server.py
pause
