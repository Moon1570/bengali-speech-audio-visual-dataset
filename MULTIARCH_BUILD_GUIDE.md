# Multi-Architecture Docker Build Guide

## 🏗️ Building for Multiple Architectures

This guide explains how to build the Bengali Speech Pipeline Docker image for both **Intel/AMD (amd64)** and **ARM64** architectures.

---

## Quick Start

### Option 1: Build Locally (Recommended for Testing)
```bash
# Builds for your current platform only
./build_multiarch_docker.sh
```

### Option 2: Build and Push to Docker Hub (For Sharing)
```bash
# Login first
docker login

# Build and push multi-arch
./build_multiarch_docker.sh --push --registry yourusername --tag v1.0
```

### Option 3: Build and Push to GitHub Container Registry
```bash
# Login to GHCR
echo YOUR_TOKEN | docker login ghcr.io -u YOUR_USERNAME --password-stdin

# Build and push
./build_multiarch_docker.sh --push --registry ghcr.io/yourusername --tag latest
```

---

## Supported Platforms

| Platform | Architecture | Use Cases |
|----------|--------------|-----------|
| **linux/amd64** | x86_64 | Intel/AMD servers, desktops, most cloud instances |
| **linux/arm64** | aarch64 | Apple Silicon (M1/M2/M3), AWS Graviton, Raspberry Pi 4+ |

Both platforms support:
- ✅ **CPU-only mode** (works everywhere)
- ✅ **NVIDIA GPU** (Linux only, runtime requirement)

---

## Command Reference

### Basic Commands

```bash
# Build for local platform (fast, for testing)
./build_multiarch_docker.sh

# Build and push to Docker Hub
./build_multiarch_docker.sh --push --registry yourusername

# Build with custom tag
./build_multiarch_docker.sh --tag v1.0.0

# Build and push with custom tag
./build_multiarch_docker.sh --push --registry yourusername --tag v1.0.0

# Show help
./build_multiarch_docker.sh --help
```

### Advanced Examples

```bash
# Build v1.0 and push to Docker Hub
./build_multiarch_docker.sh --push --registry myusername --tag v1.0

# Build latest and push to GHCR
./build_multiarch_docker.sh --push --registry ghcr.io/myorg --tag latest

# Build multiple tags (run multiple times)
./build_multiarch_docker.sh --push --registry myuser --tag v1.0.0
./build_multiarch_docker.sh --push --registry myuser --tag v1.0
./build_multiarch_docker.sh --push --registry myuser --tag latest
```

---

## What Happens During Build

### Local Build (without --push)
1. ✅ Builds for **your current platform only** (amd64 OR arm64)
2. ✅ Loads image into local Docker
3. ✅ Image immediately available: `docker images`
4. ⚠️  Only works on your architecture

**Use case**: Testing on your development machine

### Registry Push (with --push)
1. ✅ Builds for **both platforms** (amd64 AND arm64)
2. ✅ Pushes to Docker Hub or other registry
3. ✅ Creates multi-arch manifest
4. ✅ Users on any platform can pull

**Use case**: Sharing with others

---

## Verification

### Check Local Image
```bash
# List images
docker images bengali-speech-pipeline

# Inspect architecture
docker image inspect bengali-speech-pipeline:latest --format '{{.Architecture}}'
```

### Check Remote Multi-Arch Manifest
```bash
# After pushing, verify both architectures are present
docker buildx imagetools inspect yourusername/bengali-speech-pipeline:latest
```

Expected output:
```
Name:      yourusername/bengali-speech-pipeline:latest
MediaType: application/vnd.docker.distribution.manifest.list.v2+json
Digest:    sha256:abc123...
           
Manifests: 
  Name:      yourusername/bengali-speech-pipeline:latest@sha256:def456...
  MediaType: application/vnd.docker.distribution.manifest.v2+json
  Platform:  linux/amd64
             
  Name:      yourusername/bengali-speech-pipeline:latest@sha256:ghi789...
  MediaType: application/vnd.docker.distribution.manifest.v2+json
  Platform:  linux/arm64
```

---

## How Users Pull the Image

### Automatic Platform Selection
```bash
# Users simply pull - Docker chooses the right architecture automatically
docker pull yourusername/bengali-speech-pipeline:latest

# On Intel/AMD: Gets linux/amd64
# On Apple Silicon: Gets linux/arm64
# On ARM servers: Gets linux/arm64
```

### Force Specific Platform
```bash
# Force Intel/AMD version (on any machine)
docker pull --platform linux/amd64 yourusername/bengali-speech-pipeline:latest

# Force ARM64 version (on any machine)
docker pull --platform linux/arm64 yourusername/bengali-speech-pipeline:latest
```

---

## Build Time Estimates

| Build Type | Time | Note |
|------------|------|------|
| **Single platform (local)** | ~10-15 min | Fast, for testing |
| **Multi-arch (push)** | ~20-30 min | Builds both architectures |
| **Subsequent builds** | ~5-10 min | Docker layer caching helps |

