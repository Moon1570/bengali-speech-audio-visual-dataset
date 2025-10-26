# Bengali Speech Pipeline - Docker Quick Start 🐳

Run the complete Bengali Speech Audio-Visual Dataset Pipeline with one command - no manual setup required!

## 🚀 Quick Start (3 Steps)

### 1. Build the Docker Image

```bash
chmod +x build_docker.sh run_docker.sh
./build_docker.sh
```

This includes:
- ✅ Your modified SyncNet (all customizations preserved)
- ✅ Pretrained models and weights (no downloads needed)
- ✅ Modified scenedetect library
- ✅ Complete pipeline with all dependencies

**Build time**: 5-10 minutes (one time only)

### 2. Start the Container

```bash
./run_docker.sh start
```

### 3. Run the Pipeline

```bash
# Place your video in downloads/
cp /path/to/video.mp4 downloads/my_video.mp4

# Run the pipeline
./run_docker.sh run my_video
```

That's it! Results will be in `experiments/experiment_data/my_video/`

## 📋 Requirements

**Before building, you need:**

1. **Directory Structure**:
   ```
   Research/Audio Visual/Code/
   ├── bengali-speech-audio-visual-dataset/   ← You are here
   │   ├── Dockerfile
   │   ├── build_docker.sh
   │   └── run_docker.sh
   └── syncnet_python/                        ← Must exist!
       ├── data/
       │   └── work/
       │       └── pytorchmodels/
       │           └── syncnet_v2.model       ← Must be present!
       ├── scenedetect/                       ← Your modifications
       └── SyncNetInstance.py                 ← Your modifications
   ```

2. **Software**:
   - Docker (20.10+)
   - Docker Compose (1.29+)
   - 10GB+ free disk space

3. **Optional**:
   - NVIDIA GPU + nvidia-docker (for faster processing)

## 🎯 Common Commands

```bash
# Build image
./build_docker.sh

# Start container
./run_docker.sh start

# Run pipeline (various options)
./run_docker.sh run VIDEO_ID
./run_docker.sh run VIDEO_ID --silence-preset sensitive
./run_docker.sh run VIDEO_ID --reduce-noise
./run_docker.sh run VIDEO_ID --transcription-model google

# Enter container shell
./run_docker.sh shell

# View logs
./run_docker.sh logs

# Stop container
./run_docker.sh stop

# Clean up everything
./run_docker.sh cleanup
```

## 🎨 Silence Detection Presets

Control how the video is split into chunks:

```bash
# Word-level splits (many small chunks)
./run_docker.sh run VIDEO_ID --silence-preset very_sensitive

# Phrase-level splits
./run_docker.sh run VIDEO_ID --silence-preset sensitive

# Sentence-level splits (DEFAULT - balanced)
./run_docker.sh run VIDEO_ID --silence-preset balanced

# Paragraph-level splits
./run_docker.sh run VIDEO_ID --silence-preset conservative

# Major topic changes only (fewer chunks)
./run_docker.sh run VIDEO_ID --silence-preset very_conservative
```

## 🔧 Advanced Options

```bash
# Custom silence parameters
./run_docker.sh run VIDEO_ID \
    --custom-silence-thresh -32.0 \
    --custom-min-silence 650

# Enable noise reduction
./run_docker.sh run VIDEO_ID --reduce-noise

# Choose transcription model
./run_docker.sh run VIDEO_ID --transcription-model whisper  # offline
./run_docker.sh run VIDEO_ID --transcription-model google   # online, faster
./run_docker.sh run VIDEO_ID --transcription-model both     # both models

# Skip specific steps
./run_docker.sh run VIDEO_ID --skip-step2 --skip-step3

# Combine options
./run_docker.sh run VIDEO_ID \
    --silence-preset conservative \
    --reduce-noise \
    --transcription-model google
```

## 📁 Data Persistence & Output Access

**All outputs are accessible outside Docker!** These directories are automatically mounted and persist across container restarts:

