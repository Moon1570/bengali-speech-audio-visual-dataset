# Multi-stage Dockerfile for Bengali Speech Audio-Visual Dataset Pipeline
# Includes modified SyncNet and all dependencies (no internet downloads required)
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04 AS base

# Prevent interactive prompts during build
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV TZ=UTC

# Install system dependencies
# Note: Installing both 'flac' command-line tool and 'libflac-dev' development libraries
# The 'flac' package provides the /usr/bin/flac encoder needed by SpeechRecognition
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    python3-dev \
    git \
    wget \
    curl \
    ffmpeg \
    flac \
    libflac-dev \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libglib2.0-0 \
    libgl1-mesa-glx \
    portaudio19-dev \
    && rm -rf /var/lib/apt/lists/*

# Create FLAC wrapper script using ffmpeg (flac package not available on ARM64)
# SpeechRecognition library expects 'flac' command to convert WAV to FLAC
RUN echo '#!/bin/bash\n\
# FLAC wrapper using ffmpeg\n\
# The flac command-line tool is not available in Ubuntu ARM64 repos\n\
# This wrapper provides the same interface using ffmpeg\n\
\n\
if [ "$#" -eq 0 ]; then\n\
    echo "flac 1.3.3 (ffmpeg wrapper)"\n\
    echo "Copyright (C) 2000-2009  Josh Coalson, 2011-2016  Xiph.Org Foundation"\n\
    exit 0\n\
fi\n\
\n\
# Parse arguments (simplified for SpeechRecognition use case)\n\
INPUT_FILE=""\n\
OUTPUT_FILE=""\n\
SILENT=false\n\
\n\
while [ "$#" -gt 0 ]; do\n\
    case "$1" in\n\
        --totally-silent|-s)\n\
            SILENT=true\n\
            shift\n\
            ;;\n\
        -o)\n\
            OUTPUT_FILE="$2"\n\
            shift 2\n\
            ;;\n\
        --stdout|--force-raw-format|--endian=*|--sign=*)\n\
            shift\n\
            ;;\n\
        -*)\n\
            shift\n\
            ;;\n\
        *)\n\
            INPUT_FILE="$1"\n\
            shift\n\
            ;;\n\
    esac\n\
done\n\
\n\
# Convert using ffmpeg\n\
if [ "$INPUT_FILE" = "-" ] || [ -z "$INPUT_FILE" ]; then\n\
    # Read from stdin, write to stdout (most common case for SpeechRecognition)\n\
    ffmpeg -f wav -i pipe:0 -f flac pipe:1 2>/dev/null\n\
elif [ -n "$INPUT_FILE" ] && [ -n "$OUTPUT_FILE" ]; then\n\
    # Read from file, write to file\n\
    if [ "$SILENT" = true ]; then\n\
        ffmpeg -i "$INPUT_FILE" -f flac "$OUTPUT_FILE" -y >/dev/null 2>&1\n\
    else\n\
        ffmpeg -i "$INPUT_FILE" -f flac "$OUTPUT_FILE" -y 2>&1 | grep -v "^ffmpeg version" | grep -v "^  built with" | grep -v "^  configuration:" | grep -v "^  lib" || true\n\
    fi\n\
elif [ -n "$INPUT_FILE" ]; then\n\
    # Output to stdout\n\
    ffmpeg -i "$INPUT_FILE" -f flac pipe:1 2>/dev/null\n\
fi\n' > /usr/local/bin/flac && chmod +x /usr/local/bin/flac

# Create working directory
WORKDIR /app

# Copy Bengali pipeline requirements first for better caching
COPY bengali-speech-audio-visual-dataset/requirements.txt /app/bengali-pipeline/requirements.txt

# Install Bengali pipeline Python dependencies
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir -r /app/bengali-pipeline/requirements.txt

# Copy local modified SyncNet (includes all modifications, data, weights, and modified libs)
# Build context should be the parent directory containing both repos
COPY syncnet_python /app/syncnet_python

# Install SyncNet dependencies if requirements.txt exists
RUN if [ -f /app/syncnet_python/requirements.txt ]; then \
        pip3 install --no-cache-dir -r /app/syncnet_python/requirements.txt; \
    fi

# Copy modified scenedetect library if it exists in syncnet
# This ensures our custom modifications are included
RUN if [ -d /app/syncnet_python/scenedetect ]; then \
        cd /app/syncnet_python/scenedetect && \
        pip3 install --no-cache-dir -e .; \
    fi

# Copy Bengali speech pipeline code
WORKDIR /app/bengali-pipeline
COPY bengali-speech-audio-visual-dataset/ .

# Create necessary directories
RUN mkdir -p \
    downloads \
    outputs \
    experiments/experiment_data \
    logs \
    /app/syncnet_python/results

# Verify that SyncNet data and weights are present
RUN echo "Verifying SyncNet setup..." && \
    if [ -d /app/syncnet_python/data ]; then \
        echo "✓ SyncNet data directory found"; \
        ls -la /app/syncnet_python/data/ | head -20; \
    else \
        echo "⚠ Warning: SyncNet data directory not found"; \
    fi && \
    if [ -f /app/syncnet_python/data/syncnet_v2.model ]; then \
        echo "✓ SyncNet pretrained model found at data/syncnet_v2.model"; \
        du -h /app/syncnet_python/data/syncnet_v2.model; \
    elif [ -f /app/syncnet_python/data/work/pytorchmodels/syncnet_v2.model ]; then \
        echo "✓ SyncNet pretrained model found at data/work/pytorchmodels/syncnet_v2.model"; \
        du -h /app/syncnet_python/data/work/pytorchmodels/syncnet_v2.model; \
    else \
        echo "⚠ Warning: SyncNet model not found at either location"; \
        echo "   Checked: data/syncnet_v2.model and data/work/pytorchmodels/syncnet_v2.model"; \
    fi

# Set permissions
RUN chmod +x complete_pipeline.sh || true

# Create entrypoint script
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# Set up Python environment\n\
export PATH=/usr/bin:$PATH\n\
export PYTHONPATH=/app/bengali-pipeline:/app/syncnet_python:$PYTHONPATH\n\
\n\
# Display environment info\n\
echo "🐍 Python version: $(python3 --version)"\n\
echo "📁 Working directory: $(pwd)"\n\
echo "🔧 SyncNet location: $SYNCNET_REPO"\n\
echo "📦 Pipeline location: $CURRENT_REPO"\n\
\n\
# Verify SyncNet availability\n\
if [ -d "$SYNCNET_REPO" ]; then\n\
    echo "✅ SyncNet repository found"\n\
else\n\
    echo "❌ Error: SyncNet repository not found at $SYNCNET_REPO"\n\
fi\n\
\n\
# Execute command\n\
exec "$@"\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Set environment variables
ENV SYNCNET_REPO=/app/syncnet_python
ENV CURRENT_REPO=/app/bengali-pipeline
ENV PATH=/app/bengali-pipeline:$PATH
ENV PYTHONPATH=/app/bengali-pipeline:/app/syncnet_python:$PYTHONPATH

WORKDIR /app/bengali-pipeline

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["bash"]
