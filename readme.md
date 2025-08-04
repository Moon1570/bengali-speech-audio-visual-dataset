# Bengali Speech Audio-Visual Dataset

## Overview
This project focuses on creating a Bengali speech audio-visual dataset by processing videos, extracting audio, denoising, and transcribing speech. The dataset is designed to support research in speech recognition, audio-visual synchronization, and related fields.

## Features
- **Video Processing**: Downloads and processes videos for dataset creation.
- **Audio Extraction**: Extracts audio from videos and applies denoising techniques.
- **Transcription**: Supports transcription using Whisper and Google Speech APIs.
- **Silence-Based Splitting**: Splits audio and video based on silence detection.
- **Pipeline Automation**: Automates the entire dataset creation pipeline.
- **CLI-based pipeline**: For easy execution and integration.
- **Silence-based splitting**: To intelligently segment audio/video.
- **Two transcription options**: Choose between Whisper (banglaspeech2text model) and Google Speech Recognition.
- **Progress bars**: Visual feedback during processing using tqdm.
- **Structured logging**: Logs progress and issues to console and file (`logs/pipeline.log`).
- **Organized output directory**: Keeps results structured and easy to navigate.

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
### Running the Pipeline
To run the main pipeline:
```bash
python run_pipeline.py <video_path> [--output_root <output_directory>] [--transcribe] [--model <whisper|google>]
```

#### Example
To process a video and transcribe it using Whisper:
```bash
python run_pipeline.py downloads/sample_video.mp4 --transcribe --model whisper
```

To process a video without transcription and specify a custom output directory:
```bash
python run_pipeline.py downloads/sample_video.mp4 --output_root custom_outputs
```

### Show Help
To view all available options and flags:
```bash
python run_pipeline.py --help
```

## Directory Structure
- `audio/`: Contains extracted audio files.
- `denoised_audio/`: Contains denoised audio files.
- `downloads/`: Stores downloaded video files.
- `outputs/`: Contains processed outputs, including metadata and transcriptions.
- `utils/`: Utility scripts for various processing tasks.

## Output Structure
After processing, the structure will look like:

```
outputs/
└── <video_id>/
    ├── audio.wav
    ├── video.mp4
    ├── chunks/
    │   ├── audio/
    │   │   ├── chunk_001.wav
    │   │   ├── chunk_002.wav
    │   │   └── ...
    │   ├── text/            # Whisper transcription
    │   └── text_google/     # Google transcription
    └── metadata.json        # Chunk timestamps & info
```

## Logs
Logs for different stages of the pipeline are stored in the `logs/` directory with descriptive filenames (e.g., `audio_extraction.log`, `transcription.log`).

Example log entry:
```
2025-08-04 21:45:10 [INFO] Starting processing for video: myvideo
2025-08-04 21:45:12 [INFO] ✅ Split into 15 chunks.
2025-08-04 21:45:40 [INFO] ✅ Transcription completed using whisper.
```

## Requirements
- Python 3.8+
- tqdm
- banglaspeech2text
- speechrecognition
- pydub
- ffmpeg (installed in system for audio extraction)

## Future Features
- Labeling the chunks based on emotion, context, etc.

## Contributing
Contributions are welcome! Please fork the repository and submit a pull request with your changes.

