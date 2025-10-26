# Silence Detection Preset System - Implementation Summary

## Overview
Added a comprehensive preset system for silence detection sensitivity, allowing users to control how videos are split into chunks with predefined presets or custom parameters.

## Changes Made

### 1. Core Implementation (`utils/split_by_silence.py`)

**New Function: `get_silence_preset(preset_name)`**
- Returns configuration dictionary for 5 predefined presets
- Handles invalid preset names gracefully (defaults to 'balanced')

**Updated Function: `split_into_chunks()`**
- Added parameters:
  - `silence_preset` (default: 'balanced')
  - `custom_silence_thresh` (optional override)
  - `custom_min_silence_len` (optional override)
- Maintains backward compatibility with deprecated `min_silence_len` parameter
- Improved logging to show all silence detection settings

**Presets Available:**
1. **very_sensitive**: 400ms silence, -16dB offset → Many short chunks (word-level)
2. **sensitive**: 500ms silence, -18dB offset → Phrase-level splitting
3. **balanced** (default): 700ms silence, -20dB offset → Sentence-level boundaries
4. **conservative**: 900ms silence, -22dB offset → Paragraph-level chunks
5. **very_conservative**: 1200ms silence, -25dB offset → Topic-level boundaries

### 2. CLI Integration (`run_pipeline.py`)

**New Arguments:**
```bash
--silence-preset {very_sensitive,sensitive,balanced,conservative,very_conservative}
    Silence detection sensitivity preset (default: balanced)

--custom-silence-thresh FLOAT
    Custom silence threshold in dBFS (e.g., -40.0)
    Overrides preset threshold

--custom-min-silence INT
    Custom minimum silence length in milliseconds (e.g., 500)
    Overrides preset value
```

**Updated `split_into_chunks()` call** to pass new parameters

### 3. Pipeline Integration (`complete_pipeline.sh`)

**New Shell Variables:**
- `SILENCE_PRESET` (default: "balanced")
- `CUSTOM_SILENCE_THRESH` (optional)
- `CUSTOM_MIN_SILENCE` (optional)

**New Command-Line Options:**
- `--silence-preset PRESET`
- `--custom-silence-thresh NUM`
- `--custom-min-silence NUM`

**Updated:**
- Argument parsing to handle new options
- Validation for preset values and custom parameters
- Status display to show silence detection settings
- Step 1 command building to pass parameters to run_pipeline.py
- Usage examples with new options

### 4. Documentation

**Created:**
- `docs/SILENCE_PRESETS_QUICK_REF.md` - Quick reference guide
- `docs/silence_detection_presets.md` - Comprehensive documentation

**Updated:**
- `PIPELINE_README.md` - Added silence detection options and examples

**Test Script:**
- `test_silence_presets.py` - Automated testing of preset system

## Usage Examples

### Basic Preset Usage
```bash
# Use default (balanced - sentence-level)
./complete_pipeline.sh SSYouTubeonline --syncnet-repo /path/to/syncnet

# More sensitive (more chunks)
./complete_pipeline.sh SSYouTubeonline --syncnet-repo /path/to/syncnet \
  --silence-preset sensitive

# More conservative (fewer chunks)
./complete_pipeline.sh SSYouTubeonline --syncnet-repo /path/to/syncnet \
  --silence-preset conservative
```

### Custom Parameters
```bash
# Custom threshold only
./complete_pipeline.sh SSYouTubeonline --syncnet-repo /path/to/syncnet \
  --custom-silence-thresh -35.0

# Custom minimum silence only
./complete_pipeline.sh SSYouTubeonline --syncnet-repo /path/to/syncnet \
  --custom-min-silence 600

# Combine preset with custom overrides
./complete_pipeline.sh SSYouTubeonline --syncnet-repo /path/to/syncnet \
  --silence-preset balanced \
  --custom-silence-thresh -30.0
```

### Direct Python Usage
```bash
.venv/bin/python run_pipeline.py downloads/video.mp4 --silence-preset sensitive

.venv/bin/python run_pipeline.py downloads/video.mp4 \
  --silence-preset balanced \
  --custom-silence-thresh -35.0 \
  --custom-min-silence 800
```

## Testing

Run the test suite to verify preset functionality:
```bash
.venv/bin/python test_silence_presets.py
```

Expected output:
- ✅ All 5 presets load successfully
- ✅ All required parameters present
- ✅ Parameters within expected ranges
- ✅ Invalid preset defaults to 'balanced'
- ✅ Preset ordering verified (sensitivity progression)

## Troubleshooting Guide

