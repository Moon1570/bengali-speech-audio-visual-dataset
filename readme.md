# Bengali Speech Audio-Visual Dataset

## Overview
This project creates a high-quality Bengali speech audio-visual dataset by processing videos through an advanced multi-stage pipeline. The system extracts audio, applies intelligent segmentation based on silence detection, performs face detection to filter out non-speaking segments, and refines chunks to ensure they contain only face content. The dataset is designed to support research in speech recognition, audio-visual synchronization, and related fields.

## Features
- **Advanced Video Processing**: Multi-stage pipeline with intelligent content filtering
- **Audio Extraction & Denoising**: Extracts and cleans audio using advanced denoising techniques
- **Intelligent Silence Detection**: Splits content into sentence-level chunks based on silence patterns
- **Face Detection & Filtering**: Uses OpenCV to identify and filter chunks containing faces
- **Chunk Refinement**: High-resolution analysis to remove non-face segments within chunks
- **Quality Control**: Comprehensive preview generation and quality metrics
- **Modular Transcription Pipeline**: Clean, modular architecture with separated utilities
- **Single File Transcripts**: Creates unified transcript files with input file names for easy management
- **Input Folder Saving**: Transcripts saved directly alongside source files for better organization
- **Multi-Model Transcription**: Support for Whisper and Google Speech Recognition
- **CLI-based Pipeline**: Comprehensive command-line interface with extensive configuration options
- **Progress Tracking**: Visual feedback during processing using tqdm with detailed statistics
- **Structured Logging**: Multi-level logging to console and files for debugging and monitoring
- **Organized Output**: Well-structured output directory with metadata and previews

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/Moon1570/bengali-speech-audio-visual-dataset.git
   cd bengali-speech-audio-visual-dataset
   ```
2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # Linux/Mac
   venv\Scripts\activate      # Windows
   ```
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Pipeline
To run the basic pipeline without face detection:
```bash
python run_pipeline.py <video_path> [--output_root <output_directory>] [--transcribe] [--model <whisper|google>]
```

### Advanced Pipeline with Face Detection
To run the pipeline with face detection and filtering:
```bash
python run_pipeline.py <video_path> --filter-faces [--face-threshold 0.3] [--min-face-duration 1.0]
```

### Complete Pipeline with Chunk Refinement
To run the full pipeline with face detection and chunk refinement:
```bash
python run_pipeline.py <video_path> --filter-faces --refine-chunks [--refine-sample-rate 0.1] [--min-chunk-duration 1.0]
```

### Transcription Pipeline
For dedicated transcription processing with modular architecture:
```bash
# Single video/audio transcription with single file output
python run_transcription_pipeline.py --path video_file.mp4 --model google

# Single audio file transcription
python run_transcription_pipeline.py --path audio/sample.wav --model whisper

# Batch transcription of multiple videos
python run_transcription_pipeline.py --path outputs/ --batch --model whisper

# View transcription progress and history
python run_transcription_pipeline.py --show-history
```

#### Output Structure
The transcription pipeline now creates:
- **Single transcript file**: `{input_filename}.txt` (combined content from all chunks)
- **Individual chunks**: `{input_filename}_transcripts_{model}/` (detailed chunk-by-chunk files)
- **Summary file**: `{input_filename}_{model}_summary.txt` (processing statistics and preview)

All files are saved directly in the input folder alongside the source file for easy management.

#### Example Commands
Process a video with complete face filtering and refinement:
```bash
python run_pipeline.py downloads/sample_video.mp4 --filter-faces --refine-chunks --face-threshold 0.3 --refine-sample-rate 0.1 --min-chunk-duration 1.0
```

Process with transcription using Whisper:
```bash
python run_pipeline.py downloads/sample_video.mp4 --filter-faces --refine-chunks --transcribe --model whisper
```

Process with custom silence detection parameters:
```bash
python run_pipeline.py downloads/sample_video.mp4 --filter-faces --silence-thresh -40 --min-silence-len 500 --keep-silence 100
```

### Configuration Options

#### Face Detection Parameters
- `--filter-faces`: Enable face detection filtering
- `--face-threshold`: Confidence threshold for face detection (0.1-1.0, default: 0.3)
- `--min-face-duration`: Minimum duration of face presence required (seconds, default: 1.0)

#### Chunk Refinement Parameters  
- `--refine-chunks`: Enable high-resolution chunk refinement
- `--refine-sample-rate`: Sampling rate for refinement analysis (seconds, default: 0.1)
- `--min-chunk-duration`: Minimum duration for refined chunks (seconds, default: 1.0)

#### Silence Detection Parameters
- `--silence-thresh`: Silence threshold in dB (default: -40)
- `--min-silence-len`: Minimum silence length in ms (default: 500)
- `--keep-silence`: Silence padding in ms (default: 100)
- `--min-chunk-duration`: Minimum chunk duration in seconds (default: 1.0)

#### Transcription Parameters (Main Pipeline)
- `--transcribe`: Enable transcription during main pipeline
- `--model`: Transcription model (`whisper` or `google`, default: whisper)

### Show Help
To view all available options and flags:
```bash
python run_pipeline.py --help
python run_transcription_pipeline.py --help
```

## Transcription Pipeline

The project includes a dedicated modular transcription pipeline (`run_transcription_pipeline.py`) for efficient processing of audio chunks into Bengali text. The pipeline features a clean modular architecture with separated utilities and creates single transcript files for easy management.

### Modular Architecture
The transcription system is organized into four main utility modules:

- **`utils/audio_processing.py`**: Audio/video processing, extraction, and chunking
- **`utils/progress_tracking.py`**: Session management and progress statistics  
- **`utils/file_discovery.py`**: File operations and transcript saving
- **`utils/transcription_manager.py`**: Transcription coordination and reporting

### Key Features
- **Single File Transcripts**: Creates unified `{filename}.txt` files with input file names
- **Input Folder Saving**: Transcripts saved directly alongside source files
- **Multi-Model Support**: Google Speech Recognition and Whisper transcription
- **Batch Processing**: Process multiple videos simultaneously
- **Progress Tracking**: Persistent session and video-level progress monitoring
- **Resume Capability**: Continue from interrupted transcriptions
- **Performance Analytics**: Processing speed and success rate metrics
- **Dual Output Mode**: Single files for convenience + detailed chunks for analysis

### Usage Examples
```bash
# Transcribe single video with Google Speech Recognition
python run_transcription_pipeline.py --path data/video.mp4 --model google
# Output: data/video.txt, data/video_transcripts_google/, data/video_google_summary.txt

# Transcribe audio file with Whisper
python run_transcription_pipeline.py --path audio/speech.wav --model whisper
# Output: audio/speech.txt, audio/speech_transcripts_whisper/, audio/speech_whisper_summary.txt

# Batch process all videos with Google
python run_transcription_pipeline.py --path data/ --batch --model google

# Check transcription status and history
python run_transcription_pipeline.py --show-history

# Generate status report without transcribing
python run_transcription_pipeline.py --path outputs/ --batch --report-only
```

### Output Structure
For each processed file, the system creates:

1. **Single transcript file**: `{filename}.txt`
   - Combined content from all audio chunks
   - Clean, continuous text suitable for most use cases
   
2. **Detailed chunks directory**: `{filename}_transcripts_{model}/`
   - Individual chunk files: `chunk_000.txt`, `chunk_001.txt`, etc.
   - Useful for detailed analysis and debugging
   
3. **Summary file**: `{filename}_{model}_summary.txt`
   - Processing statistics and metadata
   - Preview of transcription content
   - Timestamp and model information

### Legacy Output Locations (Pre-processed Data)
- **Google Transcripts**: `outputs/<video_id>/chunks/text_google/`
- **Whisper Transcripts**: `outputs/<video_id>/chunks/text/`
- **Progress Tracking**: `logs/transcription_progress.json`

For detailed documentation, see [Transcription Pipeline Guide](docs/transcription_pipeline.md).

## Directory Structure
- `audio/`: Contains extracted audio files and their transcripts
- `denoised_audio/`: Contains denoised audio files  
- `amplified_denoised_audio/`: Contains amplified denoised audio files
- `downloads/`: Stores downloaded video files
- `data/`: Raw input data and transcripts (e.g., `data/poor_quality/`)
- `outputs/`: Contains processed outputs with metadata and transcriptions (legacy)
- `utils/`: Modular utility scripts for processing tasks
  - `audio_processing.py`: Audio/video processing, extraction, and chunking
  - `progress_tracking.py`: Session management and progress statistics
  - `file_discovery.py`: File operations and transcript saving
  - `transcription_manager.py`: Transcription coordination and reporting
  - `face_detection.py`: Face detection and filtering functionality
  - `refine_chunks.py`: High-resolution chunk refinement system
  - `split_by_silence.py`: Silence-based segmentation
  - `denoise_audio.py`: Audio denoising utilities
  - `transcribe_chunks.py`: Whisper transcription processing
  - `transcribe_chunks_google.py`: Google Speech Recognition processing
- `logs/`: Processing logs and debugging information
- `docs/`: Documentation and guides
  - `transcription_pipeline.md`: Detailed transcription pipeline documentation

## Output Structure
The system supports two output modes depending on the input type:

### Input Folder Mode (Raw Files)
When processing raw audio/video files, transcripts are saved directly alongside the source:

```
data/poor_quality/
├── chunk_002.mp4                    # Original video file
├── chunk_002.txt                    # Single combined transcript
├── chunk_002_google_summary.txt     # Processing summary
└── chunk_002_transcripts_google/    # Detailed chunks
    ├── chunk_000.txt
    ├── chunk_001.txt
    └── ...

audio/
├── sample.wav                       # Original audio file  
├── sample.txt                       # Single combined transcript
├── sample_whisper_summary.txt       # Processing summary
└── sample_transcripts_whisper/      # Detailed chunks
    ├── chunk_000.txt
    ├── chunk_001.txt
    └── ...
```

### Legacy Output Mode (Pre-processed)
For pre-processed directories in outputs/, the traditional structure is maintained:

```
outputs/
└── <video_id>/
    ├── video.mp4                # Original video file
    ├── video.wav                # Extracted audio
    ├── metadata.json            # Processing metadata and timestamps
    ├── chunks/
    │   ├── audio/               # Audio chunks
    │   │   ├── chunk_000.wav
    │   │   ├── chunk_001.wav
    │   │   └── ...
    │   ├── video/               # Video chunks (if face filtering enabled)
    │   │   ├── chunk_000.mp4
    │   │   ├── chunk_001.mp4
    │   │   └── ...
    │   ├── text/                # Whisper transcriptions
    │   │   ├── chunk_000.txt
    │   │   ├── chunk_001.txt
    │   │   └── ...
    │   └── text_google/         # Google Speech Recognition transcriptions
    │       ├── chunk_000.txt
    │       ├── chunk_001.txt
    │       └── ...
    ├── face_detection_previews/ # Face detection preview images
    │   ├── chunk_000_faces.jpg
    │   ├── chunk_001_faces.jpg
    │   └── ...
    └── refinement_previews/     # Before/after refinement comparisons
        ├── refinement_000.jpg
        ├── refinement_001.jpg
        └── ...
```

## Processing Pipeline

The system uses a sophisticated multi-stage processing pipeline:

### Stage 1: Silence Detection
- Analyzes audio to identify natural speech boundaries
- Creates initial chunks based on silence patterns
- Configurable silence thresholds and minimum chunk durations

### Stage 2: Face Detection (Optional)
- Uses OpenCV Haar cascade classifiers to detect faces in video chunks
- Filters out chunks that don't contain sufficient face content
- Generates preview images showing detected faces
- Reduces dataset size by removing non-speaking segments

