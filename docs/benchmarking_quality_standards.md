# Benchmarking Dataset Quality Standards

## Purpose

This document defines the quality standards for the Bengali Audio-Visual Speech Recognition Benchmarking Dataset. As a benchmarking dataset, we enforce **stricter quality requirements** than typical training datasets to ensure:

1. **Reproducibility**: Consistent evaluation across different models
2. **Reliability**: High-quality ground truth data
3. **Fairness**: No ambiguous or poor-quality samples
4. **Credibility**: Dataset quality meets publication standards

## Quality Requirements

### 1. Face Presence: 95% Minimum ⭐

**Requirement**: Each chunk must have a clearly detectable face in **at least 95%** of sampled frames.

**Rationale**:
- Benchmarking requires consistent audio-visual alignment
- Missing faces = poor synchronization quality
- 5% tolerance accounts for:
  - Natural blinks (150-200ms)
  - Quick head movements
  - Face detector limitations

**Implementation**:
```python
min_face_percentage = 0.95  # 95% face presence required
```

**Rejection Example**:
```
Chunk: 0-5s with 90% face presence
Result: ❌ REJECTED (below 95% threshold)
Reason: Not suitable for benchmarking
```

### 2. Gap Tolerance: 100ms Maximum

**Requirement**: Chunks can only tolerate gaps (no face detected) up to **100ms**.

**Rationale**:
- 100ms = natural blink duration
- Longer gaps = scene changes or non-face content
- For benchmarking, we prioritize quality over quantity

**Implementation**:
```python
max_face_gap = 0.1  # Split at gaps > 100ms
```

**Split Example**:
```
Timeline: [Face: 0-3s] [No face: 3-3.5s] [Face: 3.5-6s]
          └─ Gap is 500ms (> 100ms threshold)
          
Result: Split into 2 chunks
  Chunk 1: 0-3s (continuous face)
  Chunk 2: 3.5-6s (continuous face)
```

### 3. Sampling Rate: 30ms (33 FPS)

**Requirement**: Check for face presence every **30ms** (approximately 33 frames per second).

**Rationale**:
- Most videos are 24-30 FPS
- 30ms sampling captures every frame
- Ensures no gaps are missed

**Implementation**:
```python
refine_sample_rate = 0.03  # Check every 30ms
```

### 4. Minimum Chunk Duration: 1 Second

**Requirement**: Final chunks must be at least **1 second** long.

**Rationale**:
- Too short = not enough context for evaluation
- 1 second ≈ 1-2 words in Bengali
- Sufficient for audio-visual sync assessment

**Implementation**:
```python
min_chunk_duration = 1.0  # 1 second minimum
```

### 5. Sentence Boundary Alignment

**Requirement**: Chunks should align with sentence boundaries (700ms silence threshold).

**Rationale**:
- Complete semantic units
- Natural speech patterns
- Better transcription quality

**Implementation**:
```python
min_silence_len = 700  # 700ms for sentence pauses
```

## Processing Pipeline for Benchmarking

### Step 1: Sentence-Level Splitting
```
Input: Full video
↓
Split by silence (700ms threshold)
↓
Result: Sentence-level chunks
```

### Step 2: Initial Face Filtering
```
Input: Sentence-level chunks
↓
Check: Do chunks have ANY faces? (30% threshold)
↓
Remove: Completely faceless chunks
```

### Step 3: Strict Face Refinement ⭐
```
Input: Chunks with some faces
↓
Sample every 30ms for face detection
↓
Split at any gap > 100ms
↓
Validate: Each segment has ≥95% face presence
↓
Remove: Segments below 95% threshold
```

### Step 4: Duration Validation
```
Input: Face-validated segments
↓
Filter: Keep only segments ≥1 second
↓
Result: High-quality benchmarking chunks
```

## Quality vs. Quantity Trade-off

### Expected Impact

**Typical News Video** (10 minutes):
- **Lenient settings** (training dataset):
  - ~80-100 chunks
  - ~8-9 minutes of data
  - Face presence: 60-90%

- **Strict settings** (benchmarking dataset): ⭐
  - ~50-70 chunks
  - ~5-7 minutes of data  
  - Face presence: 95-100%

**Trade-off**:
- ❌ **50% less data** (fewer chunks)
- ✅ **200% higher quality** (95%+ face presence)
- ✅ **Suitable for publication** and research benchmarking

### Why This is Acceptable

For a **benchmarking dataset**:
1. **Quality > Quantity**: Better to have fewer, perfect samples
2. **Credibility**: Published datasets need high standards
3. **Reproducibility**: Consistent quality = reliable evaluation
4. **Fair Comparison**: All models tested on same quality data

For a **training dataset** (future work):
- Can use lenient settings (max_gap=0.3s, 80% face presence)
- Prioritize quantity over perfection
- Models learn from diverse examples

## Parameter Summary

### Benchmarking Dataset (Current)

```python
# In utils/split_by_silence.py
split_into_chunks(
    min_silence_len=700,        # Sentence boundaries
    refine_sample_rate=0.03,    # Check every 30ms ⭐ STRICT
    max_face_gap=0.1,           # Split at 100ms gaps ⭐ STRICT
    min_chunk_duration=1.0      # Minimum 1 second
)

# In utils/refine_chunks.py
min_face_percentage=0.95        # 95% face presence ⭐ STRICT
```

### Training Dataset (Future Alternative)

```python
# More lenient for training
split_into_chunks(
    min_silence_len=500,        # Shorter pauses OK
    refine_sample_rate=0.1,     # Check every 100ms
    max_face_gap=0.3,           # Tolerate 300ms gaps
    min_chunk_duration=0.5      # Minimum 0.5 second
)

min_face_percentage=0.80        # 80% face presence
```