### Problem: Too many chunks
**Solution:** Use more conservative preset
```bash
--silence-preset conservative
# or
--silence-preset very_conservative
```

### Problem: Too few chunks / not splitting
**Solution:** Use more sensitive preset
```bash
--silence-preset sensitive
# or
--silence-preset very_sensitive
```

### Problem: Chunks split mid-sentence
**Solution:** Increase minimum silence length
```bash
--custom-min-silence 900
```

### Problem: No silence detected at all
**Solution:** Make detection more sensitive
```bash
--silence-preset very_sensitive --custom-silence-thresh -25.0
```

## Backward Compatibility

- Old `min_silence_len` parameter still supported (deprecated)
- Default behavior unchanged (uses 'balanced' preset)
- Existing scripts work without modification
- New parameters are optional

## Performance Impact

- Negligible overhead (preset lookup is O(1))
- No change to silence detection algorithm
- Same processing speed as before
- Additional logging provides better insight

## Best Practices

1. **Start with 'balanced'** - Works well for most cases
2. **Test on sample** - Try different presets on a short video first
3. **Consider audio quality** - Noisy audio needs conservative settings
4. **Match use case** - Training data vs benchmarking requires different approaches
5. **Document choice** - Record which preset used for reproducibility

## Use Case Recommendations

| Use Case | Recommended Preset | Notes |
|----------|-------------------|-------|
| Benchmarking dataset | `balanced` | Natural sentence boundaries |
| Training dataset | `sensitive` | More data, varied examples |
| Noisy audio | `conservative` + custom thresh | Reduce false splits |
| Studio quality | `sensitive` | Clean audio allows precision |
| Topic segmentation | `very_conservative` | Preserve context |
| Word-level analysis | `very_sensitive` | Maximum granularity |

## Technical Details

### Preset Parameters

| Preset | Min Silence | Threshold Offset | Keep Silence | Max Chunk |
|--------|-------------|------------------|--------------|-----------|
| very_sensitive | 400ms | -16 dB | 100ms | 15s |
| sensitive | 500ms | -18 dB | 120ms | 18s |
| balanced | 700ms | -20 dB | 150ms | 20s |
| conservative | 900ms | -22 dB | 180ms | 25s |
| very_conservative | 1200ms | -25 dB | 200ms | 30s |

### Dynamic Threshold Calculation

The system combines preset offsets with dynamic audio analysis:
1. Calculate RMS values for 20ms frames
2. Use 5th percentile as baseline noise floor
3. Apply preset offset relative to audio dBFS
4. Custom threshold overrides both if provided

### Priority Order
1. Custom silence threshold (if provided) - highest priority
2. Preset offset + dynamic calculation
3. Dynamic threshold alone (fallback)

## Future Enhancements

Potential improvements for future versions:
- [ ] Audio-quality based auto-preset selection
- [ ] Machine learning-based optimal threshold detection
- [ ] Per-video preset recommendation system
- [ ] Visualization tool for comparing presets
- [ ] Batch preset comparison reports

## Files Modified

### Core Files
- `utils/split_by_silence.py` - Added preset system
- `run_pipeline.py` - Added CLI arguments
- `complete_pipeline.sh` - Added shell options

### Documentation
- `docs/SILENCE_PRESETS_QUICK_REF.md` - Created
- `docs/silence_detection_presets.md` - Created (or already existed)
- `PIPELINE_README.md` - Updated

### Testing
- `test_silence_presets.py` - Created (or already existed)

## Migration Guide

### For Existing Users

No changes required! The system defaults to 'balanced' preset which maintains current behavior.

### To Use New Presets

Simply add the `--silence-preset` flag:
```bash
# Old command (still works)
./complete_pipeline.sh VIDEO_ID --syncnet-repo /path/to/syncnet

# New command with preset
./complete_pipeline.sh VIDEO_ID --syncnet-repo /path/to/syncnet --silence-preset sensitive
```

### To Migrate Custom Thresholds

If you previously hardcoded custom thresholds in the code, now use:
```bash
--custom-silence-thresh YOUR_THRESHOLD --custom-min-silence YOUR_MIN_SILENCE
```

## Support

For issues or questions:
1. Check `docs/silence_detection_presets.md` for detailed guide
2. Review `docs/SILENCE_PRESETS_QUICK_REF.md` for quick reference
3. Run `test_silence_presets.py` to verify system health
4. Check troubleshooting section above

## Version Info

- **Feature:** Silence Detection Preset System
- **Date:** October 11, 2025
- **Branch:** exp-avsr-week1
- **Status:** ✅ Implemented and tested
