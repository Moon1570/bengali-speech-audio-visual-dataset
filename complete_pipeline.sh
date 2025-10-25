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
    
    # Check for virtual environment
    if [ -d ".venv" ]; then
        print_status "Activating virtual environment (.venv)..."
        source .venv/bin/activate
        PYTHON_CMD="python"
    elif command_exists python3; then
        PYTHON_CMD="python3"
    elif command_exists python; then
        PYTHON_CMD="python"
    else
        print_error "Python is not installed or not in PATH"
        print_error "Please install Python 3.8+ or activate your virtual environment"
        exit 1
    fi
    
    print_success "Dependencies check passed (using: $PYTHON_CMD)"
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
    echo "  --output-dir PATH       Custom output directory (default: experiments/experiment_data)"
    echo "  --max-workers NUM       Maximum number of workers (default: $DEFAULT_MAX_WORKERS)"
    echo "  --min-chunk-duration NUM Minimum chunk duration in seconds (default: $DEFAULT_MIN_CHUNK_DURATION)"
    echo "  --preset PRESET         SyncNet preset (low/medium/high, default: high)"
    echo ""
    echo "Audio Processing Options:"
    echo "  --reduce-noise          Enable noise reduction (spectral gating)"
    echo "  --amplify-speech        Enable speech amplification (RMS normalization)"
    echo "  --no-filter-faces       Disable face filtering"
    echo "  --no-refine-chunks      Disable chunk refinement"
    echo ""
    echo "Silence Detection Options:"
    echo "  --silence-preset PRESET Silence detection preset (default: balanced)"
    echo "                          Options: very_sensitive, sensitive, balanced, conservative, very_conservative"
    echo "  --custom-silence-thresh NUM  Custom silence threshold in dBFS (e.g., -40.0)"
    echo "  --custom-min-silence NUM     Custom minimum silence length in ms (e.g., 500)"
    echo ""
    echo "Pipeline Control:"
    echo "  --skip-step1            Skip step 1 (chunk creation)"
    echo "  --skip-step2            Skip step 2 (SyncNet filtering)"
    echo "  --skip-step3            Skip step 3 (directory organization)"
    echo "  --skip-step4            Skip step 4 (transcription)"
    echo "  --transcription-model MODEL  Transcription model (google/whisper/both, default: both)"
    echo "  --help                  Show this help message"
    echo ""
    echo "Examples:"
    echo "  # Basic usage (Mac):"
    echo "  $0 efhkN7e8238 --syncnet-repo /Users/darklord/Research/Audio\\ Visual/Code/syncnet_python"
    echo ""
    echo "  # With audio processing enabled:"
    echo "  $0 efhkN7e8238 --syncnet-repo /path/to/syncnet --reduce-noise --amplify-speech"
    echo ""
    echo "  # Without face filtering and chunk refinement:"
    echo "  $0 efhkN7e8238 --syncnet-repo /path/to/syncnet --no-filter-faces --no-refine-chunks"
    echo ""
    echo "  # Google-only transcription:"
    echo "  $0 efhkN7e8238 --syncnet-repo /path/to/syncnet --transcription-model google"
    echo ""
    echo "  # Custom output directory:"
    echo "  $0 efhkN7e8238 --syncnet-repo /path/to/syncnet --output-dir /path/to/output"
    echo ""
    echo "  # More sensitive silence detection (more chunks):"
    echo "  $0 efhkN7e8238 --syncnet-repo /path/to/syncnet --silence-preset sensitive"
    echo ""
    echo "  # Custom silence threshold:"
    echo "  $0 efhkN7e8238 --syncnet-repo /path/to/syncnet --custom-silence-thresh -35.0 --custom-min-silence 400"
    echo ""
    echo "  # WSL with custom settings:"  
    echo "  $0 efhkN7e8238 --syncnet-repo /home/\$USER/thesis/syncnet_python --preset medium --reduce-noise"
    echo ""
    echo "  # Full control example:"
    echo "  $0 efhkN7e8238 --current-repo /path/to/bengali-dataset --syncnet-repo /path/to/syncnet \\"
    echo "     --silence-preset sensitive --reduce-noise --amplify-speech --max-workers 16 \\"
    echo "     --min-chunk-duration 1.5 --preset high --transcription-model google"
}

