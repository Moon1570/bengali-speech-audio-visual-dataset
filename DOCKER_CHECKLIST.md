# Docker Setup Checklist ✅

Quick checklist for building and distributing the Dockerized Bengali Speech Pipeline.

## 📋 Pre-Build Checklist

### Directory Structure
- [ ] `bengali-speech-audio-visual-dataset/` (this repo) exists
- [ ] `../syncnet_python/` exists in parent directory
- [ ] `../syncnet_python/data/work/pytorchmodels/syncnet_v2.model` exists
- [ ] `../syncnet_python/scenedetect/` exists (if you have modified scenedetect)
- [ ] All Docker files present in this directory:
  - [ ] `Dockerfile`
  - [ ] `docker-compose.yml`
  - [ ] `run_docker.sh`
  - [ ] `build_docker.sh`
  - [ ] `verify_docker_setup.sh`
  - [ ] `.dockerignore`

### Software Requirements
- [ ] Docker installed (20.10+)
- [ ] Docker Compose installed (1.29+)
- [ ] At least 10GB free disk space
- [ ] (Optional) NVIDIA Docker for GPU support

### Verification
Run the verification script:
```bash
chmod +x verify_docker_setup.sh
./verify_docker_setup.sh
```
- [ ] All checks pass (or only warnings, no errors)

## 🏗️ Build Checklist

### Build Process
```bash
chmod +x *.sh
./build_docker.sh
```

- [ ] Build starts without errors
- [ ] SyncNet files copied successfully
- [ ] Model file included in image
- [ ] Build completes successfully
- [ ] Image appears in `docker images`: `bengali-speech-pipeline:latest`

### Post-Build Verification
```bash
# Check image exists
docker images bengali-speech-pipeline:latest
```
- [ ] Image size is reasonable (~5-8GB)
- [ ] Creation date is recent

## 🧪 Testing Checklist

### Container Lifecycle
```bash
./run_docker.sh start
```
- [ ] Container starts without errors
- [ ] No immediate crashes (check with `./run_docker.sh status`)

```bash
./run_docker.sh shell
```
- [ ] Can enter container shell
- [ ] Environment variables are set correctly:
  ```bash
  echo $SYNCNET_REPO        # Should be /app/syncnet_python
  echo $CURRENT_REPO        # Should be /app/bengali-pipeline
  echo $PYTHONPATH          # Should include both paths
  ```
- [ ] SyncNet files are accessible:
  ```bash
  ls -la /app/syncnet_python/data/work/pytorchmodels/syncnet_v2.model
  ```
- [ ] Python imports work:
  ```bash
  python3 -c "from utils.split_by_silence import get_silence_preset; print('OK')"
  ```
- [ ] Exit shell: `exit`

### Pipeline Test (Quick)
```bash
# Copy a test video
cp /path/to/short/video.mp4 downloads/test_video.mp4

# Run only Step 1 (quick test)
./run_docker.sh run test_video --skip-step2 --skip-step3 --skip-step4
```
- [ ] Pipeline starts
- [ ] Audio extraction works
- [ ] Chunking completes
- [ ] Output files created in `outputs/test_video/`

### Pipeline Test (Full)
```bash
./run_docker.sh run test_video
```
- [ ] All 4 steps complete
- [ ] SyncNet filtering works
- [ ] Transcription completes
- [ ] Results in `experiments/experiment_data/test_video/`

### Preset Test
```bash
# Test different presets
./run_docker.sh run test_video --silence-preset sensitive --skip-step2 --skip-step3 --skip-step4
./run_docker.sh run test_video --silence-preset conservative --skip-step2 --skip-step3 --skip-step4
```
- [ ] Different presets produce different chunk counts
- [ ] No errors with any preset

### GPU Test (If Available)
```bash
./run_docker.sh shell
nvidia-smi
```
- [ ] GPU detected
- [ ] CUDA available
- [ ] No driver version mismatch

