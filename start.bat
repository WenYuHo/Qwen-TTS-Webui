@echo off
echo Starting Qwen-TTS Podcast Studio...

if not exist .venv (
    echo [ERROR] Virtual environment not found. 
    echo Please run 'setup_env.bat' first!
    pause
    exit /b
)

:: Activate local environment and run
call .venv\Scripts\activate
python src\server.py
pause
