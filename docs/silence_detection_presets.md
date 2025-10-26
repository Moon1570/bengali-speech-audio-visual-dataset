# Silence Detection Presets Guide

This document explains the silence detection preset system for controlling how videos are split into chunks.

## Overview

The silence detection system analyzes audio to find natural breaks (silence) where the video can be split. The sensitivity of this detection can be adjusted using presets or custom parameters.

## Available Presets

### 1. `very_sensitive` - Word-Level Splitting
**Best for:** Dense speech with minimal pauses
- **Min Silence Length:** 400ms
- **Silence Threshold:** -16 dB offset from audio level
- **Max Chunk Length:** 15 seconds
- **Result:** Creates many small chunks, splitting at short pauses
- **Use case:** Videos with continuous speech where you need very fine-grained segmentation

**Example:**
```bash
python run_pipeline.py video.mp4 --silence-preset very_sensitive
```

### 2. `sensitive` - Phrase-Level Splitting
**Best for:** Speech with short natural pauses
- **Min Silence Length:** 500ms
- **Silence Threshold:** -18 dB offset from audio level
- **Max Chunk Length:** 18 seconds
- **Result:** Splits at phrase boundaries, more chunks than balanced
- **Use case:** Fast-paced speech or when you need smaller chunks

**Example:**
```bash
./complete_pipeline.sh VIDEO_ID --syncnet-repo /path/to/syncnet --silence-preset sensitive
```

### 3. `balanced` - Sentence-Level Splitting (DEFAULT)
**Best for:** Most general use cases
- **Min Silence Length:** 700ms
- **Silence Threshold:** -20 dB offset from audio level
- **Max Chunk Length:** 20 seconds
- **Result:** Natural sentence-level boundaries
- **Use case:** Standard benchmarking datasets, balanced chunk sizes

**Example:**
```bash
python run_pipeline.py video.mp4 --silence-preset balanced
```

### 4. `conservative` - Paragraph-Level Splitting
**Best for:** Long-form speech with clear sections
- **Min Silence Length:** 900ms
- **Silence Threshold:** -22 dB offset from audio level
- **Max Chunk Length:** 25 seconds
- **Result:** Fewer, longer chunks at major pause points
- **Use case:** Lectures, presentations, narrative speech

**Example:**
```bash
./complete_pipeline.sh VIDEO_ID --syncnet-repo /path/to/syncnet --silence-preset conservative
```

### 5. `very_conservative` - Topic-Level Splitting
**Best for:** Very long pauses between major sections
- **Min Silence Length:** 1200ms
- **Silence Threshold:** -25 dB offset from audio level
- **Max Chunk Length:** 30 seconds
- **Result:** Very few large chunks, only major topic changes
- **Use case:** Interviews, panel discussions, multi-topic videos

**Example:**
```bash
python run_pipeline.py video.mp4 --silence-preset very_conservative
```

## Custom Parameters

You can override preset values with custom parameters:

### Custom Silence Threshold
Specify the exact dBFS threshold for detecting silence:

```bash
python run_pipeline.py video.mp4 --custom-silence-thresh -35.0
```

**Guidelines:**
- More negative values (e.g., -40 dB) = less sensitive = fewer chunks
- Less negative values (e.g., -30 dB) = more sensitive = more chunks
- Typical range: -50 to -20 dBFS

### Custom Minimum Silence Length
Specify the minimum duration of silence in milliseconds:

```bash
python run_pipeline.py video.mp4 --custom-min-silence 600
```

**Guidelines:**
- Shorter values (300-500ms) = more splits = more chunks
- Longer values (800-1500ms) = fewer splits = fewer chunks
- Typical range: 300-2000ms

### Combining Custom Parameters

```bash
# Very fine-grained splitting
python run_pipeline.py video.mp4 \
  --custom-silence-thresh -30.0 \
  --custom-min-silence 300

# Very coarse splitting
python run_pipeline.py video.mp4 \
  --custom-silence-thresh -45.0 \
  --custom-min-silence 1500
```

## Using with Complete Pipeline

```bash
# Sensitive preset
./complete_pipeline.sh VIDEO_ID \
  --syncnet-repo /path/to/syncnet \
  --silence-preset sensitive \
  --transcription-model google

# Custom parameters
./complete_pipeline.sh VIDEO_ID \
  --syncnet-repo /path/to/syncnet \
  --custom-silence-thresh -35.0 \
  --custom-min-silence 500 \
  --transcription-model google
```

