@echo off
:: Auto-kill any process on port 8080 to prevent conflicts
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8080" ^| find "LISTENING"') do (
    echo [INFO] Killing stale process %%a on port 8080...
    taskkill /f /pid %%a >nul 2>&1
)

echo Starting Qwen-TTS Podcast Studio...

if not exist .venv (
    echo [ERROR] Virtual environment not found. 
    echo Please run 'setup_env.bat' first!
    pause
    exit /b
)

:: Activate local environment and run
call .venv\Scripts\activate
echo Checking environment...
python verify_setup.py
echo.
echo Starting server...
python src\server.py
pause