---

## Image Sizes

- **Per architecture**: ~9-10 GB
- **Total registry storage**: ~18-20 GB (both architectures)
- **User download**: ~9-10 GB (automatic, correct architecture only)

---

## GPU Support

### How It Works
- **Build time**: GPU not required (builds on any machine)
- **Runtime**: NVIDIA GPU + nvidia-docker required (Linux only)

### Using GPU at Runtime

#### Linux with NVIDIA GPU
```bash
# Start with GPU
./run_docker.sh --gpu start

# Run with GPU acceleration
./run_docker.sh --gpu run VIDEO_ID --transcription-model whisper
```

#### macOS or CPU-only
```bash
# Start without GPU (default)
./run_docker.sh start

# Run in CPU mode
./run_docker.sh run VIDEO_ID --transcription-model google
```

---

## Troubleshooting

### Build Fails: "buildx not found"
```bash
# Update Docker to version 19.03+
# Or install buildx plugin
docker buildx version
```

### Build Fails: "multiple platforms"
```bash
# Don't use --load with multiple platforms
# Either:
# 1. Use --push to push to registry, OR
# 2. Remove --load flag (script handles this automatically)
```

### "No space left on device"
```bash
# Clean up Docker
docker system prune -a

# Check space
df -h
```

### Push Fails: "unauthorized"
```bash
# Login to registry
docker login  # For Docker Hub
docker login ghcr.io  # For GitHub Container Registry

# Verify credentials
docker info | grep Username
```

### Wrong Architecture Pulled
```bash
# Inspect what you got
docker image inspect bengali-speech-pipeline:latest --format '{{.Architecture}}'

# Force specific platform
docker pull --platform linux/amd64 yourusername/bengali-pipeline:latest
```

---

## Best Practices

### Version Tagging
```bash
# Always tag with version AND latest
./build_multiarch_docker.sh --push --registry myuser --tag v1.0.0
./build_multiarch_docker.sh --push --registry myuser --tag v1.0
./build_multiarch_docker.sh --push --registry myuser --tag latest
```

### Testing Before Push
```bash
# 1. Build locally first
./build_multiarch_docker.sh

# 2. Test the image
./run_docker.sh start
./run_docker.sh run test_video

# 3. If successful, build and push
./build_multiarch_docker.sh --push --registry myuser --tag v1.0.0
```

### Registry Selection

| Registry | Command | Best For |
|----------|---------|----------|
| **Docker Hub** | `--registry yourusername` | Public sharing, easy to use |
| **GitHub Container Registry** | `--registry ghcr.io/yourusername` | GitHub integrated, private repos |
| **Private Registry** | `--registry registry.company.com/team` | Corporate use |

---

## Complete Workflow Example

### For Public Release
```bash
# 1. Build locally and test
./build_multiarch_docker.sh
./run_docker.sh start
./run_docker.sh run test_video

# 2. If successful, login to Docker Hub
docker login

# 3. Build and push multi-arch with version
./build_multiarch_docker.sh --push --registry yourusername --tag v1.0.0
./build_multiarch_docker.sh --push --registry yourusername --tag v1.0
./build_multiarch_docker.sh --push --registry yourusername --tag latest

# 4. Verify
docker buildx imagetools inspect yourusername/bengali-speech-pipeline:latest

# 5. Test pull on another machine
docker pull yourusername/bengali-speech-pipeline:latest
```

### For Private Team Use
```bash
# 1. Build and save as tar
./build_multiarch_docker.sh
docker save bengali-speech-pipeline:latest | gzip > bengali-pipeline.tar.gz

# 2. Share tar file (Google Drive, network drive, etc.)

# 3. Team members load
docker load < bengali-pipeline.tar.gz
```

---

## FAQ

**Q: Can I build on macOS and have it work on Linux?**  
A: Yes! Building on macOS ARM64 creates an arm64 image that works on Linux ARM64 servers. For Intel/AMD servers, use `--push` to build both architectures.

**Q: Do I need NVIDIA GPU to build?**  
A: No! GPU is only needed at runtime. You can build on any machine (even macOS without GPU).

**Q: How long does it take?**  
A: Local build: ~10-15 min. Multi-arch push: ~20-30 min.

**Q: How much disk space?**  
A: ~20-30 GB during build, ~10 GB for final image (per architecture).

**Q: Can I build for Windows?**  
A: No, this is a Linux-only image (Ubuntu base). Windows users must use WSL2 or Docker Desktop.

**Q: What if I only want one architecture?**  
A: Local builds automatically create only your current platform. Use `--platform` flag if needed.

---

## Summary

✅ **For local testing**: 
```bash
./build_multiarch_docker.sh
```

✅ **For sharing (multi-arch)**:
```bash
./build_multiarch_docker.sh --push --registry yourusername --tag latest
```

✅ **Users pull**:
```bash
docker pull yourusername/bengali-speech-pipeline:latest
```

That's it! Docker handles the rest. 🎉
