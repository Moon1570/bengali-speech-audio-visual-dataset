#!/bin/bash

# Bengali Speech Audio-Visual Dataset - Complete Processing Pipeline
# ====================================================================
# This script automates the entire pipeline from video processing to transcription
# 
# Usage: ./complete_pipeline.sh <video_file_id> [options]
# Example: ./complete_pipeline.sh efhkN7e8238 --max-workers 8

set -e  # Exit on any error

# Configuration - Use command line provided paths
DEFAULT_MAX_WORKERS=8
DEFAULT_MIN_CHUNK_DURATION=2

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check dependencies
check_dependencies() {
    print_status "Checking dependencies..."
    
    if ! command_exists python; then
        print_error "Python is not installed or not in PATH"
        exit 1
    fi
    
    print_success "Dependencies check passed"
}

# Function to display usage
usage() {
    echo "Usage: $0 <video_id> [options]"
    echo ""
    echo "Arguments:"
    echo "  video_id                Video ID (e.g., efhkN7e8238)"
    echo ""
    echo "Options:"
    echo "  --current-repo PATH     Path to current repository (auto-detected if not provided)"
    echo "  --syncnet-repo PATH     Path to SyncNet repository (required)"
    echo "  --max-workers NUM       Maximum number of workers (default: $DEFAULT_MAX_WORKERS)"
    echo "  --min-chunk-duration NUM Minimum chunk duration in seconds (default: $DEFAULT_MIN_CHUNK_DURATION)"
    echo "  --preset PRESET         SyncNet preset (low/medium/high, default: high)"
    echo "  --skip-step1            Skip step 1 (chunk creation)"
    echo "  --skip-step2            Skip step 2 (SyncNet filtering)"
    echo "  --skip-step3            Skip step 3 (directory organization)"
    echo "  --skip-step4            Skip step 4 (transcription)"
    echo "  --help                  Show this help message"
    echo ""
    echo "Examples:"
    echo "  # Mac:"
    echo "  $0 efhkN7e8238 --syncnet-repo /Users/darklord/Research/Audio\\ Visual/Code/syncnet_python"
    echo ""
    echo "  # WSL:"  
    echo "  $0 efhkN7e8238 --syncnet-repo /home/\$USER/thesis/syncnet_python"
    echo ""
    echo "  # With custom current repo:"
    echo "  $0 efhkN7e8238 --current-repo /path/to/bengali-dataset --syncnet-repo /path/to/syncnet"
}

# Parse command line arguments
VIDEO_ID=""
CURRENT_REPO=""
SYNCNET_REPO=""
MAX_WORKERS=$DEFAULT_MAX_WORKERS
MIN_CHUNK_DURATION=$DEFAULT_MIN_CHUNK_DURATION
PRESET="high"
SKIP_STEP1=false
SKIP_STEP2=false
SKIP_STEP3=false
SKIP_STEP4=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --current-repo)
            CURRENT_REPO="$2"
            shift 2
            ;;
        --syncnet-repo)
            SYNCNET_REPO="$2"
            shift 2
            ;;
        --max-workers)
            MAX_WORKERS="$2"
            shift 2
            ;;
        --min-chunk-duration)
            MIN_CHUNK_DURATION="$2"
            shift 2
            ;;
        --preset)
            PRESET="$2"
            shift 2
            ;;
        --skip-step1)
            SKIP_STEP1=true
            shift
            ;;
        --skip-step2)
            SKIP_STEP2=true
            shift
            ;;
        --skip-step3)
            SKIP_STEP3=true
            shift
            ;;
        --skip-step4)
            SKIP_STEP4=true
            shift
            ;;
        --help)
            usage
            exit 0
            ;;
        -*)
            print_error "Unknown option: $1"
            usage
            exit 1
            ;;
        *)
            if [ -z "$VIDEO_ID" ]; then
                VIDEO_ID="$1"
            else
                print_error "Multiple video IDs specified. Only one is allowed."
                usage
                exit 1
            fi
            shift
            ;;
    esac
done
            ;;
        --min-chunk-duration)
            MIN_CHUNK_DURATION="$2"
            shift 2
            ;;
        --preset)
            PRESET="$2"
            shift 2
            ;;
        --skip-step1)
            SKIP_STEP1=true
            shift
            ;;
        --skip-step2)
            SKIP_STEP2=true
            shift
            ;;
        --skip-step3)
            SKIP_STEP3=true
            shift
            ;;
        --skip-step4)
            SKIP_STEP4=true
            shift
            ;;
        --help)
            usage
            exit 0
            ;;
        -*)
            print_error "Unknown option: $1"
            usage
            exit 1
            ;;
        *)
            if [ -z "$VIDEO_ID" ]; then
                VIDEO_ID="$1"
            else
                print_error "Multiple video IDs specified. Only one is allowed."
                usage
                exit 1
            fi
            shift
            ;;
    esac
done

# Validate arguments
if [ -z "$VIDEO_ID" ]; then
    print_error "Video ID is required"
    usage
    exit 1
fi

# Set default current repo if not provided
if [ -z "$CURRENT_REPO" ]; then
    CURRENT_REPO="$(pwd)"
    print_status "Using current directory as repo: $CURRENT_REPO"
fi

# Validate SyncNet repo is provided
if [ -z "$SYNCNET_REPO" ]; then
    print_error "SyncNet repository path is required"
    print_error "Please specify --syncnet-repo PATH"
    print_error ""
    print_error "Common locations:"
    print_error "  Mac: /Users/\$USER/Research/Audio\\ Visual/Code/syncnet_python"
    print_error "  WSL: /home/\$USER/thesis/syncnet_python"
    usage
    exit 1
fi

# Validate paths exist
if [ ! -d "$CURRENT_REPO" ]; then
    print_error "Current repository path does not exist: $CURRENT_REPO"
    exit 1
fi

if [ ! -d "$SYNCNET_REPO" ]; then
    print_error "SyncNet repository path does not exist: $SYNCNET_REPO"
    exit 1
fi

# Convert to absolute paths
CURRENT_REPO="$(realpath "$CURRENT_REPO")"
SYNCNET_REPO="$(realpath "$SYNCNET_REPO")"

# Validate numeric arguments
if ! [[ "$MAX_WORKERS" =~ ^[0-9]+$ ]] || [ "$MAX_WORKERS" -lt 1 ]; then
    print_error "max-workers must be a positive integer"
    exit 1
fi

if ! [[ "$MIN_CHUNK_DURATION" =~ ^[0-9]+(\.[0-9]+)?$ ]]; then
    print_error "min-chunk-duration must be a positive number"
    exit 1
fi

# Validate preset
if [[ ! "$PRESET" =~ ^(low|medium|high)$ ]]; then
    print_error "preset must be one of: low, medium, high"
    exit 1
fi

# Start pipeline
print_status "==================================================================="
print_status "Bengali Speech Audio-Visual Dataset - Complete Processing Pipeline"
print_status "==================================================================="
print_status "Video ID: $VIDEO_ID"
print_status "Current Repository: $CURRENT_REPO"
print_status "SyncNet Repository: $SYNCNET_REPO"
print_status "Max Workers: $MAX_WORKERS"
print_status "Min Chunk Duration: ${MIN_CHUNK_DURATION}s"
print_status "SyncNet Preset: $PRESET"
print_status "==================================================================="

# Check dependencies
check_dependencies

# Change to the main repository directory
cd "$CURRENT_REPO"

# Step 1: Create chunks
if [ "$SKIP_STEP1" = false ]; then
    print_status "Step 1: Creating chunks from video..."
    
    VIDEO_FILE="downloads/${VIDEO_ID}.mp4"
    if [ ! -f "$VIDEO_FILE" ]; then
        print_error "Video file not found: $VIDEO_FILE"
        print_error "Please ensure the video file exists in the downloads directory"
        exit 1
    fi
    
    print_status "Running: python run_pipeline.py $VIDEO_FILE --filter-faces --refine-chunks --min-chunk-duration $MIN_CHUNK_DURATION"
    
    if python run_pipeline.py "$VIDEO_FILE" --filter-faces --refine-chunks --min-chunk-duration "$MIN_CHUNK_DURATION"; then
        print_success "Step 1 completed: Chunks created in outputs/${VIDEO_ID}/"
    else
        print_error "Step 1 failed: Chunk creation failed"
        exit 1
    fi
else
    print_warning "Step 1 skipped: Chunk creation"
fi

