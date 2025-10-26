# 🚀 GPU Usage Guide - Bengali Speech Pipeline

## Quick Start with GPU

### Prerequisites
- **Linux system** with NVIDIA GPU
- **NVIDIA Docker** runtime installed
- **Docker Compose** installed

> **Note**: GPU acceleration is **only available on Linux** with NVIDIA GPUs. macOS users should use CPU mode.

---

## 🎯 Complete Example Commands

### 1. Basic GPU Run (All Steps, Default Settings)
```bash
./run_docker.sh --gpu start
./run_docker.sh --gpu run A00000000_test \
    --transcription-model google
```

### 2. Full Pipeline with All Optimizations (GPU)
```bash
./run_docker.sh --gpu run A00000000_test \
    --max-workers 8 \
    --preset medium \
    --silence-preset balanced \
    --reduce-noise \
    --transcription-model google \
    --output-dir outputs
```

### 3. High-Quality Processing (Slower, Best Results)
```bash
./run_docker.sh --gpu run SSYouTubeonline \
    --max-workers 4 \
    --preset high \
    --silence-preset conservative \
    --custom-silence-thresh -35.0 \
    --custom-min-silence 600 \
    --reduce-noise \
    --amplify-speech \
    --transcription-model both \
    --output-dir /path/to/custom/output
```

### 4. Fast Processing (Speed over Quality)
```bash
./run_docker.sh --gpu run video123 \
    --max-workers 16 \
    --preset low \
    --silence-preset very_sensitive \
    --no-refine-chunks \
    --transcription-model google
```

### 5. Resume from Step 3 (Skip Audio & SyncNet)
```bash
./run_docker.sh --gpu run video456 \
    --skip-step1 \
    --skip-step2 \
    --transcription-model whisper
```

### 6. Only Transcription (Skip All Processing)
```bash
./run_docker.sh --gpu run video789 \
    --skip-step1 \
    --skip-step2 \
    --skip-step3 \
    --transcription-model both
```

### 7. Custom Output Location with Multiple Models
```bash
./run_docker.sh --gpu run my_video \
    --max-workers 12 \
    --preset medium \
    --output-dir /mnt/storage/bengali_dataset \
    --transcription-model both \
    --reduce-noise
```

---

## 📋 All Available Flags

### Global Flags (Docker Level)
```bash
--gpu                    Enable GPU support (Linux + NVIDIA only)
```

### Required Arguments
```bash
<video_id>              Video ID or filename (e.g., A00000000_test, SSYouTubeonline)
```

### Path Configuration
```bash
--current-repo PATH     Path to current repository (auto-detected)
--syncnet-repo PATH     Path to SyncNet repository (auto-set in Docker)
--output-dir PATH       Custom output directory (default: experiments/experiment_data)
```

### Performance Options
```bash
--max-workers NUM       Max parallel workers (default: 8)
                        - Low: 1-4 (high quality, slower)
                        - Medium: 8-12 (balanced)
                        - High: 16+ (fast, requires good CPU/GPU)

--min-chunk-duration NUM    Minimum chunk length in seconds (default: 2)
```

### SyncNet Options
```bash
--preset PRESET         SyncNet quality preset
                        - low: Fast, less accurate (threshold: 5.0)
                        - medium: Balanced (threshold: 6.5)
                        - high: Best quality, slower (threshold: 8.0)
```

### Audio Processing Options
```bash
--reduce-noise          Enable noise reduction (spectral gating)
                        Removes background noise, improves transcription

--amplify-speech        Enable speech amplification (RMS normalization)
                        Boosts audio levels for better recognition

--no-filter-faces       Disable face filtering
                        Keep all chunks regardless of face detection

--no-refine-chunks      Disable chunk refinement
                        Skip precise audio boundary detection
```

### Silence Detection Options
```bash
--silence-preset PRESET     Predefined silence detection settings
    Options:
    - very_sensitive:     -20 dBFS, 200ms (more chunks, aggressive splitting)
    - sensitive:          -25 dBFS, 300ms (many chunks)
    - balanced:           -30 dBFS, 500ms (RECOMMENDED, default)
    - conservative:       -35 dBFS, 700ms (fewer, longer chunks)
    - very_conservative:  -40 dBFS, 1000ms (minimal splitting)

--custom-silence-thresh NUM     Custom silence threshold in dBFS
                                Lower = more sensitive (e.g., -40.0)
                                Higher = less sensitive (e.g., -20.0)

--custom-min-silence NUM        Custom minimum silence duration in milliseconds
                                Shorter = more splits (e.g., 200)
                                Longer = fewer splits (e.g., 1000)
```

