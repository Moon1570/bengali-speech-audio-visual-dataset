# Space Handling Fix Documentation

## Issue Discovered
During evaluation of the initial audio CTC baseline, we discovered a critical bug in space handling that was causing poor evaluation metrics.

## Root Cause
The `_load_charset` method in `dataset_audio_ctc.py` was using `line.strip()` to process charset file lines, which **removed space characters** when they appeared on their own line.

### Before Fix:
```python
def _load_charset(self, charset_file: str):
    with open(charset_file, 'r', encoding='utf-8') as f:
        for idx, line in enumerate(f):
            char = line.strip()  # ❌ This removes spaces!
            char_to_idx[char] = idx
```

### After Fix:
```python
def _load_charset(self, charset_file: str):
    with open(charset_file, 'r', encoding='utf-8') as f:
        for idx, line in enumerate(f):
            char = line.rstrip('\n\r')  # ✅ Only remove newlines
            char_to_idx[char] = idx
```

## Impact of the Bug

### Training Phase:
- Space character (index 1) was mapped to empty string `''`
- Model never learned to predict actual spaces
- Training text had spaces removed during `text_to_indices()` conversion

### Evaluation Phase:
- Ground truth retained spaces (from original transcripts)
- Predictions had no spaces (model learned without spaces)
- **Result**: 100% WER because word boundaries were lost

## Timeline of Discovery and Fix

### 1. Initial Results (Buggy)
- **CER**: 70.92%
- **WER**: 100.00%
- Predictions had no spaces, ground truth had no spaces

### 2. After Ground Truth Fix
- **CER**: 74.26% (worse - now comparing against spaced GT)
- **WER**: 100.00% (unchanged - predictions still spaceless)
- Ground truth had spaces, predictions still had no spaces

### 3. After Complete Fix + Retraining
- *(Training in progress)*
- Model now learns with proper space handling
- Expected: Significantly improved WER

## Files Modified
1. **`src/data/dataset_audio_ctc.py`**: Fixed `_load_charset()` method
2. **Training data**: Cleared and retraining with fixed space handling
3. **Evaluation**: Now correctly handles spaced text

## Lessons Learned
1. **Character-level details matter**: A single `.strip()` vs `.rstrip()` caused major issues
2. **Round-trip testing is crucial**: Always test text → indices → text conversion
3. **Evaluation alignment**: Ensure training and evaluation use same text processing
4. **Space is a character too**: Don't forget to handle whitespace properly

## Verification Commands
```bash
# Test space handling
python -c "
from src.data.dataset_audio_ctc import AudioCTCDataset
dataset = AudioCTCDataset(...)
sample_text = 'আমি তোমাকে ভালোবাসি'
indices = dataset.text_to_indices(sample_text)
recovered = dataset.indices_to_text(indices)
print(f'Original: {sample_text}')
print(f'Recovered: {recovered}')
print(f'Spaces preserved: {sample_text.count(\" \")} -> {recovered.count(\" \")}')
"
```

---
*Fixed: August 24, 2025*
*Impact: Critical for proper speech recognition evaluation*
