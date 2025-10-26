# Silence Detection Presets - Quick Reference

## TL;DR
```bash
# Default - good for most cases
./complete_pipeline.sh VIDEO_ID --syncnet-repo /path/to/syncnet

# More chunks (sensitive)
./complete_pipeline.sh VIDEO_ID --syncnet-repo /path/to/syncnet --silence-preset sensitive

# Fewer chunks (conservative)
./complete_pipeline.sh VIDEO_ID --syncnet-repo /path/to/syncnet --silence-preset conservative

# Custom threshold
./complete_pipeline.sh VIDEO_ID --syncnet-repo /path/to/syncnet --custom-silence-thresh -35.0
```

## Preset Comparison

| Preset | Chunks | Duration | Best For |
|--------|--------|----------|----------|
| `very_sensitive` | Most (many short) | ~3-15s | Word-level analysis |
| `sensitive` | Many | ~5-18s | Phrase-level splitting |
| **`balanced`** (default) | Moderate | ~7-20s | Sentence boundaries |
| `conservative` | Fewer | ~10-25s | Paragraph-level |
| `very_conservative` | Fewest (long) | ~15-30s | Topic boundaries |

## Quick Decision Tree

```
Are you splitting on silence correctly?
│
├─ Too many short chunks
│  └─ Use: conservative or very_conservative
│
├─ Too few long chunks / Not splitting enough
│  └─ Use: sensitive or very_sensitive
│
├─ Chunks split mid-sentence
│  └─ Use: --custom-min-silence 800 (or higher)
│
└─ Default works well
   └─ Keep: balanced (default)
```

## Parameters at a Glance

| Preset | Min Silence | Threshold Offset |
|--------|-------------|------------------|
| very_sensitive | 400ms | -16 dB |
| sensitive | 500ms | -18 dB |
| **balanced** | **700ms** | **-20 dB** |
| conservative | 900ms | -22 dB |
| very_conservative | 1200ms | -25 dB |

## Common Use Cases

### Benchmarking Dataset
```bash
--silence-preset balanced
```

### Training Dataset (more data)
```bash
--silence-preset sensitive
```

### Noisy Audio
```bash
--silence-preset conservative --custom-silence-thresh -30.0
```

### Studio Quality
```bash
--silence-preset sensitive
```

## Custom Parameters

```bash
# Override minimum silence duration
--custom-min-silence 600  # milliseconds

# Override silence threshold
--custom-silence-thresh -35.0  # dBFS

# Combine both
--silence-preset balanced --custom-min-silence 800 --custom-silence-thresh -32.0
```

## Testing

```bash
# Test on a single video
.venv/bin/python run_pipeline.py downloads/test.mp4 --silence-preset sensitive

# Compare presets
for preset in very_sensitive sensitive balanced conservative very_conservative; do
    echo "Testing $preset..."
    .venv/bin/python run_pipeline.py downloads/test.mp4 --silence-preset $preset
done
```

## See Also
- Full documentation: `docs/silence_detection_presets.md`
- Implementation: `utils/split_by_silence.py`
- Test script: `test_silence_presets.py`
