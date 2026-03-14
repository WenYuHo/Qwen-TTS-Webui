@echo off
setlocal
echo 🎼 SYMPHONY v2 - Launch Orchestrator
echo -----------------------------------
echo 1) Standard Mode (Visible Windows)
echo 2) Headless Mode (Background)
echo.
choice /c 12 /n /m "Select launch mode [1-2]: "
if errorlevel 2 goto headless
if errorlevel 1 goto standard

:standard
echo 🚀 Launching in STANDARD mode...
python symphony_start.py
goto end

:headless
echo 🕵️ Launching in HEADLESS mode...
python symphony_start.py --headless
goto end

:end
pause
