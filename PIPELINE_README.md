# Complete Pipeline Scripts

This directory contains shell scripts to automate the entire Bengali Speech Audio-Visual Dataset processing pipeline.

## Scripts Overview

### 1. `complete_pipeline.sh` - Full Featured Pipeline
A comprehensive script with extensive error checking, logging, and configuration options.

**Usage:**
```bash
./complete_pipeline.sh <video_id> --syncnet-repo <path> [options]
```

**Examples:**
```bash
# Basic usage (Mac)
./complete_pipeline.sh efhkN7e8238 --syncnet-repo "/Users/darklord/Research/Audio Visual/Code/syncnet_python"

# With Google-only transcription
./complete_pipeline.sh efhkN7e8238 --syncnet-repo "/path/to/syncnet" --transcription-model google

# With audio processing enabled
./complete_pipeline.sh efhkN7e8238 --syncnet-repo "/path/to/syncnet" --reduce-noise --amplify-speech

# Without face filtering and chunk refinement
./complete_pipeline.sh efhkN7e8238 --syncnet-repo "/path/to/syncnet" --no-filter-faces --no-refine-chunks

# More sensitive silence detection (more chunks)
./complete_pipeline.sh efhkN7e8238 --syncnet-repo "/path/to/syncnet" --silence-preset sensitive

# Conservative silence detection (fewer, longer chunks)
./complete_pipeline.sh efhkN7e8238 --syncnet-repo "/path/to/syncnet" --silence-preset conservative

# Custom silence parameters
./complete_pipeline.sh efhkN7e8238 --syncnet-repo "/path/to/syncnet" \
  --custom-silence-thresh -35.0 --custom-min-silence 600

# WSL with custom settings
./complete_pipeline.sh efhkN7e8238 --syncnet-repo "/home/user/syncnet_python" --current-repo "/home/user/bengali-dataset" --preset medium

# Full control example
./complete_pipeline.sh efhkN7e8238 \
  --syncnet-repo "/path/to/syncnet" \
  --silence-preset sensitive \
  --reduce-noise --amplify-speech \
  --max-workers 16 \
  --min-chunk-duration 1.5 \
  --preset high \
  --transcription-model google
```

**Options:**

**Required:**
- `--syncnet-repo PATH`: Path to SyncNet repository (REQUIRED)

**Processing Configuration:**
- `--current-repo PATH`: Path to current repository (default: current directory)
- `--max-workers NUM`: Maximum number of workers (default: 8)
- `--min-chunk-duration NUM`: Minimum chunk duration in seconds (default: 2)
- `--preset PRESET`: SyncNet preset (low/medium/high, default: high)
- `--transcription-model MODEL`: Transcription model (google/whisper/both, default: both)

**Audio Processing Filters:**
- `--reduce-noise`: Enable noise reduction using spectral gating (default: disabled)
- `--amplify-speech`: Enable speech amplification using RMS normalization (default: disabled)
- `--no-filter-faces`: Disable face filtering (default: enabled)
- `--no-refine-chunks`: Disable chunk refinement (default: enabled)

**Silence Detection Options:**
- `--silence-preset PRESET`: Silence detection sensitivity (default: balanced)
  - Options: `very_sensitive`, `sensitive`, `balanced`, `conservative`, `very_conservative`
- `--custom-silence-thresh NUM`: Custom silence threshold in dBFS (e.g., -40.0)
- `--custom-min-silence NUM`: Custom minimum silence length in milliseconds (e.g., 500)

**Pipeline Control:**
- `--skip-step1`: Skip step 1 (chunk creation)
- `--skip-step2`: Skip step 2 (SyncNet filtering)
- `--skip-step3`: Skip step 3 (directory organization)
- `--skip-step4`: Skip step 4 (transcription)
- `--help`: Show help message

### 2. `quick_pipeline.sh` - Simplified Pipeline
A minimal script for quick processing with default settings.

**Usage:**
```bash
./quick_pipeline.sh <video_id> --syncnet-repo <path>
```

**Example:**
```bash
./quick_pipeline.sh efhkN7e8238 --syncnet-repo "/path/to/syncnet_python"
```

