# 🐳 Bengali Speech Pipeline - Docker Image

**Public Docker Image**: [`moon1570/bengali-speech-pipeline`](https://hub.docker.com/r/moon1570/bengali-speech-pipeline)

Complete Bengali Speech Audio-Visual Dataset Pipeline with SyncNet, face detection, and transcription capabilities.

---

## 🚀 Quick Start

### Pull the Image
```bash
docker pull moon1570/bengali-speech-pipeline:latest
```

### Run with Your Data
```bash
# Clone the repository for scripts
git clone https://github.com/Moon1570/bengali-speech-audio-visual-dataset.git
cd bengali-speech-audio-visual-dataset

# Place your video in downloads/
cp your_video.mp4 downloads/

# Run the pipeline (CPU mode - works on all platforms)
docker run --rm \
    -v $(pwd)/downloads:/app/bengali-pipeline/downloads \
    -v $(pwd)/outputs:/app/bengali-pipeline/outputs \
    -v $(pwd)/logs:/app/bengali-pipeline/logs \
    moon1570/bengali-speech-pipeline:latest \
    bash -c "./complete_pipeline.sh YOUR_VIDEO_ID --syncnet-repo /app/syncnet_python --transcription-model google"
```

### Run with GPU (Linux + NVIDIA GPU only)
```bash
docker run --rm --gpus all \
    -v $(pwd)/downloads:/app/bengali-pipeline/downloads \
    -v $(pwd)/outputs:/app/bengali-pipeline/outputs \
    -v $(pwd)/logs:/app/bengali-pipeline/logs \
    moon1570/bengali-speech-pipeline:latest \
    bash -c "./complete_pipeline.sh YOUR_VIDEO_ID --syncnet-repo /app/syncnet_python --transcription-model google"
```

---

## 📦 What's Included

✅ **Complete Pipeline**
- Audio extraction and chunking by silence detection
- SyncNet lip-sync filtering (pretrained model included)
- Face detection and tracking
- Transcription (Google Speech API + Whisper)

✅ **Pre-configured Components**
- Modified SyncNet with custom modifications
- SyncNet pretrained model (no download needed)
- Modified scenedetect library
- All Python dependencies

✅ **Fixed & Optimized**
- ✅ FLAC wrapper for ARM64/AMD64 compatibility
- ✅ Google Speech Recognition working 100%
- ✅ Custom silence detection presets
- ✅ Organized output structure

---

## 🖥️ Architecture Support

| Architecture | Status | Use Case |
|--------------|--------|----------|
| **linux/arm64** | ✅ Supported | Apple Silicon, AWS Graviton, Raspberry Pi 4+ |
| **linux/amd64** | ✅ Build Required | Intel/AMD CPUs (most servers) |
| **GPU (NVIDIA)** | ✅ Optional | Faster processing (Linux only) |
| **CPU-only** | ✅ Default | All platforms including macOS |

**Current public image**: Built for `arm64` (Apple Silicon compatible)

To build for Intel/AMD:
```bash
docker buildx build --platform linux/amd64 \
    -t moon1570/bengali-speech-pipeline:amd64 \
    --push \
    .
```

---

## 🎯 Usage Examples

### Example 1: Basic Processing
```bash
docker run --rm \
    -v $(pwd)/downloads:/app/bengali-pipeline/downloads \
    -v $(pwd)/outputs:/app/bengali-pipeline/outputs \
    moon1570/bengali-speech-pipeline:latest \
    bash -c "./complete_pipeline.sh my_video \
        --syncnet-repo /app/syncnet_python \
        --transcription-model google"
```

### Example 2: High Quality with Noise Reduction
```bash
docker run --rm \
    -v $(pwd)/downloads:/app/bengali-pipeline/downloads \
    -v $(pwd)/outputs:/app/bengali-pipeline/outputs \
    moon1570/bengali-speech-pipeline:latest \
    bash -c "./complete_pipeline.sh my_video \
        --syncnet-repo /app/syncnet_python \
        --max-workers 8 \
        --preset high \
        --silence-preset conservative \
        --reduce-noise \
        --transcription-model google"
```

### Example 3: Fast Processing
```bash
docker run --rm \
    -v $(pwd)/downloads:/app/bengali-pipeline/downloads \
    -v $(pwd)/outputs:/app/bengali-pipeline/outputs \
    moon1570/bengali-speech-pipeline:latest \
    bash -c "./complete_pipeline.sh my_video \
        --syncnet-repo /app/syncnet_python \
        --max-workers 16 \
        --preset low \
        --silence-preset sensitive \
        --transcription-model google"
```

### Example 4: With GPU Acceleration (Linux only)
```bash
docker run --rm --gpus all \
    -v $(pwd)/downloads:/app/bengali-pipeline/downloads \
    -v $(pwd)/outputs:/app/bengali-pipeline/outputs \
    moon1570/bengali-speech-pipeline:latest \
    bash -c "./complete_pipeline.sh my_video \
        --syncnet-repo /app/syncnet_python \
        --max-workers 12 \
        --preset medium \
        --transcription-model whisper"  # Whisper benefits from GPU
```

---

## 📋 Available Flags

### Core Options
- `--max-workers NUM` - Parallel workers (default: 8)
- `--preset low|medium|high` - SyncNet quality (default: high)
- `--transcription-model google|whisper|both` - Transcription engine

### Silence Detection
- `--silence-preset very_sensitive|sensitive|balanced|conservative|very_conservative`
- `--custom-silence-thresh NUM` - Custom threshold in dBFS (e.g., -35.0)
- `--custom-min-silence NUM` - Min silence in ms (e.g., 600)

### Audio Processing
- `--reduce-noise` - Enable spectral noise reduction
- `--amplify-speech` - Boost audio levels
- `--no-filter-faces` - Keep all chunks
- `--no-refine-chunks` - Skip boundary refinement

### Pipeline Control
- `--skip-step1` - Skip audio chunking
- `--skip-step2` - Skip SyncNet filtering
- `--skip-step3` - Skip organization
- `--skip-step4` - Skip transcription

For complete documentation, see the [GitHub repository](https://github.com/Moon1570/bengali-speech-audio-visual-dataset).

---

## 📂 Output Structure

After processing, your `outputs/` directory will contain:

```
outputs/
└── YOUR_VIDEO_ID/
    ├── video_normal/          # Filtered video chunks
    │   ├── chunk_000.mp4
    │   ├── chunk_001.mp4
    │   └── ...
    ├── google_transcription/  # Google API transcriptions
    │   ├── chunk_000.txt
    │   ├── chunk_001.txt
    │   └── ...
    └── whisper_transcription/ # Whisper transcriptions (if enabled)
        ├── chunk_000.txt
        └── ...
```

---

## 🔧 System Requirements

**Minimum:**
- Docker 20.10+
- 10GB free disk space
- 8GB RAM

**Recommended:**
- Docker 24.0+
- 20GB free disk space
- 16GB RAM
- Multi-core CPU (4+ cores)

**For GPU:**
- Linux OS
- NVIDIA GPU with CUDA support
- NVIDIA Docker runtime installed

---

## 🐛 Troubleshooting

### Empty Transcription Files
✅ **Fixed in v1.0** - FLAC wrapper now handles stdin correctly

### GPU Not Working
```bash
# Verify NVIDIA Docker
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

### Out of Memory
- Reduce `--max-workers` to 4 or lower
- Use `--preset low` instead of high

### Slow Transcription
- Use `--transcription-model google` (faster than Whisper on CPU)
- Remove `--reduce-noise` flag

---

## 📊 Image Details

- **Base**: `nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04`
- **Python**: 3.10.12
- **Size**: ~9.18GB
- **Architecture**: arm64 (Apple Silicon optimized)
- **Platforms**: macOS (Apple Silicon), Linux (ARM64 servers)

---

## 📚 Additional Resources

- **GitHub**: https://github.com/Moon1570/bengali-speech-audio-visual-dataset
- **Documentation**: See `DOCKER_README.md` in the repository
- **GPU Guide**: See `GPU_USAGE_GUIDE.md` in the repository
- **Issues**: https://github.com/Moon1570/bengali-speech-audio-visual-dataset/issues

---

## 🤝 Contributing

Found a bug or have a suggestion? Please open an issue on GitHub!

---

## 📄 License

See the [repository](https://github.com/Moon1570/bengali-speech-audio-visual-dataset) for license information.

---

**Happy Processing! 🎉**

Built with ❤️ for Bengali Speech Research
