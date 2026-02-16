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

:: 3. Install Dependencies
echo [3/3] Installing libraries (including Torch)...
echo This may take a few minutes (approx 2GB download).
pip install -r requirements.txt

echo.
echo ==========================================
echo SUCCESS: Environment is ready!
echo ==========================================
echo Use start.bat to launch the studio.
echo.
pause