# Step 2: Filter chunks using SyncNet
if [ "$SKIP_STEP2" = false ]; then
    print_status "Step 2: Filtering chunks using SyncNet..."
    
    OUTPUT_DIR="outputs/${VIDEO_ID}"
    SYNCNET_INPUT_DIR="${SYNCNET_REPO}/data/${VIDEO_ID}"
    SYNCNET_OUTPUT_DIR="${SYNCNET_REPO}/results/${VIDEO_ID}"
    
    # Check if output directory exists
    if [ ! -d "$OUTPUT_DIR" ]; then
        print_error "Output directory not found: $OUTPUT_DIR"
        print_error "Please run step 1 first or use --skip-step1 if chunks already exist"
        exit 1
    fi
    
    # Copy chunks/video folder to SyncNet repo (SyncNet expects video chunks specifically)
    print_status "Copying video chunks to SyncNet repository..."
    CHUNKS_VIDEO_DIR="${OUTPUT_DIR}/chunks/video"
    
    if [ ! -d "$CHUNKS_VIDEO_DIR" ]; then
        print_error "Video chunks directory not found: $CHUNKS_VIDEO_DIR"
        print_error "Expected structure: outputs/${VIDEO_ID}/chunks/video/"
        exit 1
    fi
    
    if [ -d "$SYNCNET_INPUT_DIR" ]; then
        print_warning "Removing existing data in SyncNet repo: $SYNCNET_INPUT_DIR"
        rm -rf "$SYNCNET_INPUT_DIR"
    fi
    
    mkdir -p "$(dirname "$SYNCNET_INPUT_DIR")"
    cp -r "$CHUNKS_VIDEO_DIR" "$SYNCNET_INPUT_DIR"
    print_success "Video chunks copied to: $SYNCNET_INPUT_DIR"
    
    # Change to SyncNet directory and run filtering
    print_status "Changing to SyncNet directory: $SYNCNET_REPO"
    cd "$SYNCNET_REPO"
    
    print_status "Running SyncNet filtering with preset '$PRESET' and $MAX_WORKERS workers..."
    print_status "Command: python filter_videos_by_sync_score.py --input_dir data/${VIDEO_ID} --output_dir results/${VIDEO_ID}/ --preset $PRESET --max_worker $MAX_WORKERS"
    
    if python filter_videos_by_sync_score.py \
        --input_dir "data/${VIDEO_ID}" \
        --output_dir "results/${VIDEO_ID}/" \
        --preset "$PRESET" \
        --max_worker "$MAX_WORKERS"; then
        print_success "Step 2 completed: SyncNet filtering completed"
        print_success "Results available in: $SYNCNET_OUTPUT_DIR"
        
        # Check if any good quality videos were produced
        GOOD_QUALITY_DIR="$SYNCNET_OUTPUT_DIR/good_quality"
        if [ -d "$GOOD_QUALITY_DIR" ]; then
            GOOD_COUNT=$(find "$GOOD_QUALITY_DIR" -name "*.mp4" -o -name "*.avi" | wc -l)
            if [ "$GOOD_COUNT" -eq 0 ]; then
                print_warning "No good quality videos found after SyncNet filtering"
                print_warning "All videos were filtered out due to poor audio-visual synchronization"
                print_warning "You may want to:"
                print_warning "  - Use a lower preset (medium or low instead of high)"
                print_warning "  - Check the original video quality"
                print_warning "  - Verify audio-visual alignment in the source"
            else
                print_success "Found $GOOD_COUNT good quality video(s) after filtering"
            fi
        fi
    else
        print_error "Step 2 failed: SyncNet filtering failed"
        print_error "This might be due to:"
        print_error "  - Python library compatibility issues (scenedetect/numpy)"
        print_error "  - Missing dependencies in SyncNet environment"
        print_error "  - Video format compatibility issues"
        exit 1
    fi
    
    # Return to main repository
    cd "$CURRENT_REPO"
else
    print_warning "Step 2 skipped: SyncNet filtering"
    SYNCNET_OUTPUT_DIR="${SYNCNET_REPO}/results/${VIDEO_ID}"
fi

