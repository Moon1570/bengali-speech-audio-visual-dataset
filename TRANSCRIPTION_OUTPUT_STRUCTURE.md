# Transcription Output Structure

## 📁 Directory Organization

Transcription results are now organized at the **same level** as `video_normal/`, `video_bbox/`, etc., for cleaner separation between video files and transcription results.

### Output Structure

```
experiments/experiment_data/
└── <video_id>/
    ├── google_transcription/         ⭐ Google transcripts (sibling level)
    │   ├── <video_id>_chunk_000.txt
    │   ├── <video_id>_chunk_000_google_summary.txt
    │   ├── <video_id>_chunk_001.txt
    │   ├── <video_id>_chunk_001_google_summary.txt
    │   └── ...
    │
    ├── whisper_transcription/        ⭐ Whisper transcripts (sibling level)
    │   ├── <video_id>_chunk_000.txt
    │   ├── <video_id>_chunk_000_whisper_summary.txt
    │   └── ...
    │
    ├── video_normal/                 📹 Normal filtered videos
    │   ├── <video_id>_chunk_000.mp4
    │   ├── <video_id>_chunk_001.mp4
    │   └── ...
    │
    ├── video_bbox/                   📦 Videos with face bounding boxes
    ├── video_cropped/                👤 Face-cropped videos
    └── audio/                        🔊 Extracted audio files
```

## ✅ Benefits

1. **Clean Separation**: Transcriptions are separate from video files
2. **Model Organization**: Each transcription model has its own folder
3. **No Clutter**: Video directories remain clean
4. **Scalable**: Easy to add more transcription models
5. **Accessible**: All files available outside Docker via volume mounts

## 🚀 Usage

### Docker (Recommended)

```bash
# Run pipeline with Google transcription
./run_docker.sh run VIDEO_ID --transcription-model google

# Run with both models
./run_docker.sh run VIDEO_ID --transcription-model both

# Custom output directory
./run_docker.sh run VIDEO_ID --output-dir experiments/my_experiment
```

### Accessing Results

**From host machine (outside Docker):**
```bash
# View transcription results
ls -la experiments/experiment_data/<video_id>/google_transcription/

# Read a transcript
cat experiments/experiment_data/<video_id>/google_transcription/<video_id>_chunk_000.txt

# Read summary
cat experiments/experiment_data/<video_id>/google_transcription/<video_id>_chunk_000_google_summary.txt
```

**From inside Docker:**
```bash
# Shell into container
./run_docker.sh shell

# Navigate to results
cd experiments/experiment_data/<video_id>/
ls -la
```

## 📊 File Types

### Transcript Files (`*.txt`)
- Combined transcript for each video chunk
- Contains recognized speech text
- Empty if no speech was recognized

### Summary Files (`*_<model>_summary.txt`)
- Metadata about the transcription
- Statistics (chunks processed, success rate)
- Individual chunk results
- Timestamp and model information

### Example Summary Content:
```
Transcription Summary
====================

Source: hxhLGCguRO0_test_chunk_003
Model: google
Chunks: 3
Valid chunks: 0
Timestamp: 2025-10-24 08:50:49

Combined transcript saved as: hxhLGCguRO0_test_chunk_003.txt
Individual chunks saved in: transcripts_google/

chunk_001.txt: [Unrecognized Speech]
chunk_002.txt: [Unrecognized Speech]
chunk_003.txt: [Unrecognized Speech]
```

## 🔧 Migration from Old Structure

If you have transcriptions from the old structure (inside `video_normal/`), you can move them:

```bash
# Move Google transcriptions
mv experiments/experiment_data/<video_id>/video_normal/google_transcription \
   experiments/experiment_data/<video_id>/

# Move Whisper transcriptions (if exists)
mv experiments/experiment_data/<video_id>/video_normal/whisper_transcription \
   experiments/experiment_data/<video_id>/
```

## 📝 Notes

- Transcription folders are created automatically during Step 4
- Folders are only created when using the respective model
- All outputs are preserved across Docker container restarts
- Docker volumes ensure data persists even if container is removed
- Custom output directories are fully supported via `--output-dir` parameter

## 🎯 Quick Examples

### Example 1: Single Video with Google
```bash
./run_docker.sh run aRHpoSebPPI --transcription-model google
# Results in: experiments/experiment_data/aRHpoSebPPI/google_transcription/
```

### Example 2: Multiple Models
```bash
./run_docker.sh run aRHpoSebPPI --transcription-model both
# Results in: 
#   experiments/experiment_data/aRHpoSebPPI/google_transcription/
#   experiments/experiment_data/aRHpoSebPPI/whisper_transcription/
```

### Example 3: Custom Output Location
```bash
./run_docker.sh run aRHpoSebPPI --output-dir experiments/test_run_1
# Results in: experiments/test_run_1/aRHpoSebPPI/google_transcription/
```

---

**Last Updated**: October 24, 2025  
**Status**: ✅ Implemented and tested