### Transcription Options
```bash
--transcription-model MODEL     Choose transcription model(s)
    Options:
    - google:   Google Speech Recognition API (RECOMMENDED for Bengali)
                Fast, accurate, requires internet
    - whisper:  OpenAI Whisper (works offline)
                Slower, downloads model on first use (~1.5GB for medium)
    - both:     Run both models and compare results
                Best for quality validation
```

### Pipeline Control
```bash
--skip-step1            Skip audio chunking (use existing chunks)
--skip-step2            Skip SyncNet filtering (use all chunks)
--skip-step3            Skip directory organization (keep existing structure)
--skip-step4            Skip transcription (process audio/video only)
```

### Help
```bash
--help                  Show help message
```

---

## 🖥️ GPU vs CPU Comparison

| Feature | GPU Mode | CPU Mode |
|---------|----------|----------|
| **SyncNet Speed** | ⚡ Fast (GPU accelerated) | 🐢 Slower |
| **Whisper Speed** | ⚡ Much faster | 🐢 Very slow |
| **Face Detection** | ⚡ Fast (GPU OpenCV) | ⏱️ Medium |
| **Google API** | ✅ Same speed | ✅ Same speed |
| **Platform** | 🐧 Linux only | ✅ All platforms |
| **Requirements** | NVIDIA GPU + Docker | Docker only |
| **Power Usage** | 🔥 High | ❄️ Low |

---

## 💡 Recommended Configurations

### For Production (Best Quality)
```bash
./run_docker.sh --gpu run <VIDEO_ID> \
    --max-workers 8 \
    --preset high \
    --silence-preset conservative \
    --reduce-noise \
    --transcription-model google
```

### For Testing/Development (Fast Iteration)
```bash
./run_docker.sh --gpu run <VIDEO_ID> \
    --max-workers 16 \
    --preset low \
    --silence-preset very_sensitive \
    --no-refine-chunks \
    --transcription-model google
```

### For Research (All Data, Both Models)
```bash
./run_docker.sh --gpu run <VIDEO_ID> \
    --max-workers 12 \
    --preset medium \
    --silence-preset balanced \
    --reduce-noise \
    --amplify-speech \
    --transcription-model both
```

### For Low-Resource Systems
```bash
./run_docker.sh run <VIDEO_ID> \  # No --gpu flag
    --max-workers 4 \
    --preset low \
    --transcription-model google
```

---

## 🔧 Performance Tuning

### 1. Max Workers Optimization

**Formula**: `CPU cores × 2` for I/O-bound tasks

```bash
# Check your CPU cores
nproc  # Linux
sysctl -n hw.ncpu  # macOS

# Example configurations:
# 4 cores  → --max-workers 8
# 8 cores  → --max-workers 16
# 16 cores → --max-workers 32
```

### 2. Silence Detection Tuning

**For News/Podcasts** (Clear speech, pauses):
```bash
--silence-preset conservative
# or
--custom-silence-thresh -35.0 --custom-min-silence 700
```

**For Casual Conversations** (Overlapping speech):
```bash
--silence-preset sensitive
# or
--custom-silence-thresh -25.0 --custom-min-silence 300
```

**For Noisy Environments**:
```bash
--silence-preset very_conservative --reduce-noise
# or
--custom-silence-thresh -40.0 --custom-min-silence 1000 --reduce-noise
```

### 3. SyncNet Preset Selection

| Preset | Use Case | Speed | Quality |
|--------|----------|-------|---------|
| `low` | Testing, fast preview | ⚡⚡⚡ | ⭐⭐ |
| `medium` | **Production (Recommended)** | ⚡⚡ | ⭐⭐⭐⭐ |
| `high` | Research, maximum quality | ⚡ | ⭐⭐⭐⭐⭐ |

---

## 📊 Example Workflows