# Parse command line arguments
VIDEO_ID=""
CURRENT_REPO=""
SYNCNET_REPO=""
OUTPUT_DIR="experiments/experiment_data"
MAX_WORKERS=$DEFAULT_MAX_WORKERS
MIN_CHUNK_DURATION=$DEFAULT_MIN_CHUNK_DURATION
PRESET="high"
TRANSCRIPTION_MODEL="both"
SILENCE_PRESET="balanced"
CUSTOM_SILENCE_THRESH=""
CUSTOM_MIN_SILENCE=""
REDUCE_NOISE=false
AMPLIFY_SPEECH=false
FILTER_FACES=true
REFINE_CHUNKS=true
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
        --output-dir)
            OUTPUT_DIR="$2"
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
        --reduce-noise)
            REDUCE_NOISE=true
            shift
            ;;
        --amplify-speech)
            AMPLIFY_SPEECH=true
            shift
            ;;
        --no-filter-faces)
            FILTER_FACES=false
            shift
            ;;
        --no-refine-chunks)
            REFINE_CHUNKS=false
            shift
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
        --transcription-model)
            TRANSCRIPTION_MODEL="$2"
            shift 2
            ;;
        --silence-preset)
            SILENCE_PRESET="$2"
            shift 2
            ;;
        --custom-silence-thresh)
            CUSTOM_SILENCE_THRESH="$2"
            shift 2
            ;;
        --custom-min-silence)
            CUSTOM_MIN_SILENCE="$2"
            shift 2
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

# Validate transcription model
if [[ ! "$TRANSCRIPTION_MODEL" =~ ^(google|whisper|both)$ ]]; then
    print_error "transcription-model must be one of: google, whisper, both"
    exit 1
fi

# Validate silence preset
if [[ ! "$SILENCE_PRESET" =~ ^(very_sensitive|sensitive|balanced|conservative|very_conservative)$ ]]; then
    print_error "silence-preset must be one of: very_sensitive, sensitive, balanced, conservative, very_conservative"
    exit 1
fi

# Validate custom silence parameters if provided
if [ -n "$CUSTOM_SILENCE_THRESH" ]; then
    if ! [[ "$CUSTOM_SILENCE_THRESH" =~ ^-?[0-9]+(\.[0-9]+)?$ ]]; then
        print_error "custom-silence-thresh must be a number (e.g., -40.0)"
        exit 1
    fi
fi

