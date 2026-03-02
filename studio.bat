@echo off
setlocal
set "VENV_DIR=.venv"

echo ==========================================
echo Qwen-TTS Podcast Studio: Integrated Launcher
echo ==========================================
echo.

:: 1. Auto-kill stale process on port 8080
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8080" ^| find "LISTENING"') do (
    echo [INFO] Freeing port 8080 (Process %%a)...
    taskkill /f /pid %%a >nul 2>&1
)

:: 2. Check for Virtual Environment
if not exist "%VENV_DIR%" (
    echo [SETUP] Creating virtual environment...
    python -m venv %VENV_DIR%
    if %errorlevel% neq 0 (
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
    if %errorlevel% equ 0 (
        echo [OK] NVIDIA GPU detected. Installing Torch with CUDA...
        pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
    ) else (
        echo [INFO] No GPU detected. Installing CPU Torch...
        pip install torch torchaudio
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
) else (
    call %VENV_DIR%\Scripts\activate
)

:: 3. Verify and Start
echo.
echo [INFO] Verifying system health...
python verify_setup.py
if %errorlevel% neq 0 (
    echo.
    echo [WARN] System verification had issues. Attempting to start anyway...
)

echo.
echo [LAUNCH] Starting Studio Server on http://localhost:8080 ...
python src\server.py
pause
