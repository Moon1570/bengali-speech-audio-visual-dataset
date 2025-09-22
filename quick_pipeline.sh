#!/bin/bash

# Quick Pipeline Runner - Simplified version of complete_pipeline.sh
# ==================================================================
# This script provides a quick way to run the pipeline with minimal configuration

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Check if video ID is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <video_id>"
    echo "Example: $0 efhkN7e8238"
    exit 1
fi

VIDEO_ID=$1
CURRENT_REPO="/Users/darklord/Research/Audio Visual/Code/bengali-speech-audio-visual-dataset"
SYNCNET_REPO="/Users/darklord/Research/Audio Visual/Code/syncnet_python"

print_status "==================================="
print_status "Quick Pipeline for Video: $VIDEO_ID"
print_status "==================================="

cd "$CURRENT_REPO"

# Step 1: Create chunks (quick version)
print_status "Step 1: Creating chunks..."
python run_pipeline.py "downloads/${VIDEO_ID}.mp4" --filter-faces --refine-chunks --min-chunk-duration 2

# Step 2: Copy video chunks to SyncNet and filter
print_status "Step 2: SyncNet filtering..."
mkdir -p "${SYNCNET_REPO}/data"
cp -r "outputs/${VIDEO_ID}/chunks/video" "${SYNCNET_REPO}/data/${VIDEO_ID}"
cd "$SYNCNET_REPO"
python filter_videos_by_sync_score.py --input_dir "data/${VIDEO_ID}" --output_dir "results/${VIDEO_ID}/" --preset high --max_worker 8

# Step 3: Organize (if script exists)
if [ -f "utils/directory_prepare.py" ]; then
    print_status "Step 3: Organizing directories..."
    python utils/directory_prepare.py --input_dir "results/${VIDEO_ID}/good_quality" --output_dir "${VIDEO_ID}" --max_workers 8
    cd "$CURRENT_REPO"
    mkdir -p "experiments/experiment_data"
    cp -r "${SYNCNET_REPO}/${VIDEO_ID}" "experiments/experiment_data/"
else
    print_status "Step 3: Skipping organization (script not found)"
fi

# Step 4: Transcription
cd "$CURRENT_REPO"
if [ -d "experiments/experiment_data/${VIDEO_ID}/video_normal" ]; then
    print_status "Step 4: Running transcription..."
    python run_transcription_pipeline_modular.py --path "experiments/experiment_data/${VIDEO_ID}/video_normal" --model both --batch
else
    print_status "Step 4: Video normal directory not found, skipping transcription"
fi

print_success "Quick pipeline completed for ${VIDEO_ID}!"
