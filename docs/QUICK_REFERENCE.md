# Audio Processing Quick Reference

## 🎛️ Quick Command Reference

### Enable Audio Processing
```bash
# Noise reduction only
./complete_pipeline.sh <video_id> --syncnet-repo <path> --reduce-noise

# Speech amplification only
./complete_pipeline.sh <video_id> --syncnet-repo <path> --amplify-speech

# Both audio filters
./complete_pipeline.sh <video_id> --syncnet-repo <path> --reduce-noise --amplify-speech
```

### Disable Video Processing
```bash
# No face filtering
./complete_pipeline.sh <video_id> --syncnet-repo <path> --no-filter-faces

# No chunk refinement
./complete_pipeline.sh <video_id> --syncnet-repo <path> --no-refine-chunks

# Both disabled (fastest)
./complete_pipeline.sh <video_id> --syncnet-repo <path> --no-filter-faces --no-refine-chunks
```

### Common Presets

#### Maximum Quality
```bash
./complete_pipeline.sh <video_id> --syncnet-repo <path> \
  --reduce-noise --amplify-speech --preset high
```

#### Fast Processing
```bash
./complete_pipeline.sh <video_id> --syncnet-repo <path> \
  --no-filter-faces --no-refine-chunks --preset low
```

#### Balanced (Recommended)
```bash
./complete_pipeline.sh <video_id> --syncnet-repo <path> \
  --reduce-noise --preset medium
```

---

## 📊 Feature Matrix

| Feature | Flag | Default | Status |
|---------|------|---------|--------|
| Noise Reduction | `--reduce-noise` | OFF | 🔄 Pending |
| Speech Amplification | `--amplify-speech` | OFF | 🔄 Pending |
| Face Filtering | `--no-filter-faces` (to disable) | ON | ✅ Working |
| Chunk Refinement | `--no-refine-chunks` (to disable) | ON | ✅ Working |

---

## ⏱️ Processing Time Guide

| Config | Time (10-min video) | Quality | Use Case |
|--------|---------------------|---------|----------|
| Minimal | ~15 min | ⭐ | Testing |
| Default | ~25 min | ⭐⭐⭐ | General use |
| Audio Enhanced | ~30 min | ⭐⭐⭐⭐ | Noisy videos |
| Maximum | ~45 min | ⭐⭐⭐⭐⭐ | Production |

---

## 🔧 Complete Flag List

```bash
./complete_pipeline.sh <video_id> [options]

Required:
  --syncnet-repo PATH         Path to SyncNet repository

Optional:
  --current-repo PATH         Path to current repo (default: current dir)
  --max-workers NUM           Parallel workers (default: 8)
  --min-chunk-duration NUM    Min chunk seconds (default: 2.0)
  --preset PRESET             SyncNet quality: low/medium/high (default: high)

Audio Processing:
  --reduce-noise              Enable noise reduction
  --amplify-speech            Enable speech amplification

Video Processing:
  --no-filter-faces           Disable face filtering
  --no-refine-chunks          Disable chunk refinement

Pipeline Control:
  --skip-step1                Skip chunk creation
  --skip-step2                Skip SyncNet filtering
  --skip-step3                Skip directory organization
  --skip-step4                Skip transcription
  --help                      Show help
```

---

## 💡 Quick Decision Guide

**My video has...**

| Problem | Solution |
|---------|----------|
| Background noise (fan, hum) | Add `--reduce-noise` |
| Quiet speaker | Add `--amplify-speech` |
| No faces visible | Add `--no-filter-faces` |
| Already good boundaries | Add `--no-refine-chunks` |
| All of the above | Use all flags together |
| High quality audio | Skip audio flags |
| Testing pipeline | Add both `--no-filter` flags |

---

## 📝 Real-World Examples

### Conference Recording (Noisy, Quiet Speaker)
```bash
./complete_pipeline.sh ABC123 --syncnet-repo ~/syncnet_python \
  --reduce-noise --amplify-speech --preset medium
```

### Studio Interview (Clean Audio)
```bash
./complete_pipeline.sh ABC123 --syncnet-repo ~/syncnet_python \
  --preset high
```

### Screen Recording (No Face)
```bash
./complete_pipeline.sh ABC123 --syncnet-repo ~/syncnet_python \
  --no-filter-faces --no-refine-chunks
```

### Quick Test
```bash
./complete_pipeline.sh ABC123 --syncnet-repo ~/syncnet_python \
  --no-filter-faces --no-refine-chunks --preset low --max-workers 16
```

---

For detailed documentation, see: `docs/audio_processing_controls.md`
