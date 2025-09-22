# Cross-Platform Setup Guide
# ==========================

## Quick Setup

### For Mac Users (like you)
```bash
# Use the original requirements
pip install -r requirements.txt

# Run the pipeline with your specific paths
./complete_pipeline.sh <video_id> --syncnet-repo "/Users/darklord/Research/Audio Visual/Code/syncnet_python"

# Example:
./complete_pipeline.sh efhkN7e8238 --syncnet-repo "/Users/darklord/Research/Audio Visual/Code/syncnet_python"
```

### For WSL Users (like your peer)
```bash
# First run the WSL setup script
chmod +x setup_wsl.sh
./setup_wsl.sh

# Run the pipeline with WSL-specific paths
./complete_pipeline.sh <video_id> --syncnet-repo "/home/$USER/thesis/syncnet_python"

# Example:
./complete_pipeline.sh efhkN7e8238 --syncnet-repo "/home/sakline/thesis/syncnet_python" --preset medium
```

## Command Line Usage

### Complete Pipeline Script
```bash
./complete_pipeline.sh <video_id> --syncnet-repo <path> [options]

Required:
  video_id              Video ID (e.g., efhkN7e8238)
  --syncnet-repo PATH   Path to SyncNet repository

Optional:
  --current-repo PATH   Path to current repository (default: current directory)
  --max-workers NUM     Maximum number of workers (default: 8)
  --min-chunk-duration NUM  Minimum chunk duration (default: 2)
  --preset PRESET       SyncNet preset: low/medium/high (default: high)
  --skip-step1          Skip chunk creation
  --skip-step2          Skip SyncNet filtering
  --skip-step3          Skip directory organization  
  --skip-step4          Skip transcription
```

### Quick Pipeline Script
```bash
./quick_pipeline.sh <video_id> --syncnet-repo <path>

Examples:
# Mac
./quick_pipeline.sh efhkN7e8238 --syncnet-repo "/Users/darklord/Research/Audio Visual/Code/syncnet_python"

# WSL
./quick_pipeline.sh efhkN7e8238 --syncnet-repo "/home/sakline/thesis/syncnet_python"
```

## Fixed Issues

### 1. **Path Specification (NEW)**
Instead of auto-detection, paths are now explicitly provided:
- **Required**: `--syncnet-repo` must be specified by all users
- **Optional**: `--current-repo` defaults to current directory
- **Cross-platform**: Same interface for Mac and WSL

### 2. **SyncNet Compatibility (FIXED)**  
The WSL error `TypeError: 'tuple' object does not support item assignment` is fixed by:
- Using numpy==1.24.4 in requirements_wsl.txt
- Using scenedetect==0.6.2 (compatible version)

### 3. **Better Error Handling (FIXED)**
- Added checks for good_quality video count
- Better error messages when SyncNet filters all videos
- Suggestions for lower presets when filtering fails

## Troubleshooting

### WSL: SyncNet Still Fails
```bash
# Try downgrading numpy further
pip install numpy==1.21.6 --force-reinstall

# Or skip SyncNet step
./complete_pipeline.sh <video_id> --skip-step2
```

### Mac: Custom Paths
```bash
# Specify your exact SyncNet location
./complete_pipeline.sh efhkN7e8238 --syncnet-repo "/path/to/your/syncnet_python"

# With custom current repo
./complete_pipeline.sh efhkN7e8238 --current-repo "/path/to/bengali-dataset" --syncnet-repo "/path/to/syncnet"
```

### WSL: Custom Paths  
```bash
# Specify your exact SyncNet location
./complete_pipeline.sh efhkN7e8238 --syncnet-repo "/home/sakline/thesis/syncnet_python"

# Different user
./complete_pipeline.sh efhkN7e8238 --syncnet-repo "/home/username/code/syncnet_python"
```

### Both: No Good Quality Videos
```bash
# Use medium or low preset instead of high
./complete_pipeline.sh <video_id> --preset medium
./complete_pipeline.sh <video_id> --preset low
```