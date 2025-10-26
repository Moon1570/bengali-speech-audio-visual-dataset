#!/bin/bash

# Push Bengali Speech Pipeline Docker Image to Docker Hub
# Supports both single and multi-architecture images

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
DOCKER_USERNAME="moon1570"
IMAGE_NAME="bengali-speech-pipeline"
VERSION="v1.0"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}   Bengali Speech Pipeline - Docker Push Script${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    exit 1
fi

# Check if image exists
if ! docker images | grep -q "bengali-speech-pipeline"; then
    echo -e "${RED}❌ Image 'bengali-speech-pipeline:latest' not found${NC}"
    echo "Please build the image first with: ./build_multiarch_docker.sh"
    exit 1
fi

echo -e "${GREEN}✅ Image found: bengali-speech-pipeline:latest${NC}"
echo ""

# Check if logged in to Docker Hub
echo -e "${YELLOW}Checking Docker Hub authentication...${NC}"
if ! docker info | grep -q "Username: $DOCKER_USERNAME"; then
    echo -e "${YELLOW}⚠️  Not logged in to Docker Hub${NC}"
    echo "Please login with your Docker Hub credentials:"
    echo ""
    docker login
    echo ""
else
    echo -e "${GREEN}✅ Already logged in as $DOCKER_USERNAME${NC}"
    echo ""
fi

# Tag the image
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Tagging image...${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Tag with version
echo -e "${BLUE}[1/2]${NC} Tagging as ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION}"
docker tag bengali-speech-pipeline:latest ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION}

# Tag as latest
echo -e "${BLUE}[2/2]${NC} Tagging as ${DOCKER_USERNAME}/${IMAGE_NAME}:latest"
docker tag bengali-speech-pipeline:latest ${DOCKER_USERNAME}/${IMAGE_NAME}:latest

echo -e "${GREEN}✅ Images tagged successfully${NC}"
echo ""

# Show what will be pushed
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo "The following images will be pushed to Docker Hub:"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
docker images | grep "${DOCKER_USERNAME}/${IMAGE_NAME}" || true
echo ""

# Get image size
IMAGE_SIZE=$(docker images bengali-speech-pipeline:latest --format '{{.Size}}')
echo -e "${YELLOW}⚠️  Note: Image size is ${IMAGE_SIZE} - upload may take several minutes${NC}"
echo ""

# Ask for confirmation
read -p "Do you want to push these images to Docker Hub? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Push cancelled.${NC}"
    exit 0
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Pushing to Docker Hub...${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Push version tag
echo -e "${BLUE}[1/2]${NC} Pushing ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION}..."
docker push ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION}

echo ""
echo -e "${BLUE}[2/2]${NC} Pushing ${DOCKER_USERNAME}/${IMAGE_NAME}:latest..."
docker push ${DOCKER_USERNAME}/${IMAGE_NAME}:latest

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🎉 Successfully pushed to Docker Hub!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${GREEN}✅ Your image is now available at:${NC}"
echo -e "${BLUE}   https://hub.docker.com/r/${DOCKER_USERNAME}/${IMAGE_NAME}${NC}"
echo ""
echo -e "${GREEN}Users can pull it with:${NC}"
echo -e "${YELLOW}   docker pull ${DOCKER_USERNAME}/${IMAGE_NAME}:latest${NC}"
echo -e "${YELLOW}   docker pull ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION}${NC}"
echo ""
echo -e "${GREEN}Architecture support:${NC}"
ARCH=$(docker image inspect bengali-speech-pipeline:latest --format '{{.Architecture}}' 2>/dev/null || echo "unknown")
echo "   - Current build: ${ARCH}"
echo "   - NVIDIA GPU: Supported (with --gpu flag on Linux)"
echo "   - CPU-only: Supported (all platforms)"
echo ""
