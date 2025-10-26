# Why FLAC is Required for Google Speech Recognition

## Question
> "Why do we need flac? The audios are in wav"

## Answer

You're right that our audio files are in WAV format, but FLAC is still required because of how the Google Speech Recognition library works internally.

## Technical Explanation

### The Process Flow

```
WAV File (Input)
    ↓
SpeechRecognition Library (Python)
    ↓
Internal Conversion: WAV → FLAC (requires 'flac' command-line tool)
    ↓
FLAC Data (compressed)
    ↓
Sent to Google Speech API
    ↓
Transcription Result
```

### Why FLAC?

1. **Compression**: FLAC is a lossless compressed format that's much smaller than WAV
   - WAV: ~10MB/minute (uncompressed)
   - FLAC: ~5MB/minute (lossless compression)

2. **Network Efficiency**: Google's API requires compressed audio to reduce bandwidth
   - Sending WAV files directly would be very slow
   - FLAC provides 50% smaller files without losing quality

3. **Library Implementation**: The `speech_recognition` Python library automatically converts all audio to FLAC before transmission
   - This happens transparently in the background
   - But it requires the `flac` command-line encoder to be installed

### Code Location

In `utils/transcribe_chunks_google.py`:

```python
with sr.AudioFile(tmp_path) as source:  # tmp_path is a WAV file
    audio = recognizer.record(source)    # Library reads WAV
    result = recognizer.recognize_google(audio, language="bn-BD")  # Converts to FLAC internally
```

### The Error We Saw

```
ERROR: FLAC conversion utility not available - consider installing the FLAC 
command line application by running `apt-get install flac`
```

This error occurs in Docker because:
- The `speech_recognition` library tries to call the `flac` command
- The command doesn't exist in the fresh Ubuntu Docker container
- The conversion fails, so the transcription can't happen

**Note**: This works fine when running locally on macOS because FLAC is already installed via Homebrew at `/opt/homebrew/bin/flac`. Docker containers start with a minimal Ubuntu environment and don't have this pre-installed.

## Solution

Add `flac` to the Docker image system dependencies:

```dockerfile
RUN apt-get update && apt-get install -y \
    # ... other packages ...
    flac \           # ← This package provides the FLAC encoder
    # ... other packages ...
    && rm -rf /var/lib/apt/lists/*
```

## Alternative Approaches

### If we wanted to avoid FLAC:

1. **Use Google Cloud Speech-to-Text API directly**
   - More complex setup (requires API keys, authentication)
   - Supports WAV directly
   - More features but requires Google Cloud account

2. **Use pydub to convert WAV → FLAC in Python**
   - Still needs FLAC encoder installed
   - No benefit over current approach

3. **Use only Whisper model**
   - Works directly with WAV files
   - No FLAC needed
   - But downloads 3GB model and slower for batch processing

## Conclusion

**FLAC is necessary** because:
- The `speech_recognition` library design requires it
- It's the most efficient way to send audio to Google's API
- It's a lightweight dependency (~1MB package size)
- It enables lossless compression for network transmission

The current solution (adding `flac` to Docker) is the correct and standard approach for using Google Speech Recognition.

## Related Files

- **Transcription Code**: `utils/transcribe_chunks_google.py`
- **Docker Configuration**: `Dockerfile` (line with `flac` package)
- **Error Fix Documentation**: `DOCKER_FIXES.md`
- **Test Results**: `DOCKER_TEST_RESULTS.md`