### 3. `pipeline_config.conf` - Configuration File
Contains default settings and paths that can be modified as needed.

## Audio Processing Options

The pipeline includes optional audio preprocessing filters that can be enabled via command-line flags:

### Noise Reduction (`--reduce-noise`)
- Uses spectral gating algorithm to remove background noise
- **Disabled by default** to preserve original audio quality for benchmarking
- Enable when: Processing noisy recordings or non-studio environments
- Trade-off: May introduce artifacts or affect naturalness

### Speech Amplification (`--amplify-speech`)
- Normalizes audio levels using RMS normalization
- **Disabled by default** to maintain original dynamics
- Enable when: Audio levels are too low or inconsistent
- Trade-off: May amplify noise along with speech

### Benchmarking Quality Standards

For creating high-quality benchmarking datasets, the pipeline enforces:
- **95% face presence requirement**: Chunks must have visible faces in 95%+ of frames
- **100ms gap tolerance**: Allows brief gaps (blinks) but splits at longer interruptions
- **30ms frame sampling**: High-resolution temporal analysis for accurate face tracking
- **Sentence-level boundaries**: 700ms silence threshold for natural speech segmentation

**Recommendation**: For benchmarking datasets, keep noise reduction and amplification **disabled** to preserve the original signal characteristics.

## Pipeline Steps

### Step 1: Create Chunks
- Runs: `python run_pipeline.py downloads/<video_id>.mp4 --filter-faces --refine-chunks --min-chunk-duration 2`
- Output: `outputs/<video_id>/`
- Creates video chunks with face detection and refinement

### Step 2: SyncNet Filtering
- Copies video chunks to SyncNet repository: `outputs/<video_id>/chunks/video/` → `<syncnet_repo>/data/<video_id>/`
- Runs: `python filter_videos_by_sync_score.py --input_dir data/<video_id> --output_dir results/<video_id>/ --preset high --max_worker 8`
- Output: `<syncnet_repo>/results/<video_id>/` with `good_quality` and `bad_quality` folders

### Step 3: Directory Organization
- Runs: `python utils/directory_prepare.py --input_dir results/<video_id>/good_quality --output_dir <video_id> --max_workers 8`
- Organizes videos with bounding box, cropped, normal video & audio
- Copies results back to: `experiments/experiment_data/<video_id>/`

### Step 4: Transcription
- Runs: `python run_transcription_pipeline_modular.py --path experiments/experiment_data/<video_id>/video_normal --model <transcription_model> --batch`
- Generates transcriptions using:
  - **Google Speech API** (`--transcription-model google`): Fast, accurate Bengali speech recognition
  - **Whisper** (`--transcription-model whisper`): OpenAI's multilingual model
  - **Both** (`--transcription-model both`, default): Runs both models for comparison
- Output: `transcripts_google/` and/or `transcripts_whisper/` in experiment_data directory

## Prerequisites

1. **Video File**: Ensure your video file exists in `downloads/<video_id>.mp4`
2. **SyncNet Repository**: Must be available at `/Users/darklord/Research/Audio Visual/Code/syncnet_python/`
3. **Dependencies**: Python environment with all required packages installed
4. **Permissions**: Scripts must be executable (`chmod +x *.sh`)

## Error Handling

The `complete_pipeline.sh` script includes:
- Dependency checking
- Path validation
- Error recovery options
- Detailed logging
- Step skipping capabilities

## Customization

### Modify Paths
Edit `pipeline_config.conf` or use command-line options to change:
- Repository paths
- Worker counts
- Processing parameters

### Skip Steps
Use skip options to resume from specific steps:
```bash
# Resume from step 3 (organization)
./complete_pipeline.sh efhkN7e8238 --syncnet-repo "/path/to/syncnet" --skip-step1 --skip-step2

# Only run transcription (Google only)
./complete_pipeline.sh efhkN7e8238 --syncnet-repo "/path/to/syncnet" --skip-step1 --skip-step2 --skip-step3 --transcription-model google

# Only run transcription (both models)
./complete_pipeline.sh efhkN7e8238 --syncnet-repo "/path/to/syncnet" --skip-step1 --skip-step2 --skip-step3 --transcription-model both
```

