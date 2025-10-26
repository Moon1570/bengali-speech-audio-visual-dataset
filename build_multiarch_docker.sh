#!/bin/bash

# Multi-Architecture Docker Build Script for Bengali Speech Pipeline
# Builds for both Intel/AMD (amd64) and ARM64 architectures
# Supports NVIDIA GPU (on Linux) or CPU-only mode

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
IMAGE_NAME="${IMAGE_NAME:-bengali-speech-pipeline}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
PLATFORMS="linux/amd64,linux/arm64"
PUSH_TO_REGISTRY=false
REGISTRY_NAME=""

# Banner
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}   Bengali Speech Pipeline - Multi-Architecture Build${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --push)
            PUSH_TO_REGISTRY=true
            shift
            ;;
        --registry)
            REGISTRY_NAME="$2"
            shift 2
            ;;
        --tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        --help|-h)
            cat << EOF
${GREEN}Multi-Architecture Docker Build Script${NC}

${YELLOW}Usage:${NC}
  ./build_multiarch_docker.sh [options]

${YELLOW}Options:${NC}
  --push              Push image to registry after build
  --registry NAME     Docker registry (e.g., yourusername, ghcr.io/username)
  --tag TAG           Image tag (default: latest)
  --help              Show this help message

${YELLOW}Examples:${NC}
  # Build locally for both architectures
  ./build_multiarch_docker.sh

  # Build and push to Docker Hub
  ./build_multiarch_docker.sh --push --registry yourusername --tag v1.0

  # Build and push to GitHub Container Registry
  ./build_multiarch_docker.sh --push --registry ghcr.io/yourusername --tag latest

${YELLOW}What gets built:${NC}
  • Platform: linux/amd64 (Intel/AMD 64-bit)
  • Platform: linux/arm64 (Apple Silicon, ARM servers)
  • GPU: NVIDIA CUDA support (optional, Linux only)
  • CPU: Works on all platforms

${YELLOW}Image size:${NC}
  • ~9-10 GB per architecture
  • Multi-arch manifest allows automatic platform selection

${YELLOW}Requirements:${NC}
  • Docker with buildx support
  • For --push: Docker Hub or registry login
  • For GPU: NVIDIA Docker runtime (at runtime, not build time)

EOF
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Determine full image name
if [ -n "$REGISTRY_NAME" ]; then
    FULL_IMAGE_NAME="${REGISTRY_NAME}/${IMAGE_NAME}:${IMAGE_TAG}"
else
    FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"
fi

echo -e "${BLUE}Configuration:${NC}"
echo -e "  Image name: ${GREEN}${FULL_IMAGE_NAME}${NC}"
echo -e "  Platforms:  ${GREEN}${PLATFORMS}${NC}"
echo -e "  Push:       ${GREEN}${PUSH_TO_REGISTRY}${NC}"
echo ""

# Check Docker
echo -e "${YELLOW}[1/6]${NC} Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker found: $(docker --version)${NC}"

# Check buildx
echo -e "${YELLOW}[2/6]${NC} Checking Docker buildx..."
if ! docker buildx version &> /dev/null; then
    echo -e "${RED}❌ Docker buildx is not available${NC}"
    echo "Please update Docker to a version with buildx support (19.03+)"
    exit 1
fi
echo -e "${GREEN}✅ Docker buildx available${NC}"

# Check SyncNet directory
echo -e "${YELLOW}[3/6]${NC} Verifying SyncNet directory..."
SYNCNET_PATH="../syncnet_python"
if [ ! -d "$SYNCNET_PATH" ]; then
    echo -e "${RED}❌ SyncNet directory not found at: $SYNCNET_PATH${NC}"
    exit 1
fi
echo -e "${GREEN}✅ SyncNet directory found${NC}"

# Check SyncNet model
echo -e "${YELLOW}[4/6]${NC} Checking SyncNet model..."
SYNCNET_MODEL_1="$SYNCNET_PATH/data/syncnet_v2.model"
SYNCNET_MODEL_2="$SYNCNET_PATH/data/work/pytorchmodels/syncnet_v2.model"

if [ -f "$SYNCNET_MODEL_1" ]; then
    echo -e "${GREEN}✅ SyncNet model found ($(du -h "$SYNCNET_MODEL_1" | cut -f1))${NC}"
elif [ -f "$SYNCNET_MODEL_2" ]; then
    echo -e "${GREEN}✅ SyncNet model found ($(du -h "$SYNCNET_MODEL_2" | cut -f1))${NC}"
else
    echo -e "${RED}❌ SyncNet model not found${NC}"
    exit 1
fi

# Create/use builder
echo -e "${YELLOW}[5/6]${NC} Setting up multi-architecture builder..."
BUILDER_NAME="bengali-multiarch-builder"

if docker buildx inspect "$BUILDER_NAME" &> /dev/null; then
    echo -e "${GREEN}✅ Builder '$BUILDER_NAME' already exists${NC}"
    docker buildx use "$BUILDER_NAME"
else
    echo -e "${BLUE}Creating new builder: $BUILDER_NAME${NC}"
    docker buildx create --name "$BUILDER_NAME" --use --bootstrap
    echo -e "${GREEN}✅ Builder created and activated${NC}"
fi

