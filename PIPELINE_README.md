# Complete Pipeline Scripts

This directory contains shell scripts to automate the entire Bengali Speech Audio-Visual Dataset processing pipeline.

## Scripts Overview

### 1. `complete_pipeline.sh` - Full Featured Pipeline
A comprehensive script with extensive error checking, logging, and configuration options.

**Usage:**
```bash
./complete_pipeline.sh <video_id> [options]
```

**Example:**
```bash
./complete_pipeline.sh efhkN7e8238 --max-workers 8 --preset high
```

**Options:**
- `--max-workers NUM`: Maximum number of workers (default: 8)
- `--min-chunk-duration NUM`: Minimum chunk duration in seconds (default: 2)
- `--preset PRESET`: SyncNet preset (low/medium/high, default: high)
- `--skip-step1`: Skip step 1 (chunk creation)
- `--skip-step2`: Skip step 2 (SyncNet filtering)
- `--skip-step3`: Skip step 3 (directory organization)
- `--skip-step4`: Skip step 4 (transcription)
- `--help`: Show help message

### 2. `quick_pipeline.sh` - Simplified Pipeline
A minimal script for quick processing with default settings.

**Usage:**
```bash
./quick_pipeline.sh <video_id>
```

**Example:**
```bash
./quick_pipeline.sh efhkN7e8238
```

### 3. `pipeline_config.conf` - Configuration File
Contains default settings and paths that can be modified as needed.

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
- Runs: `python run_transcription_pipeline_modular.py --path experiments/experiment_data/<video_id>/video_normal --model both --batch`
- Generates transcriptions using both Google API and Whisper

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
./complete_pipeline.sh efhkN7e8238 --skip-step1 --skip-step2

# Only run transcription
./complete_pipeline.sh efhkN7e8238 --skip-step1 --skip-step2 --skip-step3
```

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

# Step 4
cd /Users/darklord/Research/Audio Visual/Code/bengali-speech-audio-visual-dataset
python run_transcription_pipeline_modular.py --path experiments/experiment_data/efhkN7e8238/video_normal --model both --batch
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
└── <video_id>/                    # Step 3 & 4 output
    ├── video_normal/
    ├── video_cropped/
    ├── video_bbox/
    ├── audio/
    ├── transcripts_google/        # Step 4 output
    └── transcripts_whisper/       # Step 4 output
```