# Step 3: Organize folders with bounding box, cropped, normal video & audio
if [ "$SKIP_STEP3" = false ]; then
    print_status "Step 3: Organizing directories..."
    
    GOOD_QUALITY_DIR="${SYNCNET_OUTPUT_DIR}/good_quality"
    ORGANIZED_OUTPUT_DIR="${VIDEO_ID}"
    
    # Check if good_quality directory exists and has content
    if [ ! -d "$GOOD_QUALITY_DIR" ]; then
        print_error "Good quality directory not found: $GOOD_QUALITY_DIR"
        print_error "Please run step 2 first or use --skip-step2 if SyncNet results already exist"
        exit 1
    fi
    
    GOOD_COUNT=$(find "$GOOD_QUALITY_DIR" -name "*.mp4" -o -name "*.avi" | wc -l)
    if [ "$GOOD_COUNT" -eq 0 ]; then
        print_error "No good quality videos found in: $GOOD_QUALITY_DIR"
        print_error "SyncNet filtering removed all videos. Cannot proceed with organization."
        print_error "Consider:"
        print_error "  - Using a lower SyncNet preset (--preset medium or --preset low)"
        print_error "  - Checking video quality and audio-visual synchronization"
        print_error "  - Skipping SyncNet filtering (--skip-step2) if you want to process all chunks"
        exit 1
    fi
    
    print_status "Found $GOOD_COUNT good quality video(s) to organize"
    
    # Change to SyncNet directory to run directory preparation
    cd "$SYNCNET_REPO"
    
    print_status "Running directory organization..."
    print_status "Command: python utils/directory_prepare.py --input_dir results/${VIDEO_ID}/good_quality --output_dir ${VIDEO_ID} --max_workers $MAX_WORKERS"
    
    # Note: This assumes the directory_prepare.py script exists in the SyncNet repo
    # If it doesn't exist, we'll need to create or locate this script
    if [ -f "utils/directory_prepare.py" ]; then
        if python utils/directory_prepare.py \
            --input_dir "results/${VIDEO_ID}/good_quality" \
            --output_dir "$VIDEO_ID" \
            --max_workers "$MAX_WORKERS"; then
            print_success "Step 3 completed: Directory organization completed"
        else
            print_error "Step 3 failed: Directory organization failed"
            exit 1
        fi
    else
        print_warning "utils/directory_prepare.py not found in SyncNet repo"
        print_warning "Please check if this script exists or provide the correct path"
        print_warning "Skipping directory organization step..."
    fi
    
    # Copy organized videos back to main directory
    if [ -d "$VIDEO_ID" ]; then
        print_status "Copying organized videos back to main repository..."
        cd "$CURRENT_REPO"
        
        # Create experiments/experiment_data directory if it doesn't exist
        mkdir -p "experiments/experiment_data"
        
        # Copy the organized directory
        if [ -d "experiments/experiment_data/${VIDEO_ID}" ]; then
            print_warning "Removing existing organized data: experiments/experiment_data/${VIDEO_ID}"
            rm -rf "experiments/experiment_data/${VIDEO_ID}"
        fi
        
        cp -r "${SYNCNET_REPO}/${VIDEO_ID}" "experiments/experiment_data/"
        print_success "Organized videos copied to: experiments/experiment_data/${VIDEO_ID}"
    else
        print_error "Organized output directory not found: ${SYNCNET_REPO}/${VIDEO_ID}"
        exit 1
    fi
else
    print_warning "Step 3 skipped: Directory organization"
fi

# Step 4: Transcription using Google API & Whisper
if [ "$SKIP_STEP4" = false ]; then
    print_status "Step 4: Running transcription pipeline..."
    
    # Make sure we're in the main repository
    cd "$CURRENT_REPO"
    
    # Check if the organized video directory exists
    VIDEO_NORMAL_DIR="experiments/experiment_data/${VIDEO_ID}/video_normal"
    if [ ! -d "$VIDEO_NORMAL_DIR" ]; then
        print_error "Video normal directory not found: $VIDEO_NORMAL_DIR"
        print_error "Please run step 3 first or use --skip-step3 if organized videos already exist"
        exit 1
    fi
    
    print_status "Running transcription with both Google API and Whisper..."
    print_status "Command: python run_transcription_pipeline_modular.py --path $VIDEO_NORMAL_DIR --model both --batch"
    
    if python run_transcription_pipeline_modular.py \
        --path "$VIDEO_NORMAL_DIR" \
        --model both \
        --batch; then
        print_success "Step 4 completed: Transcription completed"
        print_success "Transcription results should be available in the appropriate output directories"
    else
        print_error "Step 4 failed: Transcription failed"
        exit 1
    fi
else
    print_warning "Step 4 skipped: Transcription"
fi

# Final summary
print_status "==================================================================="
print_success "PIPELINE COMPLETED SUCCESSFULLY!"
print_status "==================================================================="
print_status "Video ID: $VIDEO_ID"
print_status "Processing Summary:"
if [ "$SKIP_STEP1" = false ]; then
    print_status "  ✅ Step 1: Chunk creation completed"
else
    print_status "  ⏭️  Step 1: Skipped"
fi

if [ "$SKIP_STEP2" = false ]; then
    print_status "  ✅ Step 2: SyncNet filtering completed"
else
    print_status "  ⏭️  Step 2: Skipped"
fi

if [ "$SKIP_STEP3" = false ]; then
    print_status "  ✅ Step 3: Directory organization completed"
else
    print_status "  ⏭️  Step 3: Skipped"
fi

if [ "$SKIP_STEP4" = false ]; then
    print_status "  ✅ Step 4: Transcription completed"
else
    print_status "  ⏭️  Step 4: Skipped"
fi

print_status ""
print_status "Output locations:"
print_status "  - Original chunks: outputs/${VIDEO_ID}/"
print_status "  - SyncNet results: ${SYNCNET_REPO}/results/${VIDEO_ID}/"
print_status "  - Organized videos: experiments/experiment_data/${VIDEO_ID}/"
print_status "  - Transcription results: Check transcripts_* folders in experiment_data"
print_status "==================================================================="
