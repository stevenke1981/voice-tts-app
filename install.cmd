@echo off
setlocal EnableDelayedExpansion
title Steven's Voice Workspace - Installer

echo ============================================================
echo  Steven's Voice Workspace  ^|  Windows Installer
echo ============================================================
echo.

where conda >nul 2>&1
if %ERRORLEVEL% == 0 (
    echo [INFO] conda detected - creating environment "svw"
    conda create -n svw python=3.11 -y
    call conda activate svw
    goto :install_pkgs
)

echo [INFO] conda not found - using Python venv
python -m venv .venv
call .venv\Scripts\activate.bat

:install_pkgs
echo.
echo [INFO] Detecting GPU ...
nvcc --version >nul 2>&1
if %ERRORLEVEL% == 0 (
    echo [INFO] CUDA found - installing PyTorch CUDA 12.4
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
) else (
    echo [INFO] No CUDA - installing CPU-only PyTorch
    pip install torch torchvision torchaudio
)

echo.
echo [INFO] Installing project dependencies ...
pip install -r requirements.txt

echo.
echo ============================================================
echo  Installation complete!  Run:  start.cmd
echo ============================================================
pause
