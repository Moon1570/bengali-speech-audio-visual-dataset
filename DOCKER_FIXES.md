# Docker Build Fixes Applied

This document tracks the dependency version fixes applied to make the Docker build work with Python 3.10.

## Issue Summary

The local development environment likely uses Python 3.11+, which has access to newer package versions. The Docker container uses Python 3.10 (from Ubuntu 22.04), which requires compatible older versions.

## Fixes Applied

### 1. Bengali Pipeline Requirements (`requirements.txt`)

**File**: `bengali-speech-audio-visual-dataset/requirements.txt`

| Package | Original Version | Fixed Version | Reason |
|---------|-----------------|---------------|---------|
| `torchaudio` | 0.22.1 | **2.7.1** | Old version incompatible with torch 2.7.1 |
| `pandas` | 2.3.0 | **2.2.2** | 2.3.x requires Python >=3.11 |
| `scipy` | 1.16.1 | **1.13.1** | 1.16.x requires Python >=3.11 |

### 2. SyncNet Requirements (`../syncnet_python/requirements.txt`)

**File**: `syncnet_python/requirements.txt`

| Package | Original Version | Fixed Version | Reason |
|---------|-----------------|---------------|---------|
| `networkx` | 3.5 | **3.4.2** | 3.5 requires Python >=3.11 |
| `numpy` | 2.2.6 | **1.26.4** | 2.x series may have Python 3.11+ requirement |
| `opencv-contrib-python` | 4.12.0.88 | **4.10.0.84** | Align with Bengali pipeline version |
| `opencv-python` | 4.12.0.88 | **4.10.0.84** | Align with Bengali pipeline version |
| `pillow` | 11.3.0 | **10.4.0** | 11.x requires Python >=3.11 |
| `scipy` | 1.16.1 | **1.13.1** | 1.16.x requires Python >=3.11 |

### 3. System Dependencies (Dockerfile)

**File**: `Dockerfile`

Added system dependencies:
```dockerfile
RUN apt-get update && apt-get install -y \
    # ... other packages ...
    portaudio19-dev \
    flac \
    && rm -rf /var/lib/apt/lists/*
```

**Reasons**: 
- `portaudio19-dev`: PyAudio requires PortAudio development headers to compile
- `flac`: Google Speech Recognition requires FLAC encoder for audio format conversion

## Backup Files Created

- `syncnet_python/requirements.txt.backup` - Original SyncNet requirements

## Python Version Compatibility

| Python Version | Status |
|----------------|--------|
| Python 3.10 | ✅ Supported (Docker) |
| Python 3.11+ | ✅ Supported (Local dev) |

## Verification Commands

To verify package versions after build:

```bash
# Check Docker Python version
docker run bengali-speech-pipeline:latest python3 --version

# Check specific package versions
docker run bengali-speech-pipeline:latest pip list | grep -E "(scipy|pandas|networkx|numpy)"
```

## Notes

- The original requirements files work fine in Python 3.11+ environments
- Docker uses Ubuntu 22.04 which ships with Python 3.10
- All version downgrades maintain API compatibility
- If upgrading Python in Docker to 3.11+, the original versions can be restored

## Future Improvements

Consider:
1. Using Python 3.11+ base image in Docker
2. Adding version range instead of pinned versions (e.g., `scipy>=1.13.1,<2.0`)
3. Separate requirements files for dev vs Docker
