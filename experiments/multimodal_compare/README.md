# Audio CTC Model Training and Evaluation Guide

## Overview
This directory contains a complete implementation of an audio-only CTC (Connectionist Temporal Classification) baseline for Bengali speech recognition. The system uses mel-spectrogram features from audio to predict Bengali character sequences.

## Directory Structure
```
experiments/multimodal_compare/
├── src/
│   ├── data/
│   │   └── dataset_audio_ctc.py     # Dataset and data loading
│   ├── models/
│   │   └── audio_ctc.py             # CTC model architecture
│   ├── train/
│   │   └── train_audio_ctc.py       # Training script
│   ├── eval/
│   │   ├── metrics.py               # Evaluation metrics (CER/WER)
│   │   ├── score_asr.py             # ASR scoring script
│   │   ├── test_inference.py        # Test set inference
│   │   └── simple_eval.py           # Simple evaluation script
│   └── utils/
│       └── text_norm.py             # Bengali text normalization
├── configs/
│   └── audio_ctc.yaml               # Training configuration
├── manifests/
│   ├── manifest.csv                 # Complete dataset manifest
│   ├── test_gold.csv                # Test set ground truth
│   └── charset.txt                  # Character vocabulary
├── checkpoints/audio_ctc/           # Model checkpoints
├── logs/audio_ctc/                  # Training logs
└── results/                         # Evaluation results
```

## Model Architecture

### Audio CTC Model (`models/audio_ctc.py`)
The model consists of three main components:

1. **CNN Feature Extractor**
   - 4 Conv1D blocks with ReLU and dropout
   - Channels: [80, 128, 256, 512, 512]
   - Kernel sizes: [3, 3, 3, 3, 3]
   - Strides: [1, 2, 1, 2, 1]
   - Reduces temporal dimension by factor of 4

2. **Bidirectional LSTM**
   - 2-layer BiLSTM with 256 hidden units per direction
   - Dropout between layers
   - Processes sequential features

3. **CTC Classification Head**
   - Linear layer: 512 → vocab_size (66 Bengali characters)
   - Log softmax activation
   - CTC loss for sequence alignment

### Key Features
- **Input**: Mel-spectrogram (80 bins, 25ms window, 10ms hop)
- **Output**: Bengali character sequences
- **Parameters**: 4,172,738 total
- **Training**: Mixed precision (AMP) support

## Training Procedure

### 1. Data Preparation
```bash
# Ensure manifest.csv has the required columns:
# utt_id, audio_path, google_txt, whisper_txt, split
```

### 2. Training Configuration
Edit `configs/audio_ctc.yaml`:
```yaml
# Training parameters
train:
  epochs: 15
  lr: 0.0003
  batch_size: null  # Dynamic bucketing
  amp: true
  grad_clip: 5.0

# Data parameters  
data:
  manifest: experiments/multimodal_compare/manifests/manifest.csv
  sample_rate: 16000
  mel_bins: 80
  bucketing_sec: 40
```

### 3. Run Training
```bash
cd /path/to/bengali-speech-audio-visual-dataset
source .venv/bin/activate
python experiments/multimodal_compare/src/train/train_audio_ctc.py
```

### Training Features
- **Dynamic Bucketing**: Groups samples by audio duration for efficient batching
- **Mixed Precision**: Uses AMP for faster training and lower memory usage
- **Gradient Clipping**: Prevents gradient explosion (max norm: 5.0)
- **Cosine Scheduling**: Learning rate scheduling with warmup
- **Checkpointing**: Saves best model and epoch checkpoints
- **Logging**: Comprehensive training logs and metrics

## Evaluation Procedure

### 1. Test Set Inference
Generate predictions on test split:
```bash
python experiments/multimodal_compare/src/eval/test_inference.py
```

**Output**: `results/test_predictions.csv` with columns:
- `utt_id`: Utterance identifier
- `prediction`: Model prediction
- `ground_truth`: Reference text

### 2. Compute Metrics
Quick evaluation without normalization:
```bash
python experiments/multimodal_compare/src/eval/simple_eval.py
```

Detailed evaluation with text normalization:
```bash
python experiments/multimodal_compare/src/eval/score_asr.py \
  --predictions results/test_predictions.csv \
  --test_gold manifests/test_gold.csv
```

### Evaluation Metrics
- **CER (Character Error Rate)**: Edit distance at character level
- **WER (Word Error Rate)**: Edit distance at word level
- **Text Normalization**: Bengali-specific cleaning for fair comparison

