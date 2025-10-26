# Docker Setup Guide for Bengali Speech Pipeline

This guide explains how to build and run the complete Bengali Speech Audio-Visual Dataset Pipeline in Docker, including the modified SyncNet integration.

## 📋 Overview

The Docker setup includes:
- ✅ Modified SyncNet (with all your customizations)
- ✅ All pretrained models and weights (no internet downloads needed)
- ✅ Modified scenedetect library
- ✅ Complete Bengali pipeline with all dependencies
- ✅ GPU support (NVIDIA Docker)
- ✅ All 5 silence detection presets
- ✅ Google and Whisper transcription models

## 🔧 Prerequisites

### Required:
- Docker (version 20.10+)
- Docker Compose (version 1.29+)
- 10GB+ free disk space

### Optional (for GPU acceleration):
- NVIDIA GPU
- NVIDIA Docker runtime
- nvidia-container-toolkit

### Installation:

#### macOS:
```bash
# Install Docker Desktop
# Download from: https://www.docker.com/products/docker-desktop

# For GPU support (not available on macOS)
# GPU acceleration is only available on Linux
```

#### Linux:
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install NVIDIA Docker (for GPU support)
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

## 📁 Directory Structure

Before building, ensure this directory structure:

```
Research/Audio Visual/Code/
├── bengali-speech-audio-visual-dataset/    # This repository
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── run_docker.sh
│   ├── utils/
│   ├── downloads/           # Input videos (volume mount)
│   ├── outputs/             # Results (volume mount)
│   └── ...
└── syncnet_python/                         # Your modified SyncNet
    ├── data/
    │   └── work/
    │       └── pytorchmodels/
    │           └── syncnet_v2.model        # ⚠️ MUST be present!
    ├── scenedetect/                        # Modified library
    ├── SyncNetInstance.py                  # Your modifications
    └── ...
```

**⚠️ CRITICAL**: The `syncnet_python` directory must be in the parent directory of `bengali-speech-audio-visual-dataset` for the Docker build to find it.

## 🏗️ Building the Docker Image

### Step 1: Verify SyncNet Location

```bash
# From the bengali-speech-audio-visual-dataset directory
ls -la ../syncnet_python/data/work/pytorchmodels/syncnet_v2.model

# You should see the model file. If not, ensure it's present before building.
```

### Step 2: Build the Image

```bash
# Make the runner script executable
chmod +x run_docker.sh

# Build the Docker image (this includes all local modifications)
./run_docker.sh build
```

This will:
1. Copy your modified SyncNet code
2. Include all pretrained models and weights
3. Install modified scenedetect library
4. Set up the Bengali pipeline
5. Create a ready-to-use container

**Build time**: 5-10 minutes (first time)

## 🚀 Quick Start

### 1. Start the Container

```bash
./run_docker.sh start
```

### 2. Place Your Video

```bash
# Copy your video to the downloads folder
cp /path/to/your/video.mp4 downloads/SSYouTubeonline.mp4
```

### 3. Run the Pipeline

```bash
# Basic run with default settings
./run_docker.sh run SSYouTubeonline

# With custom silence preset
./run_docker.sh run SSYouTubeonline --silence-preset sensitive

# With noise reduction
./run_docker.sh run SSYouTubeonline --reduce-noise

# With multiple options
./run_docker.sh run SSYouTubeonline \
    --silence-preset conservative \
    --reduce-noise \
    --transcription-model google
```

### 4. Check Results

```bash
# Results will be in the outputs folder
ls -la outputs/SSYouTubeonline/

# Check experiments data
ls -la experiments/experiment_data/SSYouTubeonline/
```

## 📚 Detailed Usage

### Container Management

```bash
# Start container
./run_docker.sh start

# Stop container
./run_docker.sh stop

# Check status
./run_docker.sh status

# View logs
./run_docker.sh logs

# Enter interactive shell
./run_docker.sh shell

# Clean up (removes container and volumes)
./run_docker.sh cleanup
```

### Running the Pipeline

The `run_docker.sh` script passes all arguments to `complete_pipeline.sh` inside the container.

#### Silence Detection Presets

```bash
# Very sensitive (word-level splits)
./run_docker.sh run VIDEO_ID --silence-preset very_sensitive

# Sensitive (phrase-level splits)
./run_docker.sh run VIDEO_ID --silence-preset sensitive

# Balanced (sentence-level, DEFAULT)
./run_docker.sh run VIDEO_ID --silence-preset balanced

# Conservative (paragraph-level)
./run_docker.sh run VIDEO_ID --silence-preset conservative

# Very conservative (major topic changes)
./run_docker.sh run VIDEO_ID --silence-preset very_conservative
```

#### Custom Parameters

```bash
# Custom silence threshold and duration
./run_docker.sh run VIDEO_ID \
    --custom-silence-thresh -32.0 \
    --custom-min-silence 650
```

#### Transcription Options

```bash
# Google only (default, fastest)
./run_docker.sh run VIDEO_ID --transcription-model google

# Whisper only (slower, more accurate)
./run_docker.sh run VIDEO_ID --transcription-model whisper

# Both models
./run_docker.sh run VIDEO_ID --transcription-model both
```

#### Skip Steps

