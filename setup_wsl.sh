#!/bin/bash

# WSL Setup Script for Bengali Speech Audio-Visual Dataset
# ========================================================
# This script sets up the environment for WSL/Ubuntu systems

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_status "====================================================="
print_status "WSL Setup for Bengali Speech Audio-Visual Dataset"
print_status "====================================================="

# Check if running in WSL
if [[ -z "$WSL_DISTRO_NAME" ]]; then
    print_warning "This script is designed for WSL environments"
    print_warning "It may work on regular Linux, but macOS users should use regular requirements.txt"
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update system packages
print_status "Updating system packages..."
sudo apt-get update

# Install system dependencies
print_status "Installing system dependencies..."
sudo apt-get install -y \
    python3-dev \
    python3-pip \
    python3-venv \
    portaudio19-dev \
    python3-pyaudio \
    libsndfile1-dev \
    libportaudio2 \
    libportaudiocpp0 \
    ffmpeg \
    libavcodec-extra \
    libopencv-dev \
    python3-opencv \
    build-essential \
    cmake \
    git

print_success "System dependencies installed"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_status "Creating Python virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_status "Using existing virtual environment"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install WSL-compatible requirements
print_status "Installing WSL-compatible Python packages..."
if [ -f "requirements_wsl.txt" ]; then
    pip install -r requirements_wsl.txt
    print_success "WSL-compatible packages installed"
else
    print_error "requirements_wsl.txt not found"
    print_status "Falling back to clean requirements..."
    if [ -f "requirements_clean.txt" ]; then
        pip install -r requirements_clean.txt
        print_success "Clean requirements installed"
    else
        print_error "No compatible requirements file found"
        exit 1
    fi
fi

# Install additional packages for SyncNet compatibility
print_status "Installing additional SyncNet compatibility packages..."
pip install scenedetect[opencv]==0.6.2 --force-reinstall

# Verify installation
print_status "Verifying installation..."
python3 -c "
import sys
print(f'Python version: {sys.version}')

try:
    import cv2
    print(f'OpenCV version: {cv2.__version__}')
except ImportError:
    print('OpenCV: Not installed')

try:
    import numpy
    print(f'NumPy version: {numpy.__version__}')
except ImportError:
    print('NumPy: Not installed')

try:
    import torch
    print(f'PyTorch version: {torch.__version__}')
except ImportError:
    print('PyTorch: Not installed')

try:
    import scenedetect
    print(f'SceneDetect version: {scenedetect.__version__}')
except ImportError:
    print('SceneDetect: Not installed')

try:
    import whisper
    print('Whisper: Available')
except ImportError:
    print('Whisper: Not installed')
"

print_status "====================================================="
print_success "WSL setup completed!"
print_status "====================================================="

print_status "To activate the environment in future sessions:"
print_status "  source venv/bin/activate"
print_status ""
print_status "To test the pipeline:"
print_status "  ./complete_pipeline.sh <video_id> --preset medium"
print_status ""
print_warning "Note: If SyncNet still has issues, try:"
print_warning "  pip install numpy==1.21.6 --force-reinstall"
print_warning "  This uses an older numpy that's more compatible with scenedetect"