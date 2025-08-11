# Bengali Speech Transcription Pipeline

## Overview

The Bengali Speech Transcription Pipeline is a dedicated tool for converting audio chunks into Bengali text transcriptions. It supports both Google Speech Recognition and Whisper (banglaspeech2text) models, with comprehensive progress tracking, batch processing capabilities, and resume functionality.

## Features

- **Multi-Model Support**: Google Speech Recognition and Whisper transcription
- **Batch Processing**: Process multiple videos simultaneously
- **Progress Tracking**: Persistent session and video-level progress monitoring
- **Resume Capability**: Continue from interrupted transcriptions
- **Comprehensive Reporting**: Detailed statistics and completion reports
- **Error Handling**: Robust error recovery and reporting
- **Performance Metrics**: Processing speed and success rate analytics

## Installation

The transcription pipeline is included with the main Bengali Speech Audio-Visual Dataset project. Make sure you have the required dependencies:

```bash
# Install main project dependencies
pip install -r requirements.txt

# Additional dependencies for transcription
pip install speechrecognition  # For Google Speech Recognition
pip install banglaspeech2text  # For Whisper transcription
```

## Prerequisites

Before using the transcription pipeline, ensure:

1. **Audio chunks are prepared**: Videos must be processed through the main pipeline first
2. **API Access**: For Google Speech Recognition, ensure internet connectivity
3. **Audio format**: Chunks must be in WAV format

## Usage

### Basic Commands

#### Single Video Transcription
```bash
# Transcribe using Google Speech Recognition (default)
python run_transcription_pipeline.py --path outputs/video_name --model google

# Transcribe using Whisper
python run_transcription_pipeline.py --path outputs/video_name --model whisper
```

#### Batch Processing
```bash
# Transcribe all videos in outputs/ using Google
python run_transcription_pipeline.py --path outputs/ --batch --model google

# Transcribe all videos using Whisper
python run_transcription_pipeline.py --path outputs/ --batch --model whisper
```

### Advanced Options

#### Force Re-transcription
```bash
# Override existing transcriptions
python run_transcription_pipeline.py --path outputs/video_name --model google --force
```

#### Status Reports
```bash
# Get transcription status for single video
python run_transcription_pipeline.py --path outputs/video_name --model google --report-only

# Get comprehensive batch report
python run_transcription_pipeline.py --path outputs/ --batch --model google --report-only
```

#### Progress Management
```bash
# View historical progress and statistics
python run_transcription_pipeline.py --show-history

# Clear progress history (creates backup)
python run_transcription_pipeline.py --clear-history
```

## Command-Line Arguments

| Argument | Type | Description | Default |
|----------|------|-------------|---------|
| `--path` | string | Path to video directory or outputs root | Required |
| `--model` | choice | Transcription model (`whisper`, `google`) | `google` |
| `--batch` | flag | Process all videos in directory | `False` |
| `--force` | flag | Force re-transcription | `False` |
| `--report-only` | flag | Generate report without transcribing | `False` |
| `--show-history` | flag | Display historical progress | `False` |
| `--clear-history` | flag | Clear progress history | `False` |

## Output Structure

### Transcript Storage
Transcripts are saved in model-specific directories:

```
outputs/
└── <video_id>/
    └── chunks/
        ├── audio/              # Source audio chunks
        │   ├── chunk_000.wav
        │   ├── chunk_001.wav
        │   └── ...
        ├── text/               # Whisper transcripts
        │   ├── chunk_000.txt
        │   ├── chunk_001.txt
        │   └── ...
        └── text_google/        # Google Speech Recognition transcripts
            ├── chunk_000.txt
            ├── chunk_001.txt
            └── ...
```

### Progress Tracking Files
```
logs/
├── transcription_pipeline.log          # Execution logs
├── transcription_progress.json         # Progress tracking data
└── transcription_progress.json.backup.* # Automatic backups
```

## Progress Tracking System

### Session Tracking
Each pipeline run creates a unique session with:
- **Session ID**: Timestamp-based identifier
- **Model and Mode**: Transcription settings
- **Processing Statistics**: Videos processed, success/failure counts
- **Performance Metrics**: Duration, processing rates
- **Status Tracking**: Running, completed, failed states

### Video-Level Progress
Individual video progress includes:
- **Completion Status**: completed, partial, failed, pending
- **Chunk Statistics**: transcribed/total chunks with percentages
- **Model Association**: Tracks progress per transcription model
- **Timestamps**: Last updated information

### Progress Data Structure
```json
{
  "sessions": [
    {
      "session_id": "20250811_143022",
      "start_time": "2025-08-11T14:30:22",
      "model": "google",
      "mode": "batch",
      "videos_processed": 15,
      "videos_successful": 13,
      "chunks_transcribed": 450,
      "duration_seconds": 896.5
    }
  ],
  "completed_videos": {
    "video_001_google": {
      "status": "completed",
      "chunks_transcribed": 25,
      "total_chunks": 25,
      "completion_rate": 100.0
    }
  }
}
```

## Transcription Models