## Transcription Model Selection

The pipeline supports three transcription options via `--transcription-model`:

### Google Speech API (`google`)
- **Best for**: Bengali speech recognition with high accuracy
- **Requires**: Google Cloud credentials and API access
- **Speed**: Fast, cloud-based processing
- **Output**: `transcripts_google/` directory with JSON files
- **Use when**: You need accurate Bengali transcriptions for benchmarking

### Whisper (`whisper`)
- **Best for**: Multilingual support and offline processing
- **Requires**: Local compute (GPU recommended)
- **Speed**: Slower, depends on hardware
- **Output**: `transcripts_whisper/` directory with JSON files
- **Use when**: You need offline transcription or multilingual support

### Both (`both`, default)
- **Best for**: Comparison and validation
- **Requires**: Both Google credentials and local compute
- **Speed**: Slowest (runs both models sequentially)
- **Output**: Both `transcripts_google/` and `transcripts_whisper/` directories
- **Use when**: You want to compare results from multiple models

**Recommendation**: For production Bengali datasets, use `--transcription-model google` for optimal accuracy and speed.

## Troubleshooting

### Common Issues

1. **Video file not found**: Ensure video exists in `downloads/` directory
2. **SyncNet repo not accessible**: Check path in configuration
3. **Missing directory_prepare.py**: This script should be in the SyncNet repository
4. **Permission denied**: Make scripts executable with `chmod +x *.sh`

### Logs
Check `logs/` directory for detailed execution logs from each step.

### Manual Steps
If any step fails, you can run individual commands manually:

```bash
# Step 1
python run_pipeline.py downloads/efhkN7e8238.mp4 --filter-faces --refine-chunks --min-chunk-duration 2

# Step 2
cp -r outputs/efhkN7e8238/chunks/video/ /Users/darklord/Research/Audio Visual/Code/syncnet_python/data/efhkN7e8238/
cd /Users/darklord/Research/Audio Visual/Code/syncnet_python
python filter_videos_by_sync_score.py --input_dir data/efhkN7e8238 --output_dir results/efhkN7e8238/ --preset high --max_worker 8

# Step 3
python utils/directory_prepare.py --input_dir results/efhkN7e8238/good_quality --output_dir efhkN7e8238 --max_workers 8

# Step 4 - with both models (default)
cd /Users/darklord/Research/Audio Visual/Code/bengali-speech-audio-visual-dataset
python run_transcription_pipeline_modular.py --path experiments/experiment_data/efhkN7e8238/video_normal --model both --batch

# Step 4 - Google only
python run_transcription_pipeline_modular.py --path experiments/experiment_data/efhkN7e8238/video_normal --model google --batch

# Step 4 - Whisper only
python run_transcription_pipeline_modular.py --path experiments/experiment_data/efhkN7e8238/video_normal --model whisper --batch
```

## Output Structure

After successful completion, you'll have:

```
outputs/
└── <video_id>/                    # Step 1 output
    ├── chunks/
    │   ├── video/                 # Video chunks (copied to SyncNet)
    │   └── audio/                 # Audio chunks
    ├── face_detection_previews/
    ├── refinement_previews/
    ├── metadata.json
    ├── video.mp4
    └── video.wav

<syncnet_repo>/data/
└── <video_id>/                    # Copied video chunks for SyncNet processing

<syncnet_repo>/results/
└── <video_id>/                    # Step 2 output
    ├── good_quality/
    └── bad_quality/

experiments/experiment_data/
└── <video_id>/                       # Step 3 & 4 output
    ├── google_transcription/         # Google transcripts (Step 4)
    │   ├── <video_id>_chunk_000.txt
    │   ├── <video_id>_chunk_000_google_summary.txt
    │   └── ...
    ├── whisper_transcription/        # Whisper transcripts (Step 4)
    │   ├── <video_id>_chunk_000.txt
    │   ├── <video_id>_chunk_000_whisper_summary.txt
    │   └── ...
    ├── video_normal/                 # Normal videos
    ├── video_cropped/                # Face-cropped videos
    ├── video_bbox/                   # Videos with face bboxes
    └── audio/                        # Extracted audio files
```