### Stage 3: Chunk Refinement (Optional)  
- High-resolution analysis of remaining chunks (0.1s sampling)
- Identifies and removes sub-segments without faces within chunks
- Creates refined chunks containing only face segments
- Generates before/after comparison previews
- Significantly improves dataset quality by eliminating mixed content

### Quality Metrics
The pipeline provides comprehensive statistics:
- Initial chunk count from silence detection
- Reduction percentages after face filtering
- Additional reduction from chunk refinement
- Total duration changes and quality improvements

## Logs
Comprehensive logging system tracks all processing stages:
- `logs/pipeline.log`: Main pipeline execution log
- `logs/transcription_pipeline.log`: Dedicated transcription pipeline log
- `logs/transcription_progress.json`: Progress tracking and session history
- `audio_extraction.log`: Audio processing details  
- `video_downloader.log`: Video download operations
- `transcription.log`: Transcription processing (main pipeline)
- `denoising.log`: Audio denoising operations

Example log entries:
```
2025-08-04 21:45:10 [INFO] Starting processing for video: sample_video
2025-08-04 21:45:12 [INFO] ✅ Split into 145 initial chunks
2025-08-04 21:45:15 [INFO] 🎭 Face filtering: 145 → 70 chunks (51.7% reduction)  
2025-08-04 21:45:18 [INFO] ✨ Chunk refinement: 70 → 39 chunks (44.3% additional reduction)
2025-08-04 21:45:40 [INFO] ✅ Transcription completed using whisper

# Transcription Pipeline Logs
2025-08-04 22:10:15 [INFO] 🚀 Starting Bengali Speech Transcription Pipeline
2025-08-04 22:10:16 [INFO] 🎯 Processing video: sample_video (39 chunks)
2025-08-04 22:12:30 [INFO] ✅ Transcription completed for sample_video in 134.2s
2025-08-04 22:12:30 [INFO] ⚡ Rate: 0.29 chunks/second
```

## Requirements
- Python 3.8+
- OpenCV (cv2) for face detection
- MoviePy for video processing  
- pydub for audio manipulation
- tqdm for progress tracking
- banglaspeech2text for Whisper transcription
- speechrecognition for Google Speech API
- ffmpeg (system installation required for audio/video processing)

## Complete Workflow

### End-to-End Processing
For complete dataset creation, use both pipelines in sequence:

```bash
# Step 1: Process video with face detection and refinement
python run_pipeline.py downloads/video.mp4 --filter-faces --refine-chunks

# Step 2: Transcribe the processed chunks (creates single file + detailed chunks)
python run_transcription_pipeline.py --path outputs/video --model google

# Step 3: Verify completion
python run_transcription_pipeline.py --path outputs/video --report-only
```

### Batch Processing Workflow
For large-scale dataset creation with single transcript files:

```bash
# Process multiple raw videos directly
python run_transcription_pipeline.py --path data/videos/ --batch --model google

# Process audio files
python run_transcription_pipeline.py --path audio/ --batch --model whisper

# Batch transcribe pre-processed outputs
python run_transcription_pipeline.py --path outputs/ --batch --model google

# Generate comprehensive report
python run_transcription_pipeline.py --show-history
```

### Quality Assurance Workflow
```bash
# Check processing status across all directories
python run_transcription_pipeline.py --path data/ --batch --report-only

# Re-process failed videos with force flag
python run_transcription_pipeline.py --path data/failed_video.mp4 --model whisper --force

# Generate final statistics
python run_transcription_pipeline.py --show-history
```

## Performance Optimization
The pipeline includes several optimization features:
- Efficient face detection with configurable thresholds
- High-resolution sampling for precise chunk boundaries
- Memory-efficient video processing for large files
- Parallel processing where applicable
- Comprehensive caching to avoid reprocessing

## Future Features
- Advanced emotion detection and labeling
- Multi-speaker detection and separation
- Improved noise reduction algorithms
- Real-time processing capabilities
- Integration with additional speech recognition models

## Contributing
Contributions are welcome! Please fork the repository and submit a pull request with your changes.

