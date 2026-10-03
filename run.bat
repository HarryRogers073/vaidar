@echo off
echo ===================================================
echo   Starting HIL and AI Verification Suite (Framework_v2)
echo ===================================================
python "%~dp0app.py"
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Application crashed with exit code %errorlevel%.
    pause
)
