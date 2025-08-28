"""
Audio CTC Model Inference Script

Generates predictions on test set for baseline evaluation.
"""

import torch
import pandas as pd
import numpy as np
from torch.utils.data import DataLoader
import yaml
import argparse
from pathlib import Path
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from data.dataset_audio_ctc import AudioCTCDataset
from models.audio_ctc import AudioCTCModel


def load_model(checkpoint_path, config_path, device):
    """Load trained model from checkpoint"""
    # Load config
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Create a temporary dataset to get vocab info
    temp_dataset = AudioCTCDataset(
        manifest_csv=config['data']['manifest'],
        charset_file=config['text']['charset'],
        split=config['data']['split_train'],
        sample_rate=config['data']['sample_rate'],
        mel_bins=config['data']['mel_bins'],
        win_ms=config['data']['win_ms'],
        hop_ms=config['data']['hop_ms']
    )
    
    vocab_size = temp_dataset.vocab_size
    
    # Create model with default parameters (same as training)
    model = AudioCTCModel(
        vocab_size=vocab_size,
        hidden_dim=512,    # Default from model
        lstm_layers=2,     # Default from model
        dropout=0.1        # Default from model
    )
    
    # Load checkpoint
    checkpoint = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.to(device)
    model.eval()
    
    return model, temp_dataset, config


def inference_on_dataset(model, dataloader, dataset, device):
    """Run inference on dataset and return predictions"""
    predictions = []
    ground_truths = []
    
    model.eval()
    with torch.no_grad():
        for batch_idx, (audio, audio_lengths, text, text_lengths) in enumerate(dataloader):
            audio = audio.to(device)
            audio_lengths = audio_lengths.to(device)
            
            # Forward pass
            log_probs, output_lengths = model(audio, audio_lengths)
            
            # Decode predictions
            batch_predictions = model.decode_predictions(log_probs, output_lengths)
            
            # Convert to text
            for i, pred_indices in enumerate(batch_predictions):
                pred_text = dataset.indices_to_text(pred_indices)
                gt_text = dataset.indices_to_text(text[i][:text_lengths[i]].tolist())
                
                predictions.append(pred_text)
                ground_truths.append(gt_text)
            
            if batch_idx % 10 == 0:
                print(f"Processed batch {batch_idx + 1}/{len(dataloader)}")
    
    return predictions, ground_truths


def main():
    parser = argparse.ArgumentParser(description='Audio CTC Inference')
    parser.add_argument('--checkpoint', type=str, required=True, help='Path to model checkpoint')
    parser.add_argument('--config', type=str, required=True, help='Path to config file')
    parser.add_argument('--test_manifest', type=str, required=True, help='Path to test manifest CSV')
    parser.add_argument('--output', type=str, required=True, help='Output CSV path for predictions')
    parser.add_argument('--batch_size', type=int, default=8, help='Batch size for inference')
    
    args = parser.parse_args()
    
    # Setup device
    device = torch.device('mps' if torch.backends.mps.is_available() else 'cpu')
    print(f"Using device: {device}")
    
    # Load model
    print("Loading model...")
    model, temp_dataset, config = load_model(args.checkpoint, args.config, device)
    print("Model loaded successfully!")
    
    # Create test dataset
    print("Creating test dataset...")
    test_dataset = AudioCTCDataset(
        manifest_csv=args.test_manifest,
        charset_file=config['text']['charset'],
        split='test',
        sample_rate=config['data']['sample_rate'],
        mel_bins=config['data']['mel_bins'],
        win_ms=config['data']['win_ms'],
        hop_ms=config['data']['hop_ms']
    )
    
    test_dataloader = DataLoader(
        test_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        collate_fn=test_dataset.collate_fn,
        num_workers=0  # Use 0 for MPS compatibility
    )
    
    print(f"Test dataset size: {len(test_dataset)}")
    
    # Run inference
    print("Running inference...")
    predictions, ground_truths = inference_on_dataset(model, test_dataloader, test_dataset, device)
    
    # Create results DataFrame
    results_df = pd.DataFrame({
        'prediction': predictions,
        'ground_truth': ground_truths
    })
    
    # Save results
    results_df.to_csv(args.output, index=False, encoding='utf-8')
    print(f"Results saved to: {args.output}")
    
    # Print some examples
    print("\nSample predictions:")
    for i in range(min(5, len(predictions))):
        print(f"GT: {ground_truths[i]}")
        print(f"Pred: {predictions[i]}")
        print("-" * 50)


if __name__ == "__main__":
    main()
