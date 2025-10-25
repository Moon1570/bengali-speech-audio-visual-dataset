#!/bin/bash

# Build script for Bengali Speech Pipeline Docker Image
# This script ensures all prerequisites are met before building

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}   Bengali Speech Pipeline - Docker Build Script${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check Docker
echo -e "${YELLOW}[1/5]${NC} Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi
echo -e "${GREEN}✅ Docker found: $(docker --version)${NC}"
echo ""

# Check Docker Compose
echo -e "${YELLOW}[2/5]${NC} Checking Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}⚠️  Docker Compose not found as standalone command${NC}"
    echo "Checking if it's available as 'docker compose'..."
    if ! docker compose version &> /dev/null; then
        echo -e "${RED}❌ Docker Compose is not available${NC}"
        exit 1
    else
        echo -e "${GREEN}✅ Docker Compose found (plugin): $(docker compose version)${NC}"
        # Create alias for docker-compose
        alias docker-compose='docker compose'
    fi
else
    echo -e "${GREEN}✅ Docker Compose found: $(docker-compose --version)${NC}"
fi
echo ""

# Check SyncNet directory
echo -e "${YELLOW}[3/5]${NC} Verifying SyncNet directory structure..."
SYNCNET_PATH="../syncnet_python"

if [ ! -d "$SYNCNET_PATH" ]; then
    echo -e "${RED}❌ SyncNet directory not found at: $SYNCNET_PATH${NC}"
    echo ""
    echo "Expected directory structure:"
    echo "  Research/Audio Visual/Code/"
    echo "  ├── bengali-speech-audio-visual-dataset/  (current directory)"
    echo "  └── syncnet_python/                        (required!)"
    echo ""
    echo "Please ensure your modified syncnet_python is in the parent directory."
    exit 1
fi
echo -e "${GREEN}✅ SyncNet directory found${NC}"

# Check for SyncNet model
echo -e "${YELLOW}[4/5]${NC} Checking for SyncNet pretrained model..."
SYNCNET_MODEL_1="$SYNCNET_PATH/data/syncnet_v2.model"
SYNCNET_MODEL_2="$SYNCNET_PATH/data/work/pytorchmodels/syncnet_v2.model"

if [ -f "$SYNCNET_MODEL_1" ]; then
    SYNCNET_MODEL="$SYNCNET_MODEL_1"
    echo -e "${GREEN}✅ SyncNet model found at data/syncnet_v2.model ($(du -h "$SYNCNET_MODEL" | cut -f1))${NC}"
elif [ -f "$SYNCNET_MODEL_2" ]; then
    SYNCNET_MODEL="$SYNCNET_MODEL_2"
    echo -e "${GREEN}✅ SyncNet model found at data/work/pytorchmodels/syncnet_v2.model ($(du -h "$SYNCNET_MODEL" | cut -f1))${NC}"
else
    echo -e "${RED}❌ SyncNet model not found at either location${NC}"
    echo ""
    echo "The pretrained model must be present before building Docker image."
    echo "Checked locations:"
    echo "  - syncnet_python/data/syncnet_v2.model"
    echo "  - syncnet_python/data/work/pytorchmodels/syncnet_v2.model"
    echo ""
    echo "Please ensure the model file exists or download it:"
    echo "  mkdir -p $SYNCNET_PATH/data/work/pytorchmodels"
    echo "  cd $SYNCNET_PATH/data/work/pytorchmodels"
    echo "  wget http://www.robots.ox.ac.uk/~vgg/software/lipsync/data/syncnet_v2.model"
    exit 1
fi

# Check modified scenedetect
echo ""
echo -e "${YELLOW}[5/5]${NC} Checking for modified libraries..."
if [ -d "$SYNCNET_PATH/scenedetect" ]; then
    echo -e "${GREEN}✅ Modified scenedetect library found${NC}"
else
    echo -e "${YELLOW}⚠️  Modified scenedetect directory not found${NC}"
    echo "   If you have modified scenedetect, ensure it's in: $SYNCNET_PATH/scenedetect"
fi
echo ""

# Display summary
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ All prerequisites verified!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Show what will be included
echo "The Docker image will include:"
echo "  • Modified SyncNet with all customizations"
echo "  • Pretrained SyncNet model (no download needed)"
echo "  • Modified scenedetect library"
echo "  • Complete Bengali pipeline with all dependencies"
echo "  • All silence detection presets"
echo "  • GPU support (if nvidia-docker is available)"
echo ""

# Ask for confirmation
read -p "Do you want to proceed with building the Docker image? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Build cancelled.${NC}"
    exit 0
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}   Starting Docker Build${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Build the image
echo -e "${YELLOW}Building Docker image...${NC}"
echo "This may take 5-10 minutes on the first build."
echo ""
echo "Building from parent directory to include both repositories..."
echo ""

# Copy .dockerignore to parent directory
cp .dockerignore.parent ../.dockerignore

# Build from parent directory so both syncnet_python and bengali-pipeline are in context
cd .. && docker build -f bengali-speech-audio-visual-dataset/Dockerfile -t bengali-speech-pipeline:latest . 2>&1 | tee bengali-speech-audio-visual-dataset/build.log
BUILD_EXIT_CODE=${PIPESTATUS[0]}
cd bengali-speech-audio-visual-dataset

if [ $BUILD_EXIT_CODE -eq 0 ]; then
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}🎉 Docker image built successfully!${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "Image name: bengali-speech-pipeline:latest"
    echo "Image size: $(docker images bengali-speech-pipeline:latest --format '{{.Size}}')"
    echo ""
    echo "Next steps:"
    echo "  1. Start the container:  ./run_docker.sh start"
    echo "  2. Run the pipeline:     ./run_docker.sh run YOUR_VIDEO_ID"
    echo "  3. View help:            ./run_docker.sh help"
    echo ""
    echo "For detailed usage, see: DOCKER_GUIDE.md"
    echo ""
else
    echo ""
    echo -e "${RED}❌ Docker build failed!${NC}"
    echo ""
    echo "Check build.log for details."
    echo "Common issues:"
    echo "  • Insufficient disk space (need 10GB+)"
    echo "  • Network issues downloading base images"
    echo "  • Missing SyncNet files"
    echo ""
    exit 1
fi