if [ -n "$CUSTOM_MIN_SILENCE" ]; then
    if ! [[ "$CUSTOM_MIN_SILENCE" =~ ^[0-9]+$ ]]; then
        print_error "custom-min-silence must be a positive integer (milliseconds)"
        exit 1
    fi
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
print_status "Transcription Model: $TRANSCRIPTION_MODEL"
print_status ""
print_status "Silence Detection Settings:"
print_status "  - Preset: $SILENCE_PRESET"
[ -n "$CUSTOM_SILENCE_THRESH" ] && print_status "  - Custom Threshold: ${CUSTOM_SILENCE_THRESH} dBFS"
[ -n "$CUSTOM_MIN_SILENCE" ] && print_status "  - Custom Min Silence: ${CUSTOM_MIN_SILENCE}ms"
print_status ""
print_status "Audio Processing Filters:"
print_status "  - Noise Reduction: $([ "$REDUCE_NOISE" = true ] && echo "ENABLED" || echo "DISABLED")"
print_status "  - Speech Amplification: $([ "$AMPLIFY_SPEECH" = true ] && echo "ENABLED" || echo "DISABLED")"
print_status "  - Face Filtering: $([ "$FILTER_FACES" = true ] && echo "ENABLED" || echo "DISABLED")"
print_status "  - Chunk Refinement: $([ "$REFINE_CHUNKS" = true ] && echo "ENABLED" || echo "DISABLED")"
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
    
    # Build command with optional flags
    CMD="$PYTHON_CMD run_pipeline.py \"$VIDEO_FILE\" --min-chunk-duration $MIN_CHUNK_DURATION --silence-preset $SILENCE_PRESET"
    
    # Add silence detection custom parameters
    if [ -n "$CUSTOM_SILENCE_THRESH" ]; then
        CMD="$CMD --custom-silence-thresh $CUSTOM_SILENCE_THRESH"
    fi
    
    if [ -n "$CUSTOM_MIN_SILENCE" ]; then
        CMD="$CMD --custom-min-silence $CUSTOM_MIN_SILENCE"
    fi
    
    # Add face filtering flags
    if [ "$FILTER_FACES" = true ]; then
        CMD="$CMD --filter-faces"
    else
        CMD="$CMD --no-filter-faces"
    fi
    
    # Add chunk refinement flags
    if [ "$REFINE_CHUNKS" = true ]; then
        CMD="$CMD --refine-chunks"
    else
        CMD="$CMD --no-refine-chunks"
    fi
    
    # Add audio processing flags
    if [ "$REDUCE_NOISE" = true ]; then
        CMD="$CMD --reduce-noise"
    fi
    
    if [ "$AMPLIFY_SPEECH" = true ]; then
        CMD="$CMD --amplify-speech"
    fi
    
    print_status "Running: $CMD"
    
    if eval "$CMD"; then
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
    print_status "Command: $PYTHON_CMD filter_videos_by_sync_score.py --input_dir data/${VIDEO_ID} --output_dir results/${VIDEO_ID}/ --preset $PRESET --max_worker $MAX_WORKERS"
    
    if $PYTHON_CMD filter_videos_by_sync_score.py \
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
    print_status "Command: $PYTHON_CMD utils/directory_prepare.py --input_dir results/${VIDEO_ID}/good_quality --output_dir ${VIDEO_ID} --max_workers $MAX_WORKERS"
    
    # Note: This assumes the directory_prepare.py script exists in the SyncNet repo
    # If it doesn't exist, we'll need to create or locate this script
    if [ -f "utils/directory_prepare.py" ]; then
        if $PYTHON_CMD utils/directory_prepare.py \
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
        
        # Create output directory if it doesn't exist
        mkdir -p "${OUTPUT_DIR}"
        
        # Copy organized videos back to main repository
        if [ -d "${OUTPUT_DIR}/${VIDEO_ID}" ]; then
            print_warning "Removing existing organized data: ${OUTPUT_DIR}/${VIDEO_ID}"
            rm -rf "${OUTPUT_DIR}/${VIDEO_ID}"
        fi
        
        cp -r "${SYNCNET_REPO}/${VIDEO_ID}" "${OUTPUT_DIR}/"
        print_success "Organized videos copied to: ${OUTPUT_DIR}/${VIDEO_ID}"
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
    VIDEO_NORMAL_DIR="${OUTPUT_DIR}/${VIDEO_ID}/video_normal"
    if [ ! -d "$VIDEO_NORMAL_DIR" ]; then
        print_error "Video normal directory not found: $VIDEO_NORMAL_DIR"
        print_error "Please run step 3 first or use --skip-step3 if organized videos already exist"
        exit 1
    fi
    
    print_status "Running transcription with model: $TRANSCRIPTION_MODEL..."
    print_status "Command: $PYTHON_CMD run_transcription_pipeline_modular.py --path $VIDEO_NORMAL_DIR --model $TRANSCRIPTION_MODEL --batch"
    
    if $PYTHON_CMD run_transcription_pipeline_modular.py \
        --path "$VIDEO_NORMAL_DIR" \
        --model "$TRANSCRIPTION_MODEL" \
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
print_status "  - Organized videos: ${OUTPUT_DIR}/${VIDEO_ID}/"
print_status "  - Transcription results: Check transcripts_* folders in experiment_data"
print_status "==================================================================="
