# Bengali Speech Dataset - Processing Parameters Documentation

**Last Updated**: October 10, 2025  
**Pipeline Version**: 1.0  
**Repository**: bengali-speech-audio-visual-dataset

---

## Table of Contents
1. [Audio Processing](#1-audio-processing)
2. [Video Processing](#2-video-processing)
3. [Speech Detection & Chunking](#3-speech-detection--chunking)
4. [Face Detection & Filtering](#4-face-detection--filtering)
5. [Quality Filtering (SyncNet)](#5-quality-filtering-syncnet)
6. [Transcription Processing](#6-transcription-processing)
7. [Complete Parameters Reference](#7-complete-parameters-reference)
8. [Processing Flow](#8-processing-flow)

---

## 1. Audio Processing

### 1.1 Noise Reduction

**Status**: ✅ **Implemented**  
**File**: `utils/audio_processing.py`  
**Method**: Spectral Gating (frequency-domain filtering)

#### Implementation Details
```python
def reduce_noise(audio_data, sample_rate, noise_profile_duration=1.0):
    """Spectral gating noise reduction using STFT"""
    # Uses first 1 second as noise profile
    noise_sample = audio_data[:int(sample_rate * noise_profile_duration)]
    
    # Compute noise profile via Short-Time Fourier Transform
    noise_stft = librosa.stft(noise_sample)
    noise_profile = np.mean(np.abs(noise_stft), axis=1)
    
    # Apply spectral gating
    audio_stft = librosa.stft(audio_data)
    magnitude = np.abs(audio_stft)
    phase = np.angle(audio_stft)
    
    # Suppress frequencies below noise threshold
    noise_threshold = noise_profile[:, np.newaxis] * 1.5
    magnitude_cleaned = np.where(
        magnitude > noise_threshold,
        magnitude - noise_threshold,
        0
    )
    
    # Reconstruct audio
    cleaned_stft = magnitude_cleaned * np.exp(1j * phase)
    return librosa.istft(cleaned_stft)
```

#### Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| **Method** | Spectral Gating | Frequency-domain noise suppression |
| **Noise Profile Duration** | 1.0 second | Duration of audio used for noise estimation |
| **Noise Threshold Multiplier** | 1.5x | Multiplier applied to noise profile |
| **Window Type** | Hann (default) | STFT window function |
| **Hop Length** | 512 samples | STFT hop size (~23ms at 22050 Hz) |
| **Frame Length** | 2048 samples | STFT window size (~93ms at 22050 Hz) |

#### When Applied
- During audio extraction in `run_pipeline.py`
- Before Voice Activity Detection (VAD)
- Before speech amplification
- **Activation**: Optional via `--reduce-noise` flag

#### Algorithm Flow
1. Extract first 1 second of audio as noise profile
2. Compute STFT of noise sample
3. Calculate average magnitude per frequency bin
4. Apply 1.5x threshold multiplier
5. Process full audio with STFT
6. Suppress frequencies below noise threshold
7. Reconstruct time-domain signal via inverse STFT

---

### 1.2 Speech Amplification

**Status**: ✅ **Implemented**  
**File**: `utils/audio_processing.py`  
**Method**: RMS-based normalization

#### Implementation Details
```python
def amplify_speech(audio_data, target_dBFS=-20.0):
    """Normalize audio to target loudness level"""
    # Calculate current Root Mean Square
    rms = np.sqrt(np.mean(audio_data**2))
    
    if rms > 0:
        # Convert to dBFS (decibels relative to full scale)
        current_dBFS = 20 * np.log10(rms)
        
        # Calculate required gain
        gain_dB = target_dBFS - current_dBFS
        gain_linear = 10 ** (gain_dB / 20)
        
        # Apply gain with clipping prevention
        amplified = audio_data * gain_linear
        amplified = np.clip(amplified, -1.0, 1.0)
        
        return amplified
    return audio_data
```

#### Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| **Method** | RMS Normalization | Root Mean Square based volume adjustment |
| **Target Level** | -20.0 dBFS | Target loudness in decibels full scale |
| **Clipping Prevention** | Yes | Hard limits at [-1.0, 1.0] |
| **Gain Calculation** | Logarithmic | dB scale conversion |
| **Dynamic Range** | Preserved | Maintains relative amplitude differences |

#### When Applied
- After noise reduction (if enabled)
- Before VAD processing
- Before chunking
- **Activation**: Optional via `--amplify-speech` flag

#### Audio Levels Reference
- **0 dBFS**: Maximum digital level (clipping point)
- **-20 dBFS**: Target level (clear, loud speech)
- **-40 dBFS**: Quiet speech
- **-60 dBFS**: Very quiet / background noise

---

### 1.3 Audio Extraction

**File**: `utils/audio_processing.py`

#### Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| **Sample Rate** | 16000 Hz | Standard for speech recognition |
| **Channels** | 1 (Mono) | Single channel audio |
| **Bit Depth** | 16 bits | Standard PCM audio quality |
| **Format** | WAV | Uncompressed audio format |
| **Encoding** | PCM (Linear16) | Pulse Code Modulation |

---

## 2. Video Processing

### 2.1 Face Detection

**Status**: ✅ **Implemented**  
**File**: `utils/face_detection.py`  
**Algorithm**: Haar Cascade Classifier (OpenCV)

#### Implementation Details
```python
def detect_faces_in_video(video_path, 
                         detection_interval=5,
                         min_detection_confidence=0.5,
                         scale_factor=1.1,
                         min_neighbors=5):
    """Haar Cascade face detection"""
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    )
    
    faces = face_cascade.detectMultiScale(
        gray_frame,
        scaleFactor=scale_factor,
        minNeighbors=min_neighbors,
        minSize=(30, 30)
    )
```

#### Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| **Algorithm** | Haar Cascade | Classical computer vision method |
| **Model** | `haarcascade_frontalface_default.xml` | Pre-trained frontal face detector |
| **Detection Interval** | 5 frames | Process every 5th frame for performance |
| **Scale Factor** | 1.1 | Image pyramid scale reduction (1.05-1.4 typical) |
| **Min Neighbors** | 5 | Quality threshold (higher = stricter detection) |
| **Min Face Size** | 30×30 pixels | Minimum detectable face dimensions |
| **Min Detection Confidence** | 0.5 (50%) | Confidence threshold |
| **Color Space** | Grayscale | Convert to gray for detection |

#### Face Filtering Logic
```python
def has_faces(video_path, min_face_frames=5):
    """Check if video contains sufficient face frames"""
    face_count = 0
    for frame in sample_frames:
        if detect_face(frame):
            face_count += 1
    
    return face_count >= min_face_frames
```

#### Face Filtering Criteria

| Criterion | Value | Description |
|-----------|-------|-------------|
| **Minimum Face Frames** | 5 frames | Must detect faces in ≥5 frames |
| **Sampling Strategy** | Every 5th frame | Balance between speed and accuracy |
| **Purpose** | Quality control | Remove chunks without visible speakers |
| **Applied In** | Step 1 | Chunk creation with `--filter-faces` flag |

---

### 2.2 Scene Detection

**File**: `utils/video_processing.py`  
**Library**: PySceneDetect

#### Implementation Details
```python
def detect_scenes(video_path, threshold=27.0):
    """Detect scene changes in video"""
    video_manager = VideoManager([video_path])
    scene_manager = SceneManager()
    
    # Content-based scene detection
    scene_manager.add_detector(
        ContentDetector(threshold=threshold)
    )
```

#### Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| **Method** | Content Detector | Frame difference analysis |
| **Threshold** | 27.0 | Scene change sensitivity (0-100 scale) |
| **Algorithm** | HSV color space difference | Compares consecutive frames |
| **Use Case** | Scene boundary detection | Align chunks with visual changes |

#### Threshold Guidelines
- **20-25**: More sensitive (more cuts, shorter scenes)
- **27-30**: Default sensitivity (balanced)
- **30-40**: Less sensitive (fewer cuts, longer scenes)

---

### 2.3 Video Export Settings

#### Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| **Codec** | H.264 | Standard video compression |
| **Container** | MP4 | Universal video format |
| **Audio Codec** | AAC / WAV | Depends on processing stage |
| **FPS** | Preserved | Maintains source frame rate (typically 25-30) |
| **Resolution** | Preserved | Maintains source dimensions |
| **Pixel Format** | YUV420p | Standard color format |

---

## 3. Speech Detection & Chunking

### 3.1 Voice Activity Detection (VAD)

**Status**: ✅ **Implemented**  
**File**: `utils/audio_processing.py`  
**Library**: WebRTC VAD (Google's voice activity detector)

#### Implementation Details
```python
def detect_speech_segments(audio_path, 
                          aggressiveness=3,
                          frame_duration=30,
                          padding_duration=300):
    """WebRTC VAD-based speech detection"""
    vad = webrtcvad.Vad(aggressiveness)
    
    # Process audio in frames
    for frame in generate_frames(audio, frame_duration):
        is_speech = vad.is_speech(frame, sample_rate)
        
        # Accumulate speech segments
        # Apply padding
        # Merge close segments
```

#### Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| **Library** | WebRTC VAD | Google's production-grade VAD |
| **Aggressiveness** | 3 | 0=least aggressive, 3=most aggressive |
| **Frame Duration** | 30 ms | Processing window (10/20/30 ms supported) |
| **Padding Duration** | 300 ms | Buffer before/after speech regions |
| **Min Speech Duration** | 250 ms | Minimum continuous speech required |
| **Max Silence Gap** | 300 ms | Maximum gap before creating new chunk |
| **Sample Rate** | 16000 Hz | Required for WebRTC VAD |
| **Channels** | 1 (Mono) | VAD requires mono audio |

#### Aggressiveness Levels
- **0**: Least aggressive (keeps more audio, may include noise)
- **1**: Low aggressiveness (permissive)
- **2**: Moderate aggressiveness (balanced)
- **3**: Most aggressive (only clear speech, more silence removal) ✅ **Current setting**

#### Processing Flow
1. Convert audio to 16kHz mono PCM
2. Split into 30ms frames
3. VAD classifies each frame as speech/non-speech
4. Add 300ms padding around speech regions
5. Merge segments with gaps < 300ms
6. Filter out segments < 250ms

---

### 3.2 Energy-Based Speech Detection

**Status**: ✅ **Implemented (Fallback)**  
**File**: `utils/audio_processing.py`  
**Library**: librosa

#### Implementation Details
```python
def detect_speech_librosa(audio_path,
                         top_db=40,
                         frame_length=2048,
                         hop_length=512):
    """Energy-based speech detection using librosa"""
    intervals = librosa.effects.split(
        y=audio_data,
        top_db=top_db,
        frame_length=frame_length,
        hop_length=hop_length
    )
```

#### Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| **Method** | Short-Time Energy | Amplitude-based thresholding |
| **Top dB Threshold** | 40 dB | dB below peak amplitude |
| **Frame Length** | 2048 samples | ~93ms at 22050 Hz |
| **Hop Length** | 512 samples | ~23ms at 22050 Hz |
| **Reference** | Peak amplitude | Calculated from entire signal |

#### Threshold Guidelines
- **20 dB**: Less aggressive (keeps more audio, including quiet speech)
- **30 dB**: Moderate filtering
- **40 dB**: Aggressive filtering (only loud speech) ✅ **Current setting**
- **60 dB**: Very aggressive (may lose quiet speech)

#### When Used
- Fallback if WebRTC VAD fails
- Alternative for music/non-speech audio
- Can be combined with VAD for higher confidence

---

### 3.3 Chunking Strategy

**File**: `run_pipeline.py`

#### Implementation Logic
```python
def process_video(video_path, 
                 min_chunk_duration=2.0,
                 max_chunk_duration=10.0,
                 merge_gap=0.5):
    """Create speech chunks from video"""
    
    # 1. Detect speech segments (VAD)
    speech_segments = detect_speech_segments(audio_path)
    
    # 2. Merge close segments
    merged = merge_close_segments(
        speech_segments,
        max_gap=merge_gap  # 0.5 seconds
    )
    
    # 3. Split long segments
    final_chunks = split_long_segments(
        merged,
        max_duration=max_chunk_duration  # 10 seconds
    )
    
    # 4. Filter short segments
    filtered = filter_short_segments(
        final_chunks,
        min_duration=min_chunk_duration  # 2 seconds
    )
    
    return filtered
```

#### Parameters

| Parameter | Value | CLI Configurable | Description |
|-----------|-------|------------------|-------------|
| **Min Chunk Duration** | 2.0 seconds | ✅ `--min-chunk-duration` | Minimum final chunk length |
| **Max Chunk Duration** | 10.0 seconds | ❌ | Maximum final chunk length |
| **Merge Gap** | 0.5 seconds | ❌ | Merge segments closer than this |
| **VAD Padding** | 0.3 seconds | ❌ | Buffer around speech |
| **Min Speech** | 0.25 seconds | ❌ | Minimum continuous speech |
| **Max Silence** | 0.3 seconds | ❌ | Maximum silence gap within chunk |

#### Chunking Algorithm Flow
```
Input Audio
    ↓
[VAD Detection]
    ├─ Identify speech frames (30ms windows)
    ├─ Apply aggressiveness=3 threshold
    └─ Generate initial segments
    ↓
[Padding]
    ├─ Add 300ms before each segment start
    └─ Add 300ms after each segment end
    ↓
[Merging]
    ├─ Identify segments < 500ms apart
    ├─ Merge into single chunk
    └─ Re-validate speech content
    ↓
[Splitting]
    ├─ Find segments > 10 seconds
    ├─ Split at silence points
    └─ Maintain minimum 2s per chunk
    ↓
[Filtering]
    ├─ Remove chunks < 2 seconds
    ├─ Verify audio quality
    └─ Check face presence (if enabled)
    ↓
[Alignment]
    ├─ Sync audio and video cuts
    ├─ Align with scene changes (if refinement enabled)
    └─ Generate final chunks
    ↓
Output Chunks
```

---

### 3.4 Chunk Refinement

**Status**: ✅ **Optional**  
**File**: `run_pipeline.py`  
**Activation**: `--refine-chunks` flag

#### Implementation Details
```python
def refine_chunks(chunks, 
                 scene_changes,
                 face_detections):
    """Refine chunk boundaries using scene and face data"""
    
    refined_chunks = []
    for chunk in chunks:
        # Align with scene changes (±500ms tolerance)
        aligned = align_with_scenes(chunk, scene_changes)
        
        # Verify face presence
        if has_sufficient_faces(aligned, face_detections):
            refined_chunks.append(aligned)
        else:
            # Log rejected chunk
            logger.warning(f"Chunk rejected: insufficient faces")
    
    return refined_chunks
```

#### Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| **Scene Alignment Tolerance** | 500 ms | Maximum distance to snap to scene change |
| **Face Verification** | 30% coverage | Must have faces in ≥30% of frames |
| **Boundary Adjustment** | Enabled | Snap to nearest scene change |
| **Quality Re-check** | Enabled | Re-verify audio energy after adjustment |

#### Refinement Benefits
- Better visual continuity (aligns with scene changes)
- Improved face presence (filters low-quality chunks)
- Cleaner boundaries (reduces mid-sentence cuts)
- Higher overall quality (multi-criteria validation)

---

## 4. Face Detection & Filtering

### 4.1 Detection Algorithm

**Algorithm**: Haar Cascade (OpenCV)  
**Model**: `haarcascade_frontalface_default.xml`  
**Type**: Classical computer vision (not deep learning)

#### Detection Process
```
Video Frame
    ↓
[Preprocessing]
    ├─ Convert to grayscale
    ├─ Apply histogram equalization
    └─ Resize if needed
    ↓
[Multi-Scale Detection]
    ├─ Create image pyramid (scale=1.1)
    ├─ Apply Haar features at each scale
    ├─ Sliding window search
    └─ Collect candidate regions
    ↓
[Non-Maximum Suppression]
    ├─ Group overlapping detections
    ├─ Apply minNeighbors=5 threshold
    └─ Select best candidates
    ↓
[Filtering]
    ├─ Minimum size check (30×30 px)
    ├─ Confidence threshold (0.5)
    └─ Return face bounding boxes
    ↓
Face Coordinates (x, y, w, h)
```

### 4.2 Face Filtering Criteria

#### Parameters

| Criterion | Value | Description |
|-----------|-------|-------------|
| **Min Face Frames** | 5 frames | Minimum frames with detected faces |
| **Detection Interval** | Every 5 frames | Sample rate for performance |
| **Min Face Size** | 30×30 pixels | Smallest detectable face |
| **Min Confidence** | 0.5 (50%) | Detection confidence threshold |
| **Scale Factor** | 1.1 | Image pyramid step size |
| **Min Neighbors** | 5 | Quality threshold (reduces false positives) |

#### Filtering Logic
```python
def filter_chunks_by_faces(chunks, min_face_frames=5):
    """Filter chunks based on face presence"""
    filtered = []
    
    for chunk in chunks:
        face_frame_count = 0
        total_sampled = 0
        
        # Sample every 5th frame
        for i in range(0, len(chunk.frames), 5):
            total_sampled += 1
            if detect_face(chunk.frames[i]):
                face_frame_count += 1
        
        # Calculate face coverage
        face_coverage = face_frame_count / total_sampled
        
        # Accept if meets threshold
        if face_frame_count >= min_face_frames:
            filtered.append(chunk)
            logger.info(f"✓ Chunk accepted: {face_coverage*100:.1f}% face coverage")
        else:
            logger.warning(f"✗ Chunk rejected: only {face_frame_count} face frames")
    
    return filtered
```

---

## 5. Quality Filtering (SyncNet)

### 5.1 Audio-Visual Synchronization

**External Tool**: SyncNet Python (separate repository)  
**Script**: `filter_videos_by_sync_score.py`  
**Method**: Deep learning-based audio-visual correlation

#### Process Overview
```
Video Chunk
    ↓
[Audio Feature Extraction]
    ├─ Extract audio at 16kHz
    ├─ Compute MFCC (13 coefficients)
    ├─ Frame size: 5 frames (~200ms)
    └─ Hop size: 1 frame (80% overlap)
    ↓
[Visual Feature Extraction]
    ├─ Detect face/mouth region
    ├─ Crop to mouth area
    ├─ Resize to 112×112 pixels
    ├─ Extract CNN embeddings
    └─ Frame size: 5 frames (~200ms)
    ↓
[Correlation Analysis]
    ├─ Compute Pearson correlation
    ├─ Account for temporal offset
    ├─ Generate sync confidence score
    └─ Score range: 0.0 to 1.0
    ↓
[Quality Classification]
    ├─ Compare to preset threshold
    ├─ good_quality/ (above threshold)
    └─ bad_quality/ (below threshold)
    ↓
Filtered Chunks
```

### 5.2 SyncNet Parameters

#### Processing Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| **Window Size** | 5 frames | Temporal window for correlation (~200ms at 25fps) |
| **Overlap** | 1 frame | 80% overlap between windows |
| **Audio Features** | MFCC-13 | 13 Mel-frequency cepstral coefficients |
| **Visual Features** | CNN embeddings | Deep learning mouth region features |
| **Correlation Method** | Pearson | Statistical correlation coefficient |
| **Max Workers** | 8 | Parallel processing threads |
| **Temporal Offset** | ±5 frames | Search range for best sync alignment |

#### Quality Presets

| Preset | Threshold | Keep Rate | Description |
|--------|-----------|-----------|-------------|
| **high** | 0.75 | ~30-50% | Strict filtering, best quality, fewer chunks |
| **medium** | 0.55 | ~50-70% | Balanced filtering, good quality |
| **low** | 0.35 | ~70-90% | Lenient filtering, more chunks, lower quality |

#### Preset Selection Guidelines
- **high**: For final datasets, research papers, high-quality demonstrations
- **medium**: For training datasets, balanced quality/quantity ✅ **Recommended**
- **low**: For data exploration, maximum data retention

### 5.3 SyncNet Score Interpretation

| Score Range | Quality | Interpretation | Action |
|-------------|---------|----------------|--------|
| **0.8 - 1.0** | Excellent | Perfect lip-sync, ideal for AVSR | ✅ Keep (all presets) |
| **0.7 - 0.8** | Very Good | Strong sync, minor deviations | ✅ Keep (high preset) |
| **0.5 - 0.7** | Good | Acceptable sync, some lag | ✅ Keep (medium preset) |
| **0.3 - 0.5** | Fair | Noticeable sync issues | ✅ Keep (low preset only) |
| **0.0 - 0.3** | Poor | Significant desync, unusable | ❌ Reject (all presets) |

---

## 6. Transcription Processing

### 6.1 Google Speech-to-Text

**Status**: ✅ **Implemented**  
**File**: `run_transcription_pipeline_modular.py`  
**API**: Google Cloud Speech-to-Text

#### Implementation Details
```python
def transcribe_google(audio_path):
    """Google Cloud Speech-to-Text API"""
    from google.cloud import speech
    
    client = speech.SpeechClient()
    
    # Load audio
    with open(audio_path, 'rb') as audio_file:
        audio_content = audio_file.read()
    
    audio = speech.RecognitionAudio(content=audio_content)
    
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code='bn-BD',  # Bengali (Bangladesh)
        enable_automatic_punctuation=True,
        model='default',
        use_enhanced=True  # Enhanced model if available
    )
    
    response = client.recognize(config=config, audio=audio)
    
    # Extract transcript
    transcript = ' '.join([
        result.alternatives[0].transcript 
        for result in response.results
    ])
    
    return transcript
```

#### Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| **Language** | `bn-BD` | Bengali (Bangladesh dialect) |
| **Sample Rate** | 16000 Hz | Required audio sample rate |
| **Encoding** | LINEAR16 | 16-bit PCM audio |
| **Automatic Punctuation** | Enabled | Adds punctuation automatically |
| **Model** | Default | Optimized for Bengali speech |
| **Enhanced Model** | Enabled | Uses enhanced model if available |
| **Max Audio Length** | 60 seconds | Per API call limit |

#### API Requirements
- Google Cloud account with billing enabled
- Speech-to-Text API enabled
- Service account credentials configured
- Environment variable: `GOOGLE_APPLICATION_CREDENTIALS`

---

### 6.2 OpenAI Whisper

**Status**: ✅ **Implemented**  
**File**: `run_transcription_pipeline_modular.py`  
**Library**: openai-whisper

#### Implementation Details
```python
def transcribe_whisper(audio_path, model_size='base'):
    """OpenAI Whisper transcription"""
    import whisper
    
    # Load model
    model = whisper.load_model(model_size)
    
    # Transcribe
    result = model.transcribe(
        audio_path,
        language='bn',  # Bengali
        task='transcribe',  # Not translate
        fp16=False,  # CPU compatible
        verbose=False,
        temperature=0.0,  # Deterministic
        beam_size=5,  # Beam search width
        best_of=5,  # Number of candidates
        patience=1.0  # Beam search patience
    )
    
    return result['text']
```

#### Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| **Model Size** | `base` | 74M parameters (fast, decent quality) |
| **Language** | `bn` | Bengali language code |
| **Task** | `transcribe` | Transcribe (not translate) |
| **FP16** | `False` | Use 32-bit floats (CPU compatible) |
| **Temperature** | 0.0 | Deterministic output (no randomness) |
| **Beam Size** | 5 | Beam search width for decoding |
| **Best Of** | 5 | Number of candidate sequences |
| **Patience** | 1.0 | Beam search patience factor |

#### Model Size Options

| Model | Parameters | Speed | Quality | VRAM | Recommended For |
|-------|------------|-------|---------|------|-----------------|
| **tiny** | 39M | Very Fast | Basic | ~1 GB | Quick testing |
| **base** | 74M | Fast | Good | ~1 GB | ✅ **Current** - Balanced |
| **small** | 244M | Medium | Better | ~2 GB | Higher quality |
| **medium** | 769M | Slow | Great | ~5 GB | Research quality |
| **large** | 1550M | Very Slow | Best | ~10 GB | Maximum quality |

---

### 6.3 Transcription Output Format

#### Directory Structure
```
experiments/experiment_data/<VIDEO_ID>/
├── transcripts_google/
│   ├── chunks/
│   │   ├── <VIDEO_ID>_chunk_001.txt
│   │   ├── <VIDEO_ID>_chunk_002.txt
│   │   ├── <VIDEO_ID>_chunk_003.txt
│   │   └── ...
│   └── <VIDEO_ID>.txt                    # Combined transcript
└── transcripts_whisper/
    ├── chunks/
    │   ├── <VIDEO_ID>_chunk_001.txt
    │   ├── <VIDEO_ID>_chunk_002.txt
    │   └── ...
    └── <VIDEO_ID>.txt                    # Combined transcript
```

#### Individual Chunk Format
```
File: hxhLGCguRO0_chunk_001.txt
Content:
আমি আজকে আপনাদের সাথে শেয়ার করবো...
```

#### Combined Transcript Format
```
File: hxhLGCguRO0.txt
Content:
[Chunk 001] আমি আজকে আপনাদের সাথে শেয়ার করবো...
[Chunk 002] এই বিষয়ে আরো জানতে হলে...
[Chunk 003] আশা করি আপনারা বুঝতে পেরেছেন...
```

---

## 7. Complete Parameters Reference

### 7.1 Audio Processing Pipeline

```yaml
Audio Extraction:
  sample_rate: 16000          # Hz
  channels: 1                 # Mono
  bit_depth: 16               # bits
  format: "WAV"               # Uncompressed
  encoding: "PCM"             # Linear16

Noise Reduction:
  enabled: false              # Optional flag: --reduce-noise
  method: "spectral_gating"   # Frequency-domain filtering
  noise_profile_duration: 1.0 # seconds
  noise_threshold_multiplier: 1.5
  window_type: "hann"         # STFT window
  frame_length: 2048          # samples
  hop_length: 512             # samples

Speech Amplification:
  enabled: false              # Optional flag: --amplify-speech
  method: "rms_normalization" # RMS-based
  target_dBFS: -20.0          # Target loudness
  clipping_prevention: true   # Hard limit at ±1.0
  dynamic_range: "preserved"  # Maintains relative levels

Voice Activity Detection (VAD):
  library: "webrtcvad"        # Google's VAD
  aggressiveness: 3           # 0-3 (most aggressive)
  frame_duration: 30          # ms (10/20/30 supported)
  padding_duration: 300       # ms
  min_speech_duration: 250    # ms
  max_silence_gap: 300        # ms
  sample_rate: 16000          # Hz (required)

Energy-Based Detection:
  method: "librosa_split"     # Short-time energy
  top_db: 40                  # dB below peak
  frame_length: 2048          # samples
  hop_length: 512             # samples
  reference: "peak"           # Peak amplitude
```

### 7.2 Video Processing Pipeline

```yaml
Face Detection:
  algorithm: "haar_cascade"                  # OpenCV classifier
  model: "haarcascade_frontalface_default"   # Pre-trained model
  detection_interval: 5                      # frames
  scale_factor: 1.1                          # Image pyramid scale
  min_neighbors: 5                           # Quality threshold
  min_size: [30, 30]                         # pixels
  min_detection_confidence: 0.5              # 50%
  min_face_frames: 5                         # Minimum frames with faces
  color_space: "grayscale"                   # Convert for detection

Scene Detection:
  algorithm: "content_detector"    # Frame difference
  threshold: 27.0                  # 0-100 sensitivity
  min_scene_length: 15             # frames
  color_space: "HSV"               # HSV difference

Video Export:
  codec: "h264"                    # H.264 compression
  container: "mp4"                 # MP4 container
  audio_codec: "aac"               # AAC audio
  pixel_format: "yuv420p"          # Standard format
  preserve_fps: true               # Keep source FPS
  preserve_resolution: true        # Keep source resolution
```

### 7.3 Chunking Pipeline

```yaml
Chunk Creation:
  min_duration: 2.0              # seconds (CLI: --min-chunk-duration)
  max_duration: 10.0             # seconds
  merge_gap: 0.5                 # seconds
  vad_padding: 0.3               # seconds
  
Chunk Refinement:
  enabled: false                 # Optional flag: --refine-chunks
  scene_alignment_tolerance: 0.5 # seconds
  min_face_coverage: 0.3         # 30% of frames
  boundary_snap: true            # Snap to scene changes
  quality_recheck: true          # Re-verify after adjustment

Face Filtering:
  enabled: false                 # Optional flag: --filter-faces
  min_face_frames: 5             # Minimum frames with faces
  detection_interval: 5          # Check every 5th frame
```

### 7.4 Quality Filtering (SyncNet)

```yaml
SyncNet Processing:
  window_size: 5                      # frames (~200ms at 25fps)
  overlap: 1                          # frame (80% overlap)
  audio_features: "mfcc_13"           # 13 MFCC coefficients
  visual_features: "cnn_embeddings"   # Deep learning features
  correlation_method: "pearson"       # Pearson correlation
  temporal_offset: 5                  # frames (search range)
  max_workers: 8                      # CLI: --max-workers
  
Quality Presets:
  high:
    threshold: 0.75
    description: "Strict filtering, best quality"
    typical_keep_rate: 0.30-0.50
  medium:
    threshold: 0.55
    description: "Balanced quality/quantity"
    typical_keep_rate: 0.50-0.70
  low:
    threshold: 0.35
    description: "Lenient filtering, more data"
    typical_keep_rate: 0.70-0.90
```

### 7.5 Transcription Pipeline

```yaml
Google Speech-to-Text:
  language: "bn-BD"                   # Bengali (Bangladesh)
  sample_rate: 16000                  # Hz
  encoding: "LINEAR16"                # 16-bit PCM
  automatic_punctuation: true         # Auto-add punctuation
  model: "default"                    # Bengali-optimized
  enhanced_model: true                # Use enhanced if available
  max_audio_length: 60                # seconds per call

OpenAI Whisper:
  model_size: "base"                  # tiny/base/small/medium/large
  language: "bn"                      # Bengali
  task: "transcribe"                  # Not translate
  fp16: false                         # Use FP32 (CPU compatible)
  temperature: 0.0                    # Deterministic output
  beam_size: 5                        # Beam search width
  best_of: 5                          # Candidate sequences
  patience: 1.0                       # Beam search patience
  
Output Format:
  encoding: "utf-8"                   # UTF-8 text
  format: "txt"                       # Plain text files
  structure: "per_chunk"              # Individual + combined
```

---

## 8. Processing Flow

### 8.1 Complete Pipeline Flow

```
INPUT: Raw Video (e.g., hxhLGCguRO0.mp4)
│
╔═══════════════════════════════════════════════════════════════╗
║ STEP 1: CHUNK CREATION                                        ║
╚═══════════════════════════════════════════════════════════════╝
│
├─ Extract Audio (16kHz mono WAV)
│  └─ FFmpeg extraction
│
├─ [Optional] Noise Reduction
│  ├─ First 1s as noise profile
│  ├─ Spectral gating (1.5x threshold)
│  └─ STFT-based filtering
│
├─ [Optional] Speech Amplification
│  ├─ Calculate RMS level
│  ├─ Normalize to -20dBFS
│  └─ Clip to prevent distortion
│
├─ Voice Activity Detection
│  ├─ WebRTC VAD (aggressiveness=3)
│  ├─ 30ms frames, 300ms padding
│  └─ Generate speech segments
│
├─ Scene Detection
│  ├─ Content-based (threshold=27.0)
│  └─ Identify visual boundaries
│
├─ [Optional] Face Detection
│  ├─ Haar Cascade every 5 frames
│  ├─ Minimum 5 face frames
│  └─ Filter non-face chunks
│
├─ Segment Processing
│  ├─ Merge segments < 500ms apart
│  ├─ Split segments > 10s long
│  └─ Filter segments < 2s short
│
├─ [Optional] Chunk Refinement
│  ├─ Align with scene changes
│  ├─ Verify face coverage
│  └─ Optimize boundaries
│
└─ Output: outputs/<VIDEO_ID>/chunks/
   ├─ video/*.mp4 (video chunks)
   └─ audio/*.wav (audio chunks)
│
╔═══════════════════════════════════════════════════════════════╗
║ STEP 2: SYNCNET QUALITY FILTERING                            ║
╚═══════════════════════════════════════════════════════════════╝
│
├─ Copy Video Chunks to SyncNet Repo
│  └─ data/<VIDEO_ID>/*.mp4
│
├─ Extract Features
│  ├─ Audio: MFCC-13 coefficients
│  └─ Visual: CNN mouth embeddings
│
├─ Compute Sync Scores
│  ├─ 5-frame windows (80% overlap)
│  ├─ Pearson correlation
│  └─ Score range: 0.0-1.0
│
├─ Apply Preset Threshold
│  ├─ high: 0.75 (strict)
│  ├─ medium: 0.55 (balanced)
│  └─ low: 0.35 (lenient)
│
└─ Output: <SYNCNET_REPO>/results/<VIDEO_ID>/
   ├─ good_quality/*.mp4 (above threshold)
   └─ bad_quality/*.mp4 (below threshold)
│
╔═══════════════════════════════════════════════════════════════╗
║ STEP 3: DIRECTORY ORGANIZATION                               ║
╚═══════════════════════════════════════════════════════════════╝
│
├─ Copy Filtered Chunks
│  └─ From SyncNet results to outputs/
│
├─ Generate Video Variants
│  ├─ video_normal/ (original filtered)
│  ├─ video_bbox/ (with face boxes)
│  └─ video_cropped/ (face region only)
│
├─ Extract Audio Files
│  └─ audio/*.wav (16kHz mono)
│
└─ Output: experiments/experiment_data/<VIDEO_ID>/
   ├─ video_normal/*.mp4
   ├─ video_bbox/*.mp4
   ├─ video_cropped/*.mp4
   └─ audio/*.wav
│
╔═══════════════════════════════════════════════════════════════╗
║ STEP 4: TRANSCRIPTION GENERATION                             ║
╚═══════════════════════════════════════════════════════════════╝
│
├─ Google Speech-to-Text
│  ├─ Bengali (bn-BD) language model
│  ├─ Automatic punctuation
│  └─ Generate transcripts_google/
│
├─ OpenAI Whisper
│  ├─ Base model (74M params)
│  ├─ Bengali (bn) language
│  └─ Generate transcripts_whisper/
│
└─ Output: experiments/experiment_data/<VIDEO_ID>/
   ├─ transcripts_google/
   │  ├─ chunks/*.txt (per chunk)
   │  └─ <VIDEO_ID>.txt (combined)
   └─ transcripts_whisper/
      ├─ chunks/*.txt (per chunk)
      └─ <VIDEO_ID>.txt (combined)
│
▼
FINAL OUTPUT: Complete Multimodal Dataset
├─ Synchronized audio-visual chunks
├─ Multiple video variants (normal, bbox, cropped)
├─ Quality-filtered content (SyncNet verified)
└─ Dual-source transcriptions (Google + Whisper)
```

### 8.2 Data Flow Summary

| Stage | Input | Process | Output | Quality Check |
|-------|-------|---------|--------|---------------|
| **1. Chunk Creation** | Raw video | VAD + face detection + scene analysis | Video/audio chunks | Face presence, duration |
| **2. SyncNet Filtering** | Video chunks | Audio-visual sync analysis | Good/bad quality chunks | Sync score vs threshold |
| **3. Organization** | Filtered chunks | Variant generation + structuring | Organized dataset | Directory structure |
| **4. Transcription** | Organized chunks | Google API + Whisper | Bengali transcripts | Dual-source validation |

### 8.3 Quality Gates

Each step includes validation checkpoints:

```
Step 1 ✓ Validation:
  ├─ Chunk count > 0
  ├─ Duration within [2s, 10s]
  ├─ [If enabled] Face frames ≥ 5
  └─ Audio quality sufficient

Step 2 ✓ Validation:
  ├─ Good quality folder exists
  ├─ At least some chunks pass threshold
  └─ Sync scores calculated successfully

Step 3 ✓ Validation:
  ├─ All directories created
  ├─ Video variants generated
  └─ File counts match

Step 4 ✓ Validation:
  ├─ Transcript files created
  ├─ UTF-8 encoding correct
  └─ Both Google and Whisper completed
```

---

## 9. Command-Line Interface

### 9.1 Complete Pipeline Script

```bash
./complete_pipeline.sh <video_id> --syncnet-repo <path> [options]
```

#### Required Arguments
- `<video_id>`: YouTube video ID (e.g., `hxhLGCguRO0`)
- `--syncnet-repo <path>`: Path to SyncNet Python repository

#### Optional Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--current-repo` | path | `.` | Path to current repository |
| `--max-workers` | int | `8` | Number of parallel workers |
| `--min-chunk-duration` | float | `2.0` | Minimum chunk duration (seconds) |
| `--preset` | string | `high` | SyncNet quality preset (high/medium/low) |
| `--skip-step1` | flag | - | Skip chunk creation |
| `--skip-step2` | flag | - | Skip SyncNet filtering |
| `--skip-step3` | flag | - | Skip directory organization |
| `--skip-step4` | flag | - | Skip transcription |
| `--help` | flag | - | Show help message |

#### Usage Examples

**Basic usage:**
```bash
./complete_pipeline.sh hxhLGCguRO0 \
  --syncnet-repo "/path/to/syncnet_python"
```

**With custom parameters:**
```bash
./complete_pipeline.sh hxhLGCguRO0 \
  --syncnet-repo "/path/to/syncnet_python" \
  --max-workers 16 \
  --min-chunk-duration 1.5 \
  --preset medium
```

**Resume from specific step:**
```bash
./complete_pipeline.sh hxhLGCguRO0 \
  --syncnet-repo "/path/to/syncnet_python" \
  --skip-step1 \
  --skip-step2
```

**Mac example:**
```bash
./complete_pipeline.sh efhkN7e8238 \
  --syncnet-repo "/Users/darklord/Research/Audio Visual/Code/syncnet_python" \
  --preset high \
  --max-workers 8
```

**WSL example:**
```bash
./complete_pipeline.sh efhkN7e8238 \
  --syncnet-repo "/home/user/syncnet_python" \
  --current-repo "/home/user/bengali-dataset" \
  --preset medium \
  --max-workers 4
```

---

## 10. Performance Considerations

### 10.1 Processing Time Estimates

| Stage | Duration | Bottleneck | Parallelizable |
|-------|----------|------------|----------------|
| **Audio Extraction** | ~10-30s | I/O | No |
| **VAD Detection** | ~30-60s | CPU | Partially |
| **Face Detection** | ~1-3 min | CPU | Yes (per chunk) |
| **SyncNet Filtering** | ~5-15 min | GPU/CPU | Yes (max_workers) |
| **Directory Org** | ~1-2 min | I/O | Yes (max_workers) |
| **Transcription** | ~10-30 min | API/Model | Batch processing |

**Total estimated time for 10-minute video**: 20-50 minutes

### 10.2 Resource Requirements

#### Minimum Requirements
- **CPU**: 4 cores
- **RAM**: 8 GB
- **Disk**: 5 GB per video
- **GPU**: Optional (speeds up SyncNet/Whisper)

#### Recommended Requirements
- **CPU**: 8+ cores
- **RAM**: 16 GB
- **Disk**: 10 GB per video
- **GPU**: 6+ GB VRAM (for Whisper medium/large)

### 10.3 Optimization Tips

1. **Increase max-workers** for parallel processing (CPU-bound tasks)
2. **Use lower SyncNet preset** if quality allows (speeds up filtering)
3. **Disable optional features** (noise reduction, amplification, face filtering)
4. **Use smaller Whisper model** (tiny/base instead of medium/large)
5. **Process multiple videos in parallel** (separate terminal sessions)
6. **Use GPU acceleration** when available (PyTorch CUDA)

---

## 11. Troubleshooting

### 11.1 Common Issues

#### Issue: Too Many Chunks Filtered Out

**Symptoms**: SyncNet removes most/all chunks

**Solutions**:
- Lower SyncNet preset: `--preset medium` or `--preset low`
- Check input video quality (poor audio/video sync in source)
- Verify face detection is working (enable `--filter-faces` earlier)
- Review bad_quality chunks manually

#### Issue: Chunks Too Short/Long

**Symptoms**: Duration outside desired range

**Solutions**:
- Adjust `--min-chunk-duration` parameter
- Modify `max_chunk_duration` in code (default 10s)
- Check VAD aggressiveness (may need tuning)
- Review merge_gap parameter (default 0.5s)

#### Issue: No Faces Detected

**Symptoms**: All chunks rejected by face filtering

**Solutions**:
- Lower `min_face_frames` parameter (default 5)
- Reduce `min_neighbors` in Haar Cascade (default 5)
- Check video quality and face visibility
- Disable face filtering if not needed

#### Issue: Transcription Errors

**Symptoms**: Empty or incorrect transcripts

**Solutions**:
- Verify Google Cloud credentials configured
- Check audio quality (16kHz, mono, clear speech)
- Try different Whisper model size
- Ensure Bengali language specified correctly

---

## 12. Future Improvements

### Potential Enhancements
- [ ] Deep learning-based VAD (more accurate than WebRTC)
- [ ] Advanced face detection (MTCNN, RetinaFace, MediaPipe)
- [ ] Speaker diarization (multiple speakers per chunk)
- [ ] Emotion detection from speech/face
- [ ] Real-time processing pipeline
- [ ] Web interface for parameter tuning
- [ ] Automatic quality assessment (beyond SyncNet)
- [ ] Support for multi-language videos

---

## References

### Libraries & Tools
- **OpenCV**: https://opencv.org/
- **librosa**: https://librosa.org/
- **WebRTC VAD**: https://github.com/wiseman/py-webrtcvad
- **PySceneDetect**: https://scenedetect.com/
- **SyncNet**: https://github.com/joonson/syncnet_python
- **OpenAI Whisper**: https://github.com/openai/whisper
- **Google Speech-to-Text**: https://cloud.google.com/speech-to-text

### Research Papers
- SyncNet: "Out of time: automated lip sync in the wild" (Chung & Zisserman, 2016)
- Whisper: "Robust Speech Recognition via Large-Scale Weak Supervision" (Radford et al., 2022)

---

**Document Version**: 1.0  
**Last Updated**: October 10, 2025  
**Maintained By**: Research Team  
**Repository**: bengali-speech-audio-visual-dataset
