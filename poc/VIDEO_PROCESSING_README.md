# SyncNet Video Processing Pipeline

This directory contains scripts for processing long videos with SyncNet analysis, including video chunking, audio extraction, and batch processing capabilities.

## Scripts Overview

### 1. `process_long_video.py` - Complete Pipeline
Automatically processes long video files by:
- Cutting video into chunks
- Extracting audio from each chunk
- Running SyncNet analysis on each chunk
- Generating comprehensive results

**Usage:**
```bash
python process_long_video.py \
    --input_video /path/to/long_video.mp4 \
    --output_dir /path/to/output \
    --chunk_duration 30 \
    --overlap 5
```

**Parameters:**
- `--input_video`: Path to input video file
- `--output_dir`: Output directory for all results
- `--chunk_duration`: Duration of each chunk in seconds (default: 30)
- `--overlap`: Overlap between chunks in seconds (default: 5)
- `--min_track`: Minimum track length for SyncNet (default: 5)
- `--min_face_size`: Minimum face size for SyncNet (default: 10)

**Output Structure:**
```
output_dir/
├── chunks/                     # Video chunks
│   ├── chunk_000.mp4
│   ├── chunk_001.mp4
│   └── ...
├── audio/                      # Extracted audio files
│   ├── chunk_000.wav
│   ├── chunk_001.wav
│   └── ...
├── syncnet_data/              # SyncNet analysis data
│   ├── pyavi/
│   ├── pycrop/
│   ├── pywork/
│   └── ...
└── processing_summary.json    # Complete results summary
```

### 2. `video_utils.py` - Video Utilities
Flexible utilities for video processing tasks.

**Commands:**

#### Get Video Information
```bash
python video_utils.py info --input video.mp4
```

#### Extract Audio
```bash
python video_utils.py extract-audio \
    --input video.mp4 \
    --output audio.wav \
    --sample_rate 16000 \
    --channels 1
```

#### Cut Video by Time
```bash
python video_utils.py chunk-time \
    --input video.mp4 \
    --output_dir chunks/ \
    --duration 30 \
    --overlap 5
```

#### Cut Video by Silence
```bash
python video_utils.py chunk-silence \
    --input video.mp4 \
    --output_dir chunks/ \
    --threshold -30 \
    --min_silence 1.0 \
    --min_chunk 5.0
```

### 3. `batch_process.py` - Batch Processing
Process multiple video chunks with SyncNet in parallel.

**Usage:**
```bash
python batch_process.py \
    --chunks_dir /path/to/chunks \
    --output_dir /path/to/results \
    --max_workers 2
```

**Parameters:**
- `--chunks_dir`: Directory containing video chunks
- `--output_dir`: Output directory for SyncNet results
- `--max_workers`: Maximum parallel workers (default: 2)
- `--min_track`: Minimum track length for SyncNet (default: 5)
- `--min_face_size`: Minimum face size for SyncNet (default: 10)

## Complete Workflow Examples

### Example 1: Process a Single Long Video
```bash
# Process 2-hour Bengali news video
python process_long_video.py \
    --input_video ~/videos/bengali_news_2hours.mp4 \
    --output_dir ~/results/bengali_news \
    --chunk_duration 45 \
    --overlap 10 \
    --min_track 10 \
    --min_face_size 15
```

### Example 2: Manual Chunking + Batch Processing
```bash
# Step 1: Cut video by silence detection
python video_utils.py chunk-silence \
    --input long_video.mp4 \
    --output_dir chunks/ \
    --threshold -25 \
    --min_silence 2.0 \
    --min_chunk 10.0

# Step 2: Extract audio from all chunks
for chunk in chunks/*.mp4; do
    python video_utils.py extract-audio \
        --input "$chunk" \
        --output "audio/$(basename "$chunk" .mp4).wav"
done

# Step 3: Run batch SyncNet analysis
python batch_process.py \
    --chunks_dir chunks/ \
    --output_dir syncnet_results/ \
    --max_workers 3
```

### Example 3: Process Multiple Videos
```bash
# Process all videos in a directory
for video in ~/videos/*.mp4; do
    echo "Processing: $video"
    python process_long_video.py \
        --input_video "$video" \
        --output_dir "~/results/$(basename "$video" .mp4)" \
        --chunk_duration 30 \
        --overlap 5
done
```

## Output Files Explained

### SyncNet Results
Each processed chunk generates:
- **Cropped face videos**: `syncnet_data/pycrop/chunk_XXX/*.avi`
- **Offsets file**: `syncnet_data/pywork/chunk_XXX/offsets.txt`
- **Visualization video**: `syncnet_data/pyavi/chunk_XXX/video_out.avi`

### Summary Files
- **processing_summary.json**: Complete processing results
- **batch_processing_summary.json**: Batch processing statistics

### Sample Offsets File
```
TRACK 0: OFFSET 2, CONF 8.147
```
- **OFFSET**: Audio-visual synchronization offset in frames
- **CONF**: Confidence score (higher = better sync)

## Performance Tips

1. **Chunk Duration**: 
   - 30-60 seconds works well for most content
   - Shorter chunks for fast-changing scenes
   - Longer chunks for stable talking head videos

2. **Overlap**: 
   - 5-10 seconds overlap helps with continuity
   - More overlap for better temporal consistency

3. **Parallel Processing**:
   - Use 2-4 workers for batch processing
   - Monitor CPU/memory usage
   - SyncNet is computationally intensive

4. **Face Detection**:
   - Increase `min_face_size` for distant faces
   - Increase `min_track` for stable tracking
   - Check lighting and video quality

## Troubleshooting

### Common Issues

1. **No faces detected**:
   - Check video quality and lighting
   - Reduce `min_face_size` parameter
   - Try different chunk boundaries

2. **Low confidence scores**:
   - Video may have poor audio-visual sync
   - Check for audio delays or processing artifacts
   - Verify speaker is visible in video

3. **Memory issues**:
   - Reduce `max_workers` in batch processing
   - Process shorter chunks
   - Close other applications

4. **FFmpeg errors**:
   - Ensure FFmpeg is installed and in PATH
   - Check video file format compatibility
   - Verify sufficient disk space

### Debugging

Enable verbose output:
```bash
# Add debug flags to see detailed processing
python process_long_video.py --input video.mp4 --output_dir results/ -v
```

Check individual chunk processing:
```bash
# Test single chunk first
python run_pipeline.py --videofile chunk_000.mp4 --reference test_chunk
python run_syncnet.py --videofile data/work/pycrop/test_chunk/000.avi --reference test_chunk
```

## Dependencies

Required packages (install with `pip install -r requirements.txt`):
- torch>=1.4.0
- torchvision
- opencv-contrib-python
- scipy
- numpy
- Pillow
- python_speech_features
- librosa
- pydub
- scenedetect==0.5.1

System requirements:
- FFmpeg (for video/audio processing)
- CUDA-capable GPU (recommended for faster processing)
- Sufficient disk space for chunks and intermediate files