## Quality Assurance Checklist

Before finalizing the dataset:

- [ ] **Face Presence**: All chunks have ≥95% face detection rate
- [ ] **Gap Analysis**: No gaps >100ms within chunks
- [ ] **Duration**: All chunks ≥1 second
- [ ] **Sentence Alignment**: Chunks align with speech pauses
- [ ] **Audio Quality**: Clear speech, no background noise dominance
- [ ] **Video Quality**: No blurry frames, proper lighting
- [ ] **Transcription**: Accurate Bengali transcription
- [ ] **Metadata**: Complete metadata for each chunk

## Validation Scripts

### Check Face Presence Percentage

```python
# validate_chunks.py
import cv2
from utils.face_detection import detect_faces_in_frame

def validate_chunk_quality(video_path):
    """Validate face presence in a chunk."""
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    total_frames = 0
    faces_detected = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        faces = detect_faces_in_frame(frame)
        if len(faces) > 0:
            faces_detected += 1
        total_frames += 1
    
    cap.release()
    
    face_percentage = faces_detected / total_frames if total_frames > 0 else 0
    
    print(f"Video: {video_path}")
    print(f"Total frames: {total_frames}")
    print(f"Faces detected: {faces_detected}")
    print(f"Face presence: {face_percentage*100:.2f}%")
    print(f"Status: {'✅ PASS' if face_percentage >= 0.95 else '❌ FAIL'}")
    
    return face_percentage >= 0.95

# Validate all chunks
import glob
chunks = glob.glob("outputs/*/chunks/video/*.mp4")
failed = []

for chunk in chunks:
    if not validate_chunk_quality(chunk):
        failed.append(chunk)

print(f"\n{'='*60}")
print(f"Total chunks: {len(chunks)}")
print(f"Passed: {len(chunks) - len(failed)}")
print(f"Failed: {len(failed)}")

if failed:
    print("\nFailed chunks:")
    for chunk in failed:
        print(f"  - {chunk}")
```

### Analyze Dataset Statistics

```python
# analyze_dataset.py
import json
import glob

def analyze_dataset():
    """Analyze overall dataset statistics."""
    
    processed = json.load(open("outputs/processed.json"))
    
    total_chunks = 0
    total_duration = 0
    chunk_durations = []
    
    for video_id, data in processed.items():
        chunks = data.get("chunks", 0)
        timestamps = data.get("timestamps", [])
        
        total_chunks += chunks
        
        for start, end in timestamps:
            duration = end - start
            total_duration += duration
            chunk_durations.append(duration)
    
    print("=== Bengali Audio-Visual Benchmarking Dataset ===")
    print(f"\nTotal videos: {len(processed)}")
    print(f"Total chunks: {total_chunks}")
    print(f"Total duration: {total_duration/60:.1f} minutes")
    print(f"\nChunk Statistics:")
    print(f"  Average duration: {sum(chunk_durations)/len(chunk_durations):.2f}s")
    print(f"  Shortest chunk: {min(chunk_durations):.2f}s")
    print(f"  Longest chunk: {max(chunk_durations):.2f}s")
    print(f"  Median duration: {sorted(chunk_durations)[len(chunk_durations)//2]:.2f}s")
    
    # Duration distribution
    short = sum(1 for d in chunk_durations if d < 2)
    medium = sum(1 for d in chunk_durations if 2 <= d < 5)
    long = sum(1 for d in chunk_durations if d >= 5)
    
    print(f"\nDuration Distribution:")
    print(f"  <2s:  {short:4d} ({short/total_chunks*100:.1f}%)")
    print(f"  2-5s: {medium:4d} ({medium/total_chunks*100:.1f}%)")
    print(f"  ≥5s:  {long:4d} ({long/total_chunks*100:.1f}%)")

analyze_dataset()
```

## Dataset Publication Checklist

When preparing the dataset for publication:

### Documentation Required
- [ ] Dataset paper/technical report
- [ ] README with usage instructions
- [ ] Quality standards documentation (this document)
- [ ] License information (e.g., CC BY-SA 4.0)
- [ ] Citation information

### Files to Include
- [ ] All video chunks (.mp4)
- [ ] All audio chunks (.wav)
- [ ] Transcriptions (.txt or .json)
- [ ] Metadata file (processed.json)
- [ ] Train/validation/test splits
- [ ] Baseline evaluation results

### Quality Verification
- [ ] All chunks validated (≥95% face presence)
- [ ] Transcriptions reviewed by native speakers
- [ ] Audio quality verified (no corruption)
- [ ] Video quality verified (no artifacts)
- [ ] Metadata completeness checked

### Repository Structure
```
bengali-avsr-benchmark/
├── README.md
├── LICENSE
├── CITATION.bib
├── metadata/
│   ├── processed.json
│   ├── train_split.json
│   ├── val_split.json
│   └── test_split.json
├── data/
│   ├── video_chunks/
│   ├── audio_chunks/
│   └── transcriptions/
├── docs/
│   ├── quality_standards.md
│   ├── preprocessing_pipeline.md
│   └── baseline_results.md
└── scripts/
    ├── validate_dataset.py
    ├── analyze_statistics.py
    └── evaluation_baseline.py
```

## References

- **Related**: `docs/sentence_boundary_fix.md` - Sentence-level splitting
- **Related**: `docs/strict_face_continuity.md` - Face continuity requirements
- **Related**: `docs/processing_parameters.md` - Complete parameter reference

## Contact & Issues

For questions about dataset quality standards:
- Open an issue on GitHub
- Consult the documentation in `docs/`
- Refer to the processing pipeline logs

---

**Standard**: Benchmarking Dataset Quality Requirements  
**Version**: 1.0  
**Date**: 2025-10-11  
**Status**: ✅ Active - Applied to all processing
