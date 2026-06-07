@echo off
cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo Virtual environment not found: venv\Scripts\python.exe
    pause
    exit /b 1
)

"venv\Scripts\python.exe" "bot.py"
pause