### Google Speech Recognition
- **Language**: Bengali (bn-BD)
- **Audio Preprocessing**: Normalization and trimming (max 10 seconds)
- **Error Handling**: Unrecognized speech and API error handling
- **Output Directory**: `chunks/text_google/`

### Whisper (banglaspeech2text)
- **Model**: Large Bengali model
- **Processing**: Direct audio file processing
- **Performance**: Generally more accurate for Bengali speech
- **Output Directory**: `chunks/text/`

## Error Handling

### Transcription Errors
- **Unrecognized Speech**: Saves `[Unrecognized Speech]`
- **API Errors**: Saves `[API Error: <details>]`
- **File Errors**: Logs and continues with next chunk

### Session Recovery
- **Automatic Resume**: Continues from last completed chunk
- **Progress Preservation**: Maintains progress even on crashes
- **Backup System**: Automatic backups before clearing history

## Performance Optimization

### Processing Speed
- **Batch Mode**: Parallel processing of multiple videos
- **Skip Completed**: Automatically skips already transcribed chunks
- **Progress Tracking**: Minimal overhead with efficient JSON storage

### Resource Management
- **Memory Efficient**: Processes one chunk at a time
- **Temporary Files**: Automatic cleanup of preprocessing files
- **Error Recovery**: Continues processing despite individual failures

## Monitoring and Analytics

### Real-Time Metrics
- **Processing Rate**: Chunks per second, videos per second
- **Success Rates**: Per-session and historical statistics
- **Duration Tracking**: Time spent on transcription tasks

### Historical Analysis
- **Session History**: View past transcription runs
- **Completion Trends**: Track progress over time
- **Performance Analytics**: Compare different models and sessions

### Status Reports
```
📊 TRANSCRIPTION REPORT (GOOGLE MODEL)
============================================================
📁 Total videos found: 25
✅ Completed videos: 20
⚠️  Partial videos: 3
⏳ Pending videos: 2
🎵 Total audio chunks: 1,250
📝 Transcribed chunks: 1,100
📈 Overall completion rate: 88.0%

📊 HISTORICAL SESSION STATS
────────────────────────────────────────────────────────────
🔄 Total sessions run: 15
✅ Completed sessions: 13
🎯 Videos processed (all time): 150
📈 Success rate (all time): 92.5%
```

## Best Practices

### Workflow Integration
1. **Process Videos First**: Run main pipeline before transcription
2. **Choose Model**: Google for speed, Whisper for accuracy
3. **Monitor Progress**: Use `--show-history` to track completion
4. **Batch Processing**: Use `--batch` for multiple videos

### Error Recovery
1. **Resume Interrupted**: Pipeline automatically resumes from last completed chunk
2. **Check Status**: Use `--report-only` to assess completion status
3. **Force Retry**: Use `--force` to re-transcribe failed chunks

### Performance Tips
1. **Batch Mode**: More efficient for multiple videos
2. **Progress Monitoring**: Regular checks prevent duplicate work
3. **Model Selection**: Choose based on accuracy vs. speed requirements

## Troubleshooting

### Common Issues

#### No Audio Chunks Found
```bash
❌ No .wav files found in: outputs/video_name/chunks/audio/
```
**Solution**: Process video through main pipeline first

#### API Rate Limits (Google)
- **Symptom**: Multiple API errors in succession
- **Solution**: Add delays or switch to Whisper model

#### Partial Transcriptions
- **Check Progress**: `python run_transcription_pipeline.py --path outputs/video_name --report-only`
- **Resume**: Re-run without `--force` to continue from last chunk

### Log Analysis
Check `logs/transcription_pipeline.log` for detailed error information:
```bash
tail -f logs/transcription_pipeline.log
```

## Integration with Main Pipeline

The transcription pipeline integrates seamlessly with the main video processing pipeline:

```bash
# 1. Process video (main pipeline)
python run_pipeline.py downloads/video.mp4 --filter-faces --refine-chunks

# 2. Transcribe chunks (transcription pipeline)
python run_transcription_pipeline.py --path outputs/video --model google

# 3. Check results
python run_transcription_pipeline.py --path outputs/video --report-only
```

## Examples

### Complete Workflow
```bash
# Process multiple videos and transcribe with progress tracking
python run_transcription_pipeline.py --path outputs/ --batch --model google

# Check completion status
python run_transcription_pipeline.py --show-history

# Re-process failed videos
python run_transcription_pipeline.py --path outputs/failed_video --model whisper --force
```

### Production Batch Processing
```bash
# Large-scale transcription with monitoring
python run_transcription_pipeline.py --path outputs/ --batch --model google 2>&1 | tee transcription_log.txt

# Generate final report
python run_transcription_pipeline.py --path outputs/ --batch --report-only
```

## Contributing

When contributing to the transcription pipeline:

1. **Test Both Models**: Ensure compatibility with Google and Whisper
2. **Progress Tracking**: Maintain progress tracking functionality
3. **Error Handling**: Add appropriate error handling and logging
4. **Documentation**: Update this README for new features

## License

This transcription pipeline is part of the Bengali Speech Audio-Visual Dataset project and follows the same license terms.