## Choosing the Right Preset

| Video Type | Recommended Preset | Reason |
|------------|-------------------|---------|
| Fast-paced news | `sensitive` | Short pauses between sentences |
| Lectures/Presentations | `balanced` or `conservative` | Natural sentence/paragraph breaks |
| Interviews | `conservative` | Longer pauses between speakers |
| Continuous monologue | `balanced` | Standard sentence boundaries |
| Multi-topic discussion | `very_conservative` | Major topic transitions |
| Dense technical speech | `very_sensitive` | Need fine-grained segmentation |

## Troubleshooting

### Problem: Too many chunks (video is over-segmented)
**Solution:** Use a less sensitive preset or increase min silence length
```bash
# Try conservative preset
--silence-preset conservative

# Or increase min silence length
--custom-min-silence 1000
```

### Problem: Not splitting enough (long chunks)
**Solution:** Use a more sensitive preset or decrease threshold
```bash
# Try sensitive preset
--silence-preset sensitive

# Or make threshold more sensitive
--custom-silence-thresh -30.0
--custom-min-silence 400
```

### Problem: Splitting mid-sentence
**Solution:** Increase minimum silence length
```bash
--custom-min-silence 800  # Require longer pauses
```

### Problem: Missing natural break points
**Solution:** Make detection more sensitive
```bash
--silence-preset sensitive
# or
--custom-silence-thresh -35.0
```

## Technical Details

### How It Works

1. **Dynamic Threshold Calculation**: The system analyzes the audio to determine a baseline silence level using the 5th percentile of RMS values.

2. **Preset Offset**: Each preset defines an offset from the audio's dBFS level:
   ```
   silence_threshold = max(dynamic_threshold, audio_dBFS + preset_offset)
   ```

3. **Silence Detection**: Audio segments quieter than the threshold for longer than `min_silence_len` are considered silence.

4. **Chunk Creation**: The audio/video is split at these silence points, keeping some silence padding for natural transitions.

5. **Max Length Enforcement**: If a chunk exceeds `max_chunk_len`, it's further split regardless of silence.

### Understanding dBFS

- **dBFS** (Decibels relative to Full Scale) measures audio level
- **0 dBFS** = Maximum possible level (clipping)
- **-∞ dBFS** = Complete silence
- Typical speech audio: -10 to -30 dBFS
- Background silence: -40 to -60 dBFS

### Offset Values

- **-16 dB**: Very sensitive, catches brief pauses
- **-18 dB**: Sensitive, phrase-level pauses
- **-20 dB**: Balanced, sentence-level pauses (default)
- **-22 dB**: Conservative, paragraph-level pauses
- **-25 dB**: Very conservative, major pauses only

## Best Practices

1. **Start with `balanced`**: Works well for most cases
2. **Test on a sample**: Try different presets on a short video first
3. **Check chunk distribution**: Aim for 5-15 second chunks for most applications
4. **Consider benchmarking needs**: For datasets, consistency matters more than perfection
5. **Use face filtering**: Combine with `--filter-faces` and `--refine-chunks` for best quality

## Examples by Use Case

### Academic Research Dataset
```bash
./complete_pipeline.sh VIDEO_ID \
  --syncnet-repo /path/to/syncnet \
  --silence-preset balanced \
  --transcription-model google
```

### High-Quality Benchmarking
```bash
./complete_pipeline.sh VIDEO_ID \
  --syncnet-repo /path/to/syncnet \
  --silence-preset balanced \
  --filter-faces \
  --refine-chunks \
  --transcription-model google
```

### Quick Processing (More Chunks)
```bash
./complete_pipeline.sh VIDEO_ID \
  --syncnet-repo /path/to/syncnet \
  --silence-preset sensitive \
  --transcription-model google
```

### Long-Form Content
```bash
./complete_pipeline.sh VIDEO_ID \
  --syncnet-repo /path/to/syncnet \
  --silence-preset conservative \
  --transcription-model google
```

## See Also

- [Benchmarking Quality Standards](benchmarking_quality_standards.md)
- [Pipeline README](../PIPELINE_README.md)
- [Sentence Boundary Fix](sentence_boundary_fix.md)