# Show builder info
echo -e "${BLUE}Builder platforms:${NC}"
docker buildx inspect --bootstrap | grep "Platforms:" || true
echo ""

# Copy .dockerignore
echo -e "${YELLOW}[6/6]${NC} Preparing build context..."
if [ -f ".dockerignore.parent" ]; then
    cp .dockerignore.parent ../.dockerignore
    echo -e "${GREEN}✅ .dockerignore copied to parent directory${NC}"
fi
echo ""

# Summary
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ All prerequisites verified!${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo "The multi-architecture image will include:"
echo "  • Platform: linux/amd64 (Intel/AMD)"
echo "  • Platform: linux/arm64 (Apple Silicon, ARM servers)"
echo "  • Modified SyncNet with pretrained model"
echo "  • Complete Bengali pipeline"
echo "  • NVIDIA GPU support (optional at runtime)"
echo "  • CPU-only mode (works everywhere)"
echo ""

# Confirm
if [ "$PUSH_TO_REGISTRY" = true ]; then
    echo -e "${YELLOW}⚠️  Image will be PUSHED to: ${FULL_IMAGE_NAME}${NC}"
    echo ""
    read -p "Do you want to proceed? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Build cancelled.${NC}"
        exit 0
    fi
else
    echo -e "${BLUE}ℹ️  Image will be built and loaded locally (not pushed)${NC}"
    echo ""
    read -p "Do you want to proceed? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Build cancelled.${NC}"
        exit 0
    fi
fi

echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}   Starting Multi-Architecture Build${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo -e "${YELLOW}⏳ Building for: ${PLATFORMS}${NC}"
echo -e "${YELLOW}⏳ This will take 15-30 minutes (building for 2 architectures)${NC}"
echo ""

# Build command
BUILD_ARGS=(
    "buildx" "build"
    "--platform" "$PLATFORMS"
    "--file" "bengali-speech-audio-visual-dataset/Dockerfile"
    "--tag" "$FULL_IMAGE_NAME"
    "--progress" "plain"
)

# Add push or load flag
if [ "$PUSH_TO_REGISTRY" = true ]; then
    BUILD_ARGS+=("--push")
    echo -e "${BLUE}Mode: Building and pushing to registry${NC}"
else
    BUILD_ARGS+=("--load")
    echo -e "${BLUE}Mode: Building and loading locally${NC}"
    echo -e "${YELLOW}⚠️  Note: --load only works with single platform. Building for host platform.${NC}"
    # Detect host platform
    ARCH=$(uname -m)
    if [ "$ARCH" = "x86_64" ]; then
        HOST_PLATFORM="linux/amd64"
    elif [ "$ARCH" = "arm64" ] || [ "$ARCH" = "aarch64" ]; then
        HOST_PLATFORM="linux/arm64"
    else
        HOST_PLATFORM="linux/amd64"
    fi
    BUILD_ARGS[3]="$HOST_PLATFORM"  # Replace platforms
    echo -e "${BLUE}Building for: ${HOST_PLATFORM}${NC}"
fi

BUILD_ARGS+=(".")

# Navigate to parent directory and build
cd ..
echo -e "${CYAN}Build command:${NC}"
echo "docker ${BUILD_ARGS[@]}"
echo ""

# Execute build
if docker "${BUILD_ARGS[@]}" 2>&1 | tee bengali-speech-audio-visual-dataset/build_multiarch.log; then
    BUILD_SUCCESS=true
else
    BUILD_SUCCESS=false
fi

# Return to original directory
cd bengali-speech-audio-visual-dataset

echo ""
if [ "$BUILD_SUCCESS" = true ]; then
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}🎉 Multi-Architecture Build Successful!${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${GREEN}✅ Image: ${FULL_IMAGE_NAME}${NC}"
    
    if [ "$PUSH_TO_REGISTRY" = true ]; then
        echo -e "${GREEN}✅ Pushed to registry${NC}"
        echo ""
        echo "Users can now pull with:"
        echo -e "  ${CYAN}docker pull ${FULL_IMAGE_NAME}${NC}"
        echo ""
        echo "Docker will automatically pull the right architecture:"
        echo "  • Intel/AMD machines get: linux/amd64"
        echo "  • Apple Silicon gets: linux/arm64"
        echo "  • ARM servers get: linux/arm64"
    else
        echo -e "${GREEN}✅ Loaded locally for ${HOST_PLATFORM}${NC}"
        echo ""
        echo "To push a multi-arch image, use:"
        echo -e "  ${CYAN}./build_multiarch_docker.sh --push --registry yourusername${NC}"
    fi
    
    echo ""
    echo "Next steps:"
    echo "  1. Start container:  ./run_docker.sh start"
    echo "  2. Run pipeline:     ./run_docker.sh run VIDEO_ID"
    echo "  3. With GPU (Linux): ./run_docker.sh --gpu start"
    echo ""
    
    if [ "$PUSH_TO_REGISTRY" = true ]; then
        echo "Verify the manifest:"
        echo -e "  ${CYAN}docker buildx imagetools inspect ${FULL_IMAGE_NAME}${NC}"
        echo ""
    fi
else
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}❌ Build Failed!${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "Check build_multiarch.log for details"
    exit 1
fi
