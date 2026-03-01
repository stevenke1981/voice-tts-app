@echo off
title Steven's Voice Workspace

:: Try conda env first
where conda >nul 2>&1
if %ERRORLEVEL% == 0 (
    call conda activate svw 2>nul
    if not errorlevel 1 goto :run
)

:: Fall back to venv
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

:run
python steven_voice.py