### Workflow 1: Full Pipeline (Start to Finish)
```bash
# Step 1: Build and start with GPU
./run_docker.sh build
./run_docker.sh --gpu start

# Step 2: Run complete pipeline
./run_docker.sh --gpu run my_video \
    --max-workers 8 \
    --preset medium \
    --silence-preset balanced \
    --reduce-noise \
    --transcription-model google

# Step 3: Check results
ls outputs/my_video/
ls outputs/google_transcription/
```

### Workflow 2: Iterative Development
```bash
# First pass: Quick test
./run_docker.sh --gpu run test_video \
    --max-workers 16 \
    --preset low \
    --skip-step4

# Review chunks, adjust parameters

# Second pass: Better quality
./run_docker.sh --gpu run test_video \
    --skip-step1 \
    --skip-step2 \
    --skip-step3 \
    --transcription-model both
```

### Workflow 3: Batch Processing
```bash
# Process multiple videos
for video in video1 video2 video3; do
    ./run_docker.sh --gpu run $video \
        --max-workers 12 \
        --preset medium \
        --transcription-model google
done
```

---

## 🚨 Troubleshooting

### GPU Not Detected
```bash
# Check NVIDIA Docker installation
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi

# If fails, install nvidia-docker:
# https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html
```

### Out of Memory (GPU)
```bash
# Reduce workers
--max-workers 4

# Use lower preset
--preset low

# Or switch to CPU mode
./run_docker.sh run <VIDEO_ID>  # No --gpu flag
```

### Slow Transcription
```bash
# Use Google instead of Whisper
--transcription-model google

# Disable noise reduction
# (remove --reduce-noise flag)
```

### Empty Transcriptions
```bash
# Issue: Fixed in current version (FLAC wrapper bug)
# Verify fix:
docker run --rm bengali-speech-pipeline:latest bash -c \
    'echo "test" | /usr/local/bin/flac - --stdout | wc -c'
# Should output: >0 bytes
```

---

## 📝 Real-World Examples

### Example 1: YouTube News Video
```bash
./run_docker.sh --gpu run news_video_001 \
    --max-workers 8 \
    --preset medium \
    --silence-preset conservative \
    --custom-silence-thresh -35.0 \
    --reduce-noise \
    --transcription-model google \
    --output-dir outputs/news_dataset
```
**Expected**: 5-15 min processing for 30 min video

### Example 2: Casual Interview
```bash
./run_docker.sh --gpu run interview_xyz \
    --max-workers 12 \
    --preset high \
    --silence-preset sensitive \
    --reduce-noise \
    --amplify-speech \
    --transcription-model both \
    --output-dir outputs/interviews
```
**Expected**: 10-20 min processing for 30 min video

### Example 3: Low-Quality Recording
```bash
./run_docker.sh --gpu run low_quality_audio \
    --max-workers 6 \
    --preset high \
    --silence-preset very_conservative \
    --custom-silence-thresh -40.0 \
    --reduce-noise \
    --amplify-speech \
    --transcription-model google
```
**Expected**: 15-25 min processing for 30 min video

---

## 🎓 Tips & Best Practices

1. **Always start with balanced preset** for initial testing
2. **Use Google API** for Bengali (better accuracy than Whisper)
3. **Enable noise reduction** for low-quality audio
4. **Adjust silence detection** based on video type (news vs conversation)
5. **Monitor GPU usage**: `watch -n 1 nvidia-smi`
6. **Check outputs regularly**: `ls -lh outputs/VIDEO_ID/`
7. **Use CPU mode on macOS** (GPU not supported)

---

## 📚 Additional Resources

- **Full Documentation**: See `PIPELINE_README.md`
- **Docker Guide**: See `DOCKER_README.md`
- **Sharing Guide**: See `DOCKER_SHARING_GUIDE.md`
- **Transcription Fix**: See `GOOGLE_TRANSCRIPTION_FIX.md`

---

## 🤝 Getting Help

If you encounter issues:

1. Check the logs: `./run_docker.sh logs`
2. Enter container: `./run_docker.sh shell`
3. Check file sizes: `ls -lh outputs/VIDEO_ID/google_transcription/`
4. Verify GPU: `nvidia-smi` (in container)
5. Review this guide for flag combinations

---

**Happy Processing! 🎉**
