#!/bin/bash
# Run transcription on HOST machine (outside Docker)
# Use this when Docker transcription fails

set -e

if [ $# -lt 1 ]; then
    echo "Usage: $0 <video_id> [model]"
    echo ""
    echo "Examples:"
    echo "  $0 A00000000_test"
    echo "  $0 efhkN7e8238 google"
    echo "  $0 hxhLGCguRO0 whisper"
    exit 1
fi

VIDEO_ID="$1"
MODEL="${2:-google}"
VIDEO_NORMAL_DIR="experiments/experiment_data/${VIDEO_ID}/video_normal"

if [ ! -d "$VIDEO_NORMAL_DIR" ]; then
    echo "❌ Video directory not found: $VIDEO_NORMAL_DIR"
    echo "Run steps 1-3 first to create the organized videos"
    exit 1
fi

echo "🚀 Running transcription on HOST machine (outside Docker)"
echo "Video ID: $VIDEO_ID"
echo "Model: $MODEL"
echo "Path: $VIDEO_NORMAL_DIR"
echo ""

# Activate virtual environment
source .venv/bin/activate

# Run transcription
python run_transcription_pipeline_modular.py \
    --path "$VIDEO_NORMAL_DIR" \
    --model "$MODEL" \
    --batch

echo ""
echo "✅ Transcription completed!"
echo "Results: experiments/experiment_data/${VIDEO_ID}/${MODEL}_transcription/"
