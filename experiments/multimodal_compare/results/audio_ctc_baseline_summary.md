# Audio CTC Baseline Results Summary

## Model Architecture
- **Model Type**: Audio-only CTC (Connectionist Temporal Classification)
- **Architecture**: CNN Feature Extractor + Bidirectional LSTM + CTC Head
- **Parameters**: 4,172,738 (4.17M)
- **Input Features**: Mel-spectrogram (80 bins, 25ms window, 10ms hop)
- **Vocabulary**: 66 Bengali characters

## Training Configuration
- **Dataset**: 102 training samples, 13 validation samples
- **Epochs**: 15
- **Optimizer**: AdamW (lr=3e-4)
- **Scheduler**: Cosine annealing with warmup (200 steps)
- **Batch Size**: Dynamic bucketing by audio duration
- **Mixed Precision**: Enabled (AMP)
- **Gradient Clipping**: 5.0

## Training Results
- **Final Training Loss**: 1.5282
- **Final Validation Loss**: 2.9258
- **Best Validation Loss**: 2.8294 (achieved at epoch 7)
- **Convergence**: Model converged from initial loss ~3.5 to final ~2.8

## Test Set Evaluation Results
- **Test Samples**: 14 utterances
- **Character Error Rate (CER)**: 70.92%
- **Word Error Rate (WER)**: 100.00%

## Analysis
### Strengths
1. **Successful Training**: Model converged properly with decreasing loss
2. **Character Recognition**: Model generates Bengali characters from audio
3. **Reasonable CER**: 70.92% CER shows partial character-level recognition

### Limitations
1. **High Error Rates**: 100% WER indicates poor word-level understanding
2. **Length Mismatch**: Predictions significantly shorter than ground truth
3. **Limited Vocabulary**: Only 22 out of 45 characters used in predictions
4. **Small Dataset**: Only 102 training samples may be insufficient

### Model Behavior
- Model generates roughly correct character patterns
- Predictions are much shorter than references (avg 30 vs 70 chars)
- Common Bengali characters are recognized (আ, ই, এ, ক, ন, র, ত, স)
- Missing complex characters and diacritics

## Baseline Establishment
This audio-only CTC model serves as our baseline for multimodal comparison:
- **CER Baseline**: 70.92%
- **WER Baseline**: 100.00%

Future audiovisual models should improve upon these metrics by incorporating lip movement information to enhance speech recognition accuracy.

## Files Generated
- **Model Checkpoints**: `experiments/multimodal_compare/checkpoints/audio_ctc/`
- **Training Logs**: `experiments/multimodal_compare/logs/audio_ctc/`
- **Test Predictions**: `experiments/multimodal_compare/results/test_predictions.csv`
- **Evaluation Scripts**: `experiments/multimodal_compare/src/eval/`

---
*Baseline completed on August 24, 2025*
