#!/usr/bin/env python3
"""
Simple Audio CTC Test Inference Script

Runs inference on test split from manifest.csv and saves predictions.
"""

import torch
import pandas as pd
import numpy as np
from torch.utils.data import DataLoader
import yaml
from pathlib import Path
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from data.dataset_audio_ctc import AudioCTCDataset, collate_fn
from models.audio_ctc import AudioCTCModel


def main():
    # Paths
    checkpoint_path = "experiments/multimodal_compare/checkpoints/audio_ctc/best_model.pt"
    manifest_path = "experiments/multimodal_compare/manifests/manifest.csv"
    charset_path = "experiments/multimodal_compare/manifests/charset.txt"
    output_dir = "experiments/multimodal_compare/results"
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Load manifest and filter for test set
    print("Loading manifest...")
    df = pd.read_csv(manifest_path)
    test_df = df[df['split'] == 'test']
    print(f"Found {len(test_df)} test samples")
    
    if len(test_df) == 0:
        print("No test samples found! Checking available splits:")
        print(df['split'].value_counts())
        return
    
    # Save test manifest
    test_manifest_path = os.path.join(output_dir, "test_manifest.csv")
    test_df.to_csv(test_manifest_path, index=False)
    
    # Setup device
    device = torch.device('mps' if torch.backends.mps.is_available() else 'cpu')
    print(f"Using device: {device}")
    
    # Create test dataset to get vocab info
    print("Creating dataset...")
    test_dataset = AudioCTCDataset(
        manifest_csv=test_manifest_path,
        charset_file=charset_path,
        split='test',  # Use test split since our CSV has test samples
        sample_rate=16000,
        mel_bins=80,
        win_ms=25,
        hop_ms=10
    )
    
    vocab_size = test_dataset.vocab_size
    print(f"Vocabulary size: {vocab_size}")
    
    # Create model
    print("Creating model...")
    model = AudioCTCModel(
        vocab_size=vocab_size,
        hidden_dim=512,
        lstm_layers=2,
        dropout=0.1
    )
    
    # Load checkpoint
    print("Loading checkpoint...")
    checkpoint = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.to(device)
    model.eval()
    print("Model loaded successfully!")
    
    # Create dataloader
    test_dataloader = DataLoader(
        test_dataset,
        batch_size=4,
        shuffle=False,
        collate_fn=collate_fn,
        num_workers=0  # Use 0 for MPS compatibility
    )
    
    # Run inference
    print("Running inference...")
    predictions = []
    ground_truths = []
    utt_ids = []
    
    model.eval()
    with torch.no_grad():
        for batch_idx, batch in enumerate(test_dataloader):
            audio = batch['audios'].to(device)
            audio_lengths = batch['audio_lens'].to(device)
            text = batch['targets']
            text_lengths = batch['target_lens']
            
            # Forward pass
            log_probs, output_lengths = model(audio, audio_lengths)
            
            # Decode predictions
            batch_predictions = model.decode_greedy(log_probs, output_lengths)
            
            # Convert to text
            for i, pred_indices in enumerate(batch_predictions):
                pred_text = test_dataset.indices_to_text(pred_indices)
                gt_text = test_dataset.indices_to_text(text[i][:text_lengths[i]].tolist())
                
                predictions.append(pred_text)
                ground_truths.append(gt_text)
                
                # Get utterance ID
                utt_ids.append(batch['utt_ids'][i])
            
            print(f"Processed batch {batch_idx + 1}/{len(test_dataloader)}")
    
    # Create results DataFrame
    results_df = pd.DataFrame({
        'utt_id': utt_ids,
        'prediction': predictions,
        'ground_truth': ground_truths
    })
    
    # Save results
    output_path = os.path.join(output_dir, "test_predictions.csv")
    results_df.to_csv(output_path, index=False, encoding='utf-8')
    print(f"Results saved to: {output_path}")
    
    # Print some examples
    print("\nSample predictions:")
    for i in range(min(5, len(predictions))):
        print(f"ID: {utt_ids[i]}")
        print(f"GT: {ground_truths[i]}")
        print(f"Pred: {predictions[i]}")
        print("-" * 60)
    
    print(f"\nTotal test samples processed: {len(predictions)}")


if __name__ == "__main__":
    main()
