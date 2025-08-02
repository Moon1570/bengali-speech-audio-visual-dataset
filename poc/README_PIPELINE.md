# SyncNet Video Processing Pipeline

## Overview
This pipeline processes long videos by cutting them into chunks, extracting audio, and analyzing audio-visual synchronization using SyncNet. It's specifically designed for Bengali speech audio-visual dataset processing.

## What We Accomplished

### ✅ Complete Pipeline Implementation
1. **Video Chunking**: Splits long videos into manageable 30-second chunks with 5-second overlap
2. **Audio Extraction**: Extracts 16kHz mono audio from each chunk  
3. **SyncNet Analysis**: Runs complete face detection, tracking, and lip-sync analysis
4. **Visualization**: Generates output videos with face markings and tracking info
5. **Results Analysis**: Provides detailed sync quality metrics and recommendations

### ✅ Successfully Processed Your Video
- **Input**: `/Users/darklord/Research/Audio Visual/Code/bengali-speech-audio-visual-dataset/downloads/aRHpoSebPPI.mp4`
- **Duration**: 340.61 seconds (5.7 minutes)
- **Chunks Created**: 14 chunks (30s each with 5s overlap)
- **Successful Analysis**: 12/14 chunks (85.7% success rate)
- **No Faces Detected**: 2 chunks (chunks 5 and 6)

### 📊 Quality Results
- **Average Confidence**: 4.944 (moderate quality)
- **Best Chunk**: chunk_000 (confidence: 7.183, offset: -1 frame)
- **Worst Chunk**: chunk_009 (confidence: 2.231, offset: -2 frames)
- **High Quality Chunks**: 6 (>5.0 confidence)
- **Medium Quality Chunks**: 6 (2.0-5.0 confidence)

## Generated Files Structure

```
aRHpoSebPPI_analysis/
├── chunks/                     # Video chunks (14 files)
│   ├── chunk_000.mp4          # 0-30 seconds
│   ├── chunk_001.mp4          # 25-55 seconds  
│   └── ...
├── audio/                      # Extracted audio files
│   ├── chunk_000.wav          # 16kHz mono audio
│   └── ...
├── syncnet_data/               # SyncNet processing data
│   ├── pywork/                # Analysis results
│   │   ├── chunk_000/
│   │   │   └── offsets.txt    # Sync analysis results
│   │   └── ...
│   ├── pyavi/                 # Visualization videos
│   │   ├── chunk_000/
│   │   │   └── video_out.avi  # Video with face markings
│   │   └── ...
│   ├── pycrop/                # Cropped face videos
│   └── pyframes/              # Individual frames
└── processing_summary.json     # Complete results summary
```

## Key Scripts Created

### 1. `process_long_video.py` - Main Processing Pipeline
```bash
python process_long_video.py \
  --input_video "/path/to/video.mp4" \
  --output_dir "analysis_output" \
  --chunk_duration 30 \
  --overlap 5
```

### 2. `analyze_results.py` - Results Analysis
```bash
python analyze_results.py analysis_output/processing_summary.json --detailed --list-files
```

### 3. `process_video_chunks.py` - Alternative Processing Script
```bash
python process_video_chunks.py \
  --video "/path/to/video.mp4" \
  --chunk_duration 30 \
  --max_chunks 5
```

## Understanding SyncNet Results

### Offset Values
- **Negative offset**: Audio leads video (audio comes first)
- **Positive offset**: Video leads audio (video comes first)  
- **Zero offset**: Perfect synchronization
- **±1-2 frames**: Excellent sync
- **±3-5 frames**: Good sync
- **>±10 frames**: Poor sync

### Confidence Scores
- **>7.0**: Excellent confidence
- **5.0-7.0**: Good confidence  
- **2.0-5.0**: Moderate confidence
- **<2.0**: Low confidence

### Your Video Analysis
Most chunks show moderate to good synchronization:
- **Best segments**: chunks 0, 2, 3, 11, 12 (confidence >6.0)
- **Moderate segments**: chunks 1, 7, 8, 9, 10 (confidence 2-5)
- **Problem areas**: chunks 5, 6 (no faces detected)

## Usage for Bengali Speech Dataset

### For Training Data
1. **Use high-confidence chunks** (>5.0) for training data
2. **Extract audio from best chunks** for speech recognition training
3. **Use visualization videos** to verify face detection quality

### For Dataset Expansion
```bash
# Process multiple videos
for video in /path/to/videos/*.mp4; do
  python process_long_video.py \
    --input_video "$video" \
    --output_dir "$(basename "$video" .mp4)_analysis"
done

# Analyze all results
for summary in *_analysis/processing_summary.json; do
  python analyze_results.py "$summary" --detailed
done
```

### Batch Processing Script
Create a batch script to process multiple videos:

```bash
#!/bin/bash
VIDEO_DIR="/Users/darklord/Research/Audio Visual/Code/bengali-speech-audio-visual-dataset/downloads"
OUTPUT_DIR="batch_analysis"

for video in "$VIDEO_DIR"/*.mp4; do
  video_name=$(basename "$video" .mp4)
  echo "Processing: $video_name"
  
  python process_long_video.py \
    --input_video "$video" \
    --output_dir "$OUTPUT_DIR/${video_name}_analysis" \
    --chunk_duration 30 \
    --overlap 5
  
  echo "Analyzing results for: $video_name"
  python analyze_results.py "$OUTPUT_DIR/${video_name}_analysis/processing_summary.json" --detailed
done
```

## Next Steps

1. **Review visualization videos** to ensure face detection quality
2. **Extract high-quality audio chunks** for speech training
3. **Process additional videos** in your dataset
4. **Use sync analysis** to filter quality training data
5. **Combine results** from multiple videos for comprehensive dataset

## File Locations for Your Processed Video

- **Chunks**: `aRHpoSebPPI_analysis/chunks/`
- **Audio**: `aRHpoSebPPI_analysis/audio/`  
- **Sync Results**: `aRHpoSebPPI_analysis/syncnet_data/pywork/*/offsets.txt`
- **Videos with Face Markings**: `aRHpoSebPPI_analysis/syncnet_data/pyavi/*/video_out.avi`
- **Summary**: `aRHpoSebPPI_analysis/processing_summary.json`

The pipeline is now ready to process your entire Bengali speech video dataset efficiently!