- `downloads/` - Input videos
- `outputs/` - Processed results
- `experiments/` - Experiment data ⭐ **Main output location**
- `logs/` - Pipeline logs
- `data/` - Additional data
- `denoised_audio/` - Denoised audio files
- `amplified_denoised_audio/` - Amplified audio files

**Access your results from the host machine:**
```bash
# On your host (outside Docker)
ls -la experiments/experiment_data/<video_id>/

# Output structure:
# <video_id>/
# ├── google_transcription/    ← Transcription results
# ├── whisper_transcription/   ← Whisper results (if used)
# ├── video_normal/            ← Filtered video chunks
# ├── video_bbox/              ← Videos with face boxes
# ├── video_cropped/           ← Face-cropped videos
# └── audio/                   ← Extracted audio files
```

**Custom output directory:**
```bash
# Use --output-dir to specify a different location
./run_docker.sh run VIDEO_ID --output-dir /app/bengali-pipeline/my_custom_output

# Access from host:
ls -la my_custom_output/VIDEO_ID/
```

## 🐛 Troubleshooting

### Build fails with "syncnet_python not found"
```bash
# Ensure syncnet_python is in the parent directory
ls -la ../syncnet_python/

# Expected structure:
# Research/Audio Visual/Code/
# ├── bengali-speech-audio-visual-dataset/
# └── syncnet_python/
```

### Build fails with "model not found"
```bash
# Verify the SyncNet model exists
ls -la ../syncnet_python/data/work/pytorchmodels/syncnet_v2.model

# If missing, download it:
mkdir -p ../syncnet_python/data/work/pytorchmodels/
cd ../syncnet_python/data/work/pytorchmodels/
wget http://www.robots.ox.ac.uk/~vgg/software/lipsync/data/syncnet_v2.model
```

### Container exits immediately
```bash
# Check logs
./run_docker.sh logs

# Check status
./run_docker.sh status
```

### Permission denied on output files
```bash
# Fix permissions (run on host)
sudo chown -R $USER:$USER outputs/ experiments/ logs/
```

### GPU not detected
```bash
# Test NVIDIA Docker
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi

# If it fails, install nvidia-container-toolkit
```

## 📚 Full Documentation

For complete documentation, see:
- **DOCKER_GUIDE.md** - Comprehensive Docker guide
- **PIPELINE_README.md** - Pipeline usage and options
- **docs/SILENCE_PRESETS_QUICK_REF.md** - Silence preset guide

## 🎯 Example Workflow

```bash
# 1. Build (one time)
./build_docker.sh

# 2. Start
./run_docker.sh start

# 3. Process videos
for video in downloads/*.mp4; do
    VIDEO_ID=$(basename "$video" .mp4)
    echo "Processing $VIDEO_ID..."
    ./run_docker.sh run "$VIDEO_ID" --silence-preset balanced
done

# 4. Check results
ls -la experiments/experiment_data/

# 5. Stop when done
./run_docker.sh stop
```

## ✅ What's Included (No Internet Required at Runtime)

The Docker image is **completely self-contained**:
- ✅ Modified SyncNet with your customizations
- ✅ SyncNet pretrained model (130MB)
- ✅ Modified scenedetect library
- ✅ All Python dependencies
- ✅ FFmpeg and audio tools
- ✅ OpenCV with face detection
- ✅ Complete Bengali pipeline

**Only requires internet for**:
- Google Speech API (optional, can use Whisper offline)

## 🌟 Benefits of Docker Version

1. **One-Command Setup** - No complex dependency installation
2. **Reproducible** - Same environment everywhere
3. **Isolated** - Doesn't affect your system Python
4. **Portable** - Share the image with team members
5. **No Downloads** - All models and weights included
6. **GPU Support** - Automatic GPU acceleration if available

## 📞 Support

If you encounter issues:

1. Check the build log: `cat build.log`
2. Check container logs: `./run_docker.sh logs`
3. Enter shell for debugging: `./run_docker.sh shell`
4. Review full guide: `DOCKER_GUIDE.md`

---

**Happy Processing! 🚀**

For questions or issues, check the documentation or open an issue.