```bash
# Skip specific steps
./run_docker.sh run VIDEO_ID --skip-step2 --skip-step3

# Only run chunking (Step 1)
./run_docker.sh run VIDEO_ID --skip-step2 --skip-step3 --skip-step4
```

### Manual Commands

```bash
# Enter container shell
./run_docker.sh shell

# Once inside, you can run any command:
cd /app/bengali-pipeline

# Run individual steps
python3 run_pipeline.py downloads/video.mp4 --silence-preset sensitive

# Check SyncNet
ls -la /app/syncnet_python/data/work/pytorchmodels/

# Run tests
python3 test_silence_presets.py

# Exit shell
exit
```

## 🔍 Troubleshooting

### Build Issues

**Problem**: `COPY ../syncnet_python failed`
```bash
# Solution: Ensure syncnet_python is in the parent directory
ls -la ../syncnet_python/
```

**Problem**: SyncNet model not found
```bash
# Solution: Verify model exists before building
ls -la ../syncnet_python/data/work/pytorchmodels/syncnet_v2.model
```

**Problem**: Build runs out of space
```bash
# Solution: Clean up Docker
docker system prune -a
docker volume prune
```

### Runtime Issues

**Problem**: Container exits immediately
```bash
# Check logs
./run_docker.sh logs

# Or check container status
docker-compose ps
```

**Problem**: GPU not detected
```bash
# Verify NVIDIA Docker is installed
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi

# If fails, reinstall nvidia-container-toolkit
```

**Problem**: Permission denied on output files
```bash
# Fix permissions (run on host)
sudo chown -R $USER:$USER outputs/ experiments/ logs/
```

**Problem**: Pipeline fails inside container
```bash
# Enter shell and debug
./run_docker.sh shell

# Check environment
echo $SYNCNET_REPO
echo $PYTHONPATH
ls -la /app/syncnet_python/

# Run with verbose logging
./complete_pipeline.sh VIDEO_ID --syncnet-repo /app/syncnet_python 2>&1 | tee debug.log
```

### Verification Commands

```bash
# Verify SyncNet is present
docker exec bengali-pipeline ls -la /app/syncnet_python/data/work/pytorchmodels/

# Verify Python can import modules
docker exec bengali-pipeline python3 -c "import sys; print(sys.path)"
docker exec bengali-pipeline python3 -c "from utils.split_by_silence import get_silence_preset; print(get_silence_preset('balanced'))"

# Check disk usage
./run_docker.sh status
```

## 📊 Performance Considerations

### CPU Mode (No GPU)
- Transcription: ~2-3x slower than GPU
- Face detection: Similar performance
- SyncNet: Significantly slower (~10x)

**Recommendation**: Use `--transcription-model google` for faster results on CPU.

### GPU Mode
- Full pipeline: 10-30 minutes for a 1-hour video
- Optimal for Whisper transcription and SyncNet filtering

### Memory Requirements
- Minimum: 8GB RAM
- Recommended: 16GB RAM
- GPU: 4GB+ VRAM

## 🔄 Updating the Image

When you modify the code:

```bash
# Rebuild the image
./run_docker.sh stop
./run_docker.sh build

# Restart
./run_docker.sh start
```

## 📦 What's Included (No Internet Required)

The Docker image contains:
- ✅ Python 3.10 and all dependencies
- ✅ Modified SyncNet with all customizations
- ✅ SyncNet pretrained model (syncnet_v2.model)
- ✅ Modified scenedetect library
- ✅ FFmpeg and audio processing tools
- ✅ OpenCV with CUDA support
- ✅ All Python packages (no pip install needed at runtime)
- ✅ Complete Bengali pipeline code

**Total image size**: ~5-8GB

## 🌐 Network Isolation

The container can run completely offline:
- No downloads during runtime
- All models included in the image
- Google Speech API requires internet (but is optional)

For **100% offline operation**:
```bash
./run_docker.sh run VIDEO_ID --transcription-model whisper
```

## 📝 Examples

### Example 1: Process a Single Video (Default)
```bash
# Copy video
cp ~/Videos/interview.mp4 downloads/interview.mp4

# Run pipeline
./run_docker.sh run interview

# Results in: experiments/experiment_data/interview/
```

### Example 2: High-Quality Dataset Creation
```bash
./run_docker.sh run video_001 \
    --silence-preset conservative \
    --reduce-noise \
    --transcription-model both
```

### Example 3: Quick Chunking Test
```bash
# Test different presets quickly
for preset in very_sensitive sensitive balanced conservative very_conservative; do
    echo "Testing $preset..."
    ./run_docker.sh run test_video \
        --silence-preset $preset \
        --skip-step2 --skip-step3 --skip-step4
done
```

### Example 4: Batch Processing
```bash
# Process multiple videos
for video in downloads/*.mp4; do
    VIDEO_ID=$(basename "$video" .mp4)
    echo "Processing $VIDEO_ID..."
    ./run_docker.sh run "$VIDEO_ID"
done
```

## 🆘 Support

For issues:
1. Check logs: `./run_docker.sh logs`
2. Enter shell: `./run_docker.sh shell`
3. Review documentation: `PIPELINE_README.md`
4. Check Docker status: `./run_docker.sh status`

## 📄 License

Same as the main project.

---

**Ready to go!** 🚀

Start with:
```bash
./run_docker.sh build
./run_docker.sh start
./run_docker.sh run YOUR_VIDEO_ID
```