### Volume Persistence Test
```bash
# Create a file
./run_docker.sh shell
echo "test" > /app/bengali-pipeline/downloads/test.txt
exit

# Restart container
./run_docker.sh stop
./run_docker.sh start

# Check file persists
./run_docker.sh shell
cat /app/bengali-pipeline/downloads/test.txt
exit
```
- [ ] File persists across restarts

## 📚 Documentation Checklist

- [ ] `DOCKER_README.md` - Quick start guide exists and is clear
- [ ] `DOCKER_GUIDE.md` - Comprehensive guide exists and is complete
- [ ] `docs/DOCKER_IMPLEMENTATION.md` - Technical details documented
- [ ] Main `readme.md` updated with Docker section
- [ ] All scripts have execute permissions: `chmod +x *.sh`

## 🎁 Distribution Checklist

### For Git Repository
- [ ] All Docker files committed
- [ ] `.dockerignore` properly configured
- [ ] Documentation committed
- [ ] `readme.md` updated with Docker quick start
- [ ] Scripts have proper line endings (LF, not CRLF)

### For Users
Provide clear instructions:
1. [ ] Directory structure requirements documented
2. [ ] SyncNet location clearly specified
3. [ ] Model file requirement emphasized
4. [ ] Quick start commands tested and documented
5. [ ] Troubleshooting section complete

### Pre-Release Testing
Test on a clean system (or VM):
- [ ] Clone repo to fresh location
- [ ] Copy SyncNet to parent directory
- [ ] Run `./verify_docker_setup.sh`
- [ ] Run `./build_docker.sh`
- [ ] Process a video end-to-end
- [ ] Verify results are correct

## 🔧 Maintenance Checklist

### Regular Updates
- [ ] Update base image version if needed
- [ ] Update Python dependencies
- [ ] Update CUDA version for new GPUs
- [ ] Test after each update

### Performance Monitoring
- [ ] Check image size (should stay under 10GB)
- [ ] Monitor build time (should be under 15 minutes)
- [ ] Track runtime performance

### User Feedback
- [ ] Collect common issues
- [ ] Update troubleshooting section
- [ ] Add more examples based on use cases

## 🚨 Troubleshooting Quick Checks

If users report issues:

1. **Build fails**
   - [ ] Verify SyncNet directory structure
   - [ ] Check model file exists
   - [ ] Verify Docker has enough space
   - [ ] Check Docker version compatibility

2. **Container won't start**
   - [ ] Check `docker-compose logs`
   - [ ] Verify no port conflicts
   - [ ] Check volume mount permissions

3. **Pipeline fails**
   - [ ] Enter shell and run manually
   - [ ] Check environment variables
   - [ ] Verify SyncNet files accessible
   - [ ] Review pipeline logs

4. **GPU not working**
   - [ ] Verify NVIDIA Docker installed
   - [ ] Test with `nvidia-smi` in container
   - [ ] Check CUDA version compatibility

## ✨ Final Verification

Before considering the setup complete:

- [ ] Full pipeline runs successfully
- [ ] Documentation is clear and complete
- [ ] All scripts are executable
- [ ] Troubleshooting covers common issues
- [ ] Examples work as documented
- [ ] GPU support works (if applicable)
- [ ] Volume mounts persist data correctly
- [ ] No hardcoded paths or user-specific paths
- [ ] Error messages are helpful
- [ ] Success messages are clear

## 📝 Notes

Add any specific notes or observations here:

```
Date tested: _______________
Tested by: _______________
System: _______________
Docker version: _______________
Issues found: _______________
```

## 🎯 Success Criteria

The Docker setup is ready when:
- ✅ A new user can build and run in under 15 minutes
- ✅ No manual dependency installation required
- ✅ All features work as in native installation
- ✅ Documentation is clear and complete
- ✅ Common issues have documented solutions
- ✅ Can run completely offline (with Whisper)

---

**Status**: [ ] Complete  [ ] In Progress  [ ] Not Started

**Last Updated**: _______________
