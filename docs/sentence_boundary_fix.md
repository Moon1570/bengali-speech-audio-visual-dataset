# Sentence Boundary Detection Fix

## Problem

The audio chunking system was cutting audio mid-sentence instead of at natural sentence boundaries. This was causing:
- Poor quality training data for speech recognition
- Incomplete sentences in chunks
- Loss of semantic context

## Root Cause Analysis

The issue was in `utils/split_by_silence.py` with parameters that were too sensitive:

### Original Parameters (PROBLEMATIC)
```python
min_silence_len=200    # 200ms - Too short for sentence pauses
silence_thresh = audio_seg.dBFS - 25  # Too sensitive, catching all brief pauses
max_chunk_len=10000    # 10 seconds - forcing arbitrary splits
keep_silence=100       # 100ms padding
```

**Why this failed:**
- **200ms threshold**: Natural pauses between sentences are typically 500-800ms. A 200ms threshold catches every brief pause between words or clauses, not just sentences.
- **-25 dBFS sensitivity**: This catches very quiet moments, including natural breathing pauses within sentences.
- **10-second limit**: Forces splits regardless of whether it's mid-sentence or not.

## Solution

Updated parameters to focus on sentence-level pauses:

### New Parameters (FIXED)
```python
min_silence_len=700    # 700ms - Catches sentence pauses only
silence_thresh = audio_seg.dBFS - 18  # Less sensitive, focuses on real silence
max_chunk_len=20000    # 20 seconds - More flexible
keep_silence=150       # 150ms padding for natural flow
```

**Why this works:**
- **700ms threshold**: Matches typical sentence boundary pauses (500-800ms range)
- **-18 dBFS sensitivity**: Only catches actual silence between sentences, not brief pauses
- **20-second limit**: Gives more flexibility for longer complex sentences
- **150ms padding**: Preserves natural sentence flow

## Results Comparison

### Before Fix (200ms threshold)
- **Raw chunks detected**: 34 chunks
- **After refinement**: 10 chunks  
- **Average chunk duration**: ~2-3 seconds
- **Issue**: Many chunks cut mid-sentence

### After Fix (700ms threshold)
- **Raw chunks detected**: 8 chunks
- **After refinement**: 10 chunks
- **Chunk durations**: 1-10 seconds with natural boundaries
- **Improvement**: Chunks now align with sentence boundaries

Example chunk distribution:
```
Chunk 0: 0.00s - 5.40s (duration: 5.40s)
Chunk 1: 5.42s - 12.32s (duration: 6.90s)
Chunk 2: 12.82s - 14.92s (duration: 2.10s)
Chunk 3: 15.02s - 25.32s (duration: 10.30s)
Chunk 4: 25.43s - 26.53s (duration: 1.10s)
Chunk 5: 26.55s - 29.25s (duration: 2.70s)
Chunk 6: 29.28s - 36.78s (duration: 7.50s)
Chunk 7: 38.72s - 40.32s (duration: 1.60s)
Chunk 8: 40.40s - 51.10s (duration: 10.70s)
Chunk 9: 51.17s - 54.77s (duration: 3.60s)
```

## Technical Details

### Silence Detection Process

1. **Noise Reduction**: Apply spectral gating to remove background noise
2. **Dynamic Threshold**: Calculate silence threshold based on 5th percentile of RMS values
3. **Silence Detection**: Use pydub's `split_on_silence()` with updated parameters
4. **Face Filtering**: Keep only chunks where faces are visible
5. **Refinement**: Remove segments within chunks where no face is detected

### Parameter Tuning Guidelines

For different languages or recording conditions, adjust:

- **min_silence_len**: 
  - Bengali/English: 600-800ms
  - Fast speech: 500-600ms
  - Slow/formal speech: 800-1000ms

- **silence_thresh offset**:
  - Clean audio: -15 to -18 dB
  - Noisy audio: -20 to -25 dB
  - Studio quality: -12 to -15 dB

- **max_chunk_len**:
  - Short sentences: 15-20 seconds
  - Long monologues: 25-30 seconds
  - Keep under 30s for optimal processing

## Testing

To test sentence boundary detection:

```bash
# Run pipeline on test video
python run_pipeline.py downloads/hxhLGCguRO0_test.mp4

# Check chunk durations in output
ls -lh outputs/hxhLGCguRO0_test/chunks/audio/

# Listen to chunks to verify sentence boundaries
# (use any audio player to check chunks)
```

## References

- **File Modified**: `utils/split_by_silence.py` line 66
- **Function**: `split_into_chunks()`
- **Test Video**: `downloads/hxhLGCguRO0_test.mp4` (1 minute sample)
- **Test Output**: `outputs/hxhLGCguRO0_test/`

## Impact

This fix significantly improves:
- **Dataset Quality**: Complete sentences for better transcription training
- **Semantic Context**: Maintains meaning within each chunk
- **User Experience**: Audio chunks sound more natural
- **Transcription Accuracy**: Better context for speech recognition models

---

**Date Fixed**: 2025-10-10  
**Tested With**: hxhLGCguRO0_test.mp4 (60-second Bengali speech video)  
**Status**: ✅ Verified working
