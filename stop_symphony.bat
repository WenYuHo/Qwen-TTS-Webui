@echo off
echo 🛑 Stopping all Symphony Background Agents...
taskkill /fi "windowtitle eq 🎼 SYMPHONY MANAGER*" /f
taskkill /fi "windowtitle eq 👷 SYMPHONY WORKER*" /f
echo.
echo ✅ Background agents stopped.
pause