## Working Procedure of Current CTC Model

### 1. Input Processing
```
Audio (.wav) → Mel-spectrogram (80 × T) → CNN Features (512 × T/4)
```
- Load 16kHz mono audio
- Extract 80-bin mel-spectrogram features
- 25ms window, 10ms hop length
- CNN reduces temporal dimension by 4x

### 2. Sequence Modeling
```
CNN Features → BiLSTM → Context Features (512-dim)
```
- Bidirectional LSTM processes temporal sequence
- 2 layers with 256 hidden units each direction
- Dropout for regularization

### 3. CTC Classification
```
Context Features → Linear → Log Probabilities (vocab_size)
```
- Linear projection to character vocabulary (66 chars)
- Log softmax for probability distribution
- CTC alignment handles variable-length sequences

### 4. CTC Loss and Decoding
**Training (CTC Loss)**:
- Computes loss between predictions and target sequences
- Handles alignment automatically (no forced alignment needed)
- Blank token allows for insertions/deletions

**Inference (Greedy Decoding)**:
```python
# Pseudo-code for CTC decoding
for each timestep:
    pred = argmax(log_probs[t])
    if pred != blank and pred != previous:
        output.append(pred)
```

### 5. Text Processing Pipeline
```
Audio → Model → Character Indices → Bengali Text
```
- Model outputs character indices
- `indices_to_text()` converts to Bengali characters
- Blank tokens (index 0) are removed
- Consecutive duplicates are collapsed

## Key Implementation Details

### Dataset (`data/dataset_audio_ctc.py`)
- **Bucketing**: Groups samples by duration for efficient batching
- **Text Selection**: Prefers longer transcripts (Whisper > Google)
- **Normalization**: Uses `BengaliTextNormalizer` for consistent text
- **Caching**: Efficient audio loading with torchaudio

### Training Loop (`train/train_audio_ctc.py`)
- **Mixed Precision**: Automatic mixed precision with GradScaler
- **Learning Rate Scheduling**: Cosine annealing with linear warmup
- **Validation**: Regular validation with best model saving
- **Logging**: JSON metrics logging and comprehensive text logs

### Character Vocabulary
- **Size**: 66 characters including:
  - Bengali letters (ক, খ, গ, ...)
  - Vowel marks (া, ি, ী, ...)
  - Punctuation (।, ,)
  - Special tokens (<blank>)

## Performance Baseline
**Current Results (August 2025)**:
- Character Error Rate (CER): **70.92%**
- Word Error Rate (WER): **100.00%**
- Test samples: 14 utterances
- Training data: 102 samples

## Usage Examples

### Training from Scratch
```bash
# 1. Prepare your manifest.csv with audio_path, text, split columns
# 2. Create charset.txt with your character vocabulary  
# 3. Configure training parameters in configs/audio_ctc.yaml
# 4. Run training
python experiments/multimodal_compare/src/train/train_audio_ctc.py
```

### Inference on New Audio
```bash
# 1. Add new samples to manifest.csv with split='test'
# 2. Run inference
python experiments/multimodal_compare/src/eval/test_inference.py
# 3. Evaluate
python experiments/multimodal_compare/src/eval/simple_eval.py
```

### Model Inspection
```python
from models.audio_ctc import AudioCTCModel

# Load model
model = AudioCTCModel(vocab_size=66)
checkpoint = torch.load('checkpoints/audio_ctc/best_model.pt')
model.load_state_dict(checkpoint['model_state_dict'])

# Model info
print(f"Parameters: {sum(p.numel() for p in model.parameters()):,}")
print(f"Architecture: {model}")
```

## Troubleshooting

### Common Issues
1. **CUDA/MPS Memory**: Reduce batch size or use CPU
2. **Audio Loading**: Ensure 16kHz mono WAV files
3. **Character Encoding**: Use UTF-8 for Bengali text
4. **Path Issues**: Use absolute paths in manifest.csv

### Debug Tools
- `debug_predictions.py`: Analyze prediction quality
- `simple_eval.py`: Quick evaluation without normalization
- Training logs: Check convergence in `logs/audio_ctc/`

## Future Improvements
1. **Data Augmentation**: Speed/pitch perturbation, noise addition
2. **Architecture**: Transformer encoder, attention mechanisms
3. **Training**: Label smoothing, curriculum learning
4. **Multimodal**: Add visual features for audio-visual speech recognition

---
*Created: August 24, 2025*
*Model: Audio CTC Baseline v1.0*
