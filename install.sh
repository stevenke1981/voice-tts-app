#!/usr/bin/env bash
set -euo pipefail

echo "============================================================"
echo " Steven's Voice Workspace  |  macOS / Linux Installer"
echo "============================================================"

if command -v conda &>/dev/null; then
    echo "[INFO] conda detected - creating environment 'svw'"
    conda create -n svw python=3.11 -y
    source "$(conda info --base)/etc/profile.d/conda.sh"
    conda activate svw
else
    echo "[INFO] conda not found - using venv"
    python3 -m venv .venv
    source .venv/bin/activate
fi

ARCH=$(uname -m)
if [ "$ARCH" = "arm64" ]; then
    echo "[INFO] Apple Silicon - installing MPS PyTorch"
    pip install torch torchvision torchaudio
elif command -v nvcc &>/dev/null; then
    echo "[INFO] NVIDIA GPU - installing CUDA PyTorch"
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
else
    echo "[INFO] CPU only"
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
fi

echo "[INFO] Installing project dependencies ..."
pip install -r requirements.txt

echo ""
echo "============================================================"
echo " Installation complete!  Run:  ./start.sh"
echo "============================================================"
