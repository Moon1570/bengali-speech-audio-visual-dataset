#!/bin/bash

# Pre-build verification script
# Checks all requirements before attempting Docker build

set -e

echo "🔍 Bengali Speech Pipeline - Pre-Build Verification"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

ERRORS=0
WARNINGS=0

# Check 1: Docker
echo "Checking Docker..."
if command -v docker &> /dev/null; then
    echo "  ✅ Docker found: $(docker --version)"
else
    echo "  ❌ Docker not installed"
    ERRORS=$((ERRORS + 1))
fi

# Check 2: Docker Compose
echo "Checking Docker Compose..."
if command -v docker-compose &> /dev/null; then
    echo "  ✅ Docker Compose found: $(docker-compose --version)"
elif docker compose version &> /dev/null; then
    echo "  ✅ Docker Compose found (plugin): $(docker compose version)"
else
    echo "  ❌ Docker Compose not available"
    ERRORS=$((ERRORS + 1))
fi

# Check 3: SyncNet directory
echo "Checking SyncNet directory..."
if [ -d "../syncnet_python" ]; then
    echo "  ✅ SyncNet directory found"
    
    # Check for key files
    if [ -f "../syncnet_python/SyncNetInstance.py" ]; then
        echo "  ✅ SyncNetInstance.py found"
    else
        echo "  ⚠️  SyncNetInstance.py not found"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo "  ❌ SyncNet directory not found at ../syncnet_python"
    echo "     Expected: Research/Audio Visual/Code/syncnet_python/"
    ERRORS=$((ERRORS + 1))
fi

# Check 4: SyncNet model
echo "Checking SyncNet pretrained model..."
if [ -f "../syncnet_python/data/syncnet_v2.model" ]; then
    SIZE=$(du -h "../syncnet_python/data/syncnet_v2.model" | cut -f1)
    echo "  ✅ SyncNet model found at data/syncnet_v2.model ($SIZE)"
elif [ -f "../syncnet_python/data/work/pytorchmodels/syncnet_v2.model" ]; then
    SIZE=$(du -h "../syncnet_python/data/work/pytorchmodels/syncnet_v2.model" | cut -f1)
    echo "  ✅ SyncNet model found at data/work/pytorchmodels/syncnet_v2.model ($SIZE)"
else
    echo "  ❌ SyncNet model not found"
    echo "     Checked locations:"
    echo "       - ../syncnet_python/data/syncnet_v2.model"
    echo "       - ../syncnet_python/data/work/pytorchmodels/syncnet_v2.model"
    ERRORS=$((ERRORS + 1))
fi

# Check 5: Modified libraries
echo "Checking modified libraries..."
if [ -d "../syncnet_python/scenedetect" ]; then
    echo "  ✅ Modified scenedetect found"
else
    echo "  ⚠️  Modified scenedetect not found"
    echo "     If you have a modified scenedetect, place it in ../syncnet_python/scenedetect"
    WARNINGS=$((WARNINGS + 1))
fi

# Check 6: Disk space
echo "Checking disk space..."
if command -v df &> /dev/null; then
    AVAILABLE=$(df -h . | awk 'NR==2 {print $4}')
    echo "  ℹ️  Available space: $AVAILABLE"
    
    # Try to get numeric value (in GB)
    AVAILABLE_GB=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ "$AVAILABLE_GB" -lt 10 ]; then
        echo "  ⚠️  Less than 10GB free space"
        WARNINGS=$((WARNINGS + 1))
    else
        echo "  ✅ Sufficient space available"
    fi
fi

# Check 7: NVIDIA Docker (optional)
echo "Checking GPU support (optional)..."
if docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi &> /dev/null 2>&1; then
    echo "  ✅ NVIDIA Docker available - GPU acceleration will work"
else
    echo "  ⚠️  NVIDIA Docker not available - will run in CPU mode"
    echo "     (This is fine, but processing will be slower)"
    WARNINGS=$((WARNINGS + 1))
fi

# Check 8: Required files
echo "Checking required files in current directory..."
REQUIRED_FILES=("Dockerfile" "docker-compose.yml" "run_docker.sh" "requirements.txt" "complete_pipeline.sh")
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file found"
    else
        echo "  ❌ $file not found"
        ERRORS=$((ERRORS + 1))
    fi
done

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Summary:"
echo "  Errors: $ERRORS"
echo "  Warnings: $WARNINGS"
echo ""

if [ $ERRORS -eq 0 ]; then
    if [ $WARNINGS -eq 0 ]; then
        echo "✅ All checks passed! You're ready to build."
        echo ""
        echo "Next step:"
        echo "  ./build_docker.sh"
    else
        echo "⚠️  All critical checks passed, but there are $WARNINGS warning(s)."
        echo "   You can proceed with the build, but review the warnings above."
        echo ""
        echo "Next step:"
        echo "  ./build_docker.sh"
    fi
    exit 0
else
    echo "❌ Found $ERRORS error(s). Please fix them before building."
    echo ""
    echo "Common solutions:"
    echo ""
    echo "1. SyncNet not found:"
    echo "   Ensure syncnet_python is in: Research/Audio Visual/Code/syncnet_python/"
    echo ""
    echo "2. Model not found:"
    echo "   Download the model:"
    echo "   mkdir -p ../syncnet_python/data/work/pytorchmodels/"
    echo "   cd ../syncnet_python/data/work/pytorchmodels/"
    echo "   wget http://www.robots.ox.ac.uk/~vgg/software/lipsync/data/syncnet_v2.model"
    echo ""
    echo "3. Docker not installed:"
    echo "   Install Docker Desktop: https://www.docker.com/products/docker-desktop"
    echo ""
    exit 1
fi
