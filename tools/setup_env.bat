@echo off
setlocal
echo ==========================================
echo Qwen-TTS Podcast Studio: Local Setup
echo ==========================================
echo.

:: 1. Create Virtual Environment
if not exist .venv (
    echo [1/3] Creating virtual environment...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo ERROR: Failed to create virtual environment. 
        echo Ensure Python is installed and in your PATH.
        pause
        exit /b
    )
) else (
    echo [1/3] Virtual environment already exists.
)

:: 2. Upgrade pip
echo [2/3] Preparing environment...
call .venv\Scripts\activate
python -m pip install --upgrade pip

:: 3. Detect CUDA
echo Checking for NVIDIA GPU (CUDA)...
nvidia-smi >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] NVIDIA GPU detected. Installing Torch with CUDA support...
    pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
) else (
    echo [INFO] No NVIDIA GPU detected or nvidia-smi missing. Installing CPU version...
    pip install torch torchaudio
)

:: 4. Install Core Dependencies
echo [3/4] Installing core libraries...
pip install -r requirements.txt

:: 5. Optional: Video Generation
echo.
echo ==========================================
echo OPTIONAL: Video Generation (LTX-Video)
echo ==========================================
echo This adds text-to-video capabilities.
echo Requires ~1GB additional downloads and a strong GPU (8GB+ VRAM recommended).
set /p install_video="Would you like to install video generation dependencies? (y/n): "
if /i "%install_video%"=="y" (
    echo Installing LTX-Video requirements...
    pip install -r requirements_video.txt
    echo [OK] Video dependencies installed.
) else (
    echo Skipping video generation setup.
)

echo.
echo ==========================================
echo SUCCESS: Environment is ready!
echo ==========================================
echo Use start.bat to launch the studio.
echo.
pause
