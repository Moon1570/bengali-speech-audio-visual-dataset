# Docker Image Sharing Guide

## 📦 Sharing Your Bengali Speech Pipeline Docker Image

After rebuilding your Docker image with all fixes, you can share it in several ways:

## Option 1: Docker Hub (Recommended - Easy for Users)

### 1. Create Docker Hub Account
- Go to https://hub.docker.com
- Create a free account if you don't have one

### 2. Login to Docker Hub
```bash
docker login
# Enter your Docker Hub username and password
```

### 3. Tag Your Image
```bash
# Format: docker tag <local-image> <dockerhub-username>/<repository-name>:<tag>
docker tag bengali-speech-pipeline:latest moon1570/bengali-speech-pipeline:latest
docker tag bengali-speech-pipeline:latest moon1570/bengali-speech-pipeline:v1.0
```

### 4. Push to Docker Hub
```bash
docker push moon1570/bengali-speech-pipeline:latest
docker push moon1570/bengali-speech-pipeline:v1.0
```

### 5. Users Can Pull It
```bash
docker pull moon1570/bengali-speech-pipeline:latest
```

**Pros:**
- ✅ Easy for users (single command to download)
- ✅ Automatic updates
- ✅ Works on all platforms

**Cons:**
- ⚠️ Free tier limited to public repositories (anyone can see)
- ⚠️ Large image size (~9GB) - slow upload/download

---

## Option 2: GitHub Container Registry (GHCR)

### 1. Create Personal Access Token
- Go to GitHub Settings → Developer settings → Personal access tokens
- Create token with `write:packages` permission

### 2. Login to GHCR
```bash
echo YOUR_TOKEN | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin
```

### 3. Tag and Push
```bash
docker tag bengali-speech-pipeline:latest ghcr.io/yourusername/bengali-speech-pipeline:latest
docker push ghcr.io/yourusername/bengali-speech-pipeline:latest
```

### 4. Users Can Pull
```bash
docker pull ghcr.io/yourusername/bengali-speech-pipeline:latest
```

**Pros:**
- ✅ Integrates with GitHub
- ✅ Can be private
- ✅ Free for public repos

---

## Option 3: Save as TAR File (Best for Local/Network Sharing)

### 1. Save Image to File
```bash
docker save bengali-speech-pipeline:latest | gzip > bengali-speech-pipeline.tar.gz
```

This will create a ~3-4GB compressed file (from 9GB image).

### 2. Share the File
- Upload to Google Drive, Dropbox, or cloud storage
- Share via network drive
- Copy to USB drive

### 3. Users Load the Image
```bash
# Decompress and load
gunzip -c bengali-speech-pipeline.tar.gz | docker load

# Or without decompressing:
docker load < bengali-speech-pipeline.tar.gz
```

**Pros:**
- ✅ Full control over distribution
- ✅ Works offline
- ✅ No registry needed

**Cons:**
- ⚠️ Large file size (~3-4GB compressed)
- ⚠️ Manual distribution

---

## Option 4: Export to Specific Registry

If you have access to a private registry (company, university, etc.):

```bash
# Tag for your registry
docker tag bengali-speech-pipeline:latest registry.yourcompany.com/bengali-speech-pipeline:latest

# Push to registry
docker push registry.yourcompany.com/bengali-speech-pipeline:latest
```

---

## 📋 Checklist Before Sharing

- [ ] Rebuild image with latest fixes: `./build_docker.sh`
- [ ] Test the image works: `./run_docker.sh run <test-video>`
- [ ] Verify Google transcription works inside Docker
- [ ] Update documentation (README, version info)
- [ ] Tag with version number (e.g., `v1.0`, `v1.1`)
- [ ] Remove sensitive data (API keys, credentials)
- [ ] Test on clean system if possible

---

## 📝 Current Image Info

**Image Name**: `bengali-speech-pipeline:latest`
**Size**: ~9.18 GB
**Platform**: linux/arm64 (macOS M-series) or linux/amd64
**Base**: nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

### What's Included:
- ✅ Modified SyncNet with custom modifications
- ✅ SyncNet pre-trained model (syncnet_v2.model)
- ✅ Modified scenedetect library
- ✅ All Python dependencies
- ✅ FFmpeg with FLAC support
- ✅ FLAC wrapper (fixed for stdin/stdout)
- ✅ Complete Bengali speech pipeline
- ✅ Face detection capabilities
- ✅ Google Speech Recognition support
- ✅ Whisper model support (downloads on first use)

---

## 🎯 Recommended Approach

**For Public Distribution**: Use **Docker Hub** (Option 1)
- Most users are familiar with it
- Easy single-command installation
- Automatic updates

**For Private/Team Use**: Use **TAR file** (Option 3)
- Full control
- No registry needed
- Works in restricted networks

**For GitHub Project**: Use **GHCR** (Option 2)
- Integrates with your repo
- Can keep it private
- Free for open source

---

## 📖 User Instructions Template

After sharing, provide users with these instructions:

### For Docker Hub:
```bash
# Pull the image
docker pull yourusername/bengali-speech-pipeline:latest

# Clone the repository (for scripts)
git clone https://github.com/yourusername/bengali-speech-audio-visual-dataset.git
cd bengali-speech-audio-visual-dataset

# Run the pipeline
./run_docker.sh run <video_id> --transcription-model google
```

### For TAR file:
```bash
# Load the image
docker load < bengali-speech-pipeline.tar.gz

# Clone the repository
git clone https://github.com/yourusername/bengali-speech-audio-visual-dataset.git
cd bengali-speech-audio-visual-dataset

# Run the pipeline
./run_docker.sh run <video_id> --transcription-model google
```

---

## 🔒 Security Notes

Before sharing publicly:
1. Check for hardcoded credentials
2. Remove any personal data from test files
3. Review logs for sensitive information
4. Consider adding `.dockerignore` for unnecessary files

---

## 📈 Version Tagging Best Practices

Use semantic versioning:
- `v1.0.0` - First stable release
- `v1.1.0` - Added features (e.g., custom output directory)
- `v1.0.1` - Bug fixes (e.g., FLAC wrapper fix)

Tag commands:
```bash
docker tag bengali-speech-pipeline:latest yourusername/bengali-speech-pipeline:v1.0.0
docker tag bengali-speech-pipeline:latest yourusername/bengali-speech-pipeline:latest
```

Always maintain a `latest` tag for the most recent version.
