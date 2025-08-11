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
- **Transcription Support**: Multiple transcription options (Whisper, Google Speech Recognition)
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

#### Transcription Parameters
- `--transcribe`: Enable transcription
- `--model`: Transcription model (`whisper` or `google`, default: whisper)

### Show Help
To view all available options and flags:
```bash
python run_pipeline.py --help
```

## Directory Structure
- `audio/`: Contains extracted audio files
- `denoised_audio/`: Contains denoised audio files  
- `amplified_denoised_audio/`: Contains amplified denoised audio files
- `downloads/`: Stores downloaded video files
- `outputs/`: Contains processed outputs with metadata and transcriptions
- `utils/`: Utility scripts for processing tasks
  - `face_detection.py`: Face detection and filtering functionality
  - `refine_chunks.py`: High-resolution chunk refinement system
  - `split_by_silence.py`: Silence-based segmentation
  - `denoise_audio.py`: Audio denoising utilities
  - `transcribe_chunks.py`: Transcription processing
- `logs/`: Processing logs and debugging information

## Output Structure
After processing, the structure will look like:

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
    │   ├── text/                # Whisper transcription
    │   └── text_google/         # Google transcription
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
## Logs
Comprehensive logging system tracks all processing stages:
- `logs/pipeline.log`: Main pipeline execution log
- `audio_extraction.log`: Audio processing details  
- `video_downloader.log`: Video download operations
- `transcription.log`: Transcription processing
- `denoising.log`: Audio denoising operations

Example log entries:
```
2025-08-04 21:45:10 [INFO] Starting processing for video: sample_video
2025-08-04 21:45:12 [INFO] ✅ Split into 145 initial chunks
2025-08-04 21:45:15 [INFO] 🎭 Face filtering: 145 → 70 chunks (51.7% reduction)  
2025-08-04 21:45:18 [INFO] ✨ Chunk refinement: 70 → 39 chunks (44.3% additional reduction)
2025-08-04 21:45:40 [INFO] ✅ Transcription completed using whisper
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

