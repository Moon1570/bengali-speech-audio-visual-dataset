#!/usr/bin/env python3
"""
Simple evaluation to debug the audio CTC model predictions
"""

import pandas as pd
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.text_norm import BengaliTextNormalizer

def main():
    # Load our predictions
    pred_df = pd.read_csv("experiments/multimodal_compare/results/test_predictions.csv")
    
    # Initialize normalizer
    normalizer = BengaliTextNormalizer()
    
    print("=== RAW PREDICTIONS VS GROUND TRUTH ===")
    for i, row in pred_df.iterrows():
        if i >= 5:  # Only show first 5 for debugging
            break
            
        print(f"\nUtterance: {row['utt_id']}")
        print(f"Raw GT: {repr(row['ground_truth'])}")
        print(f"Raw Pred: {repr(row['prediction'])}")
        
        # Normalize both
        norm_gt = normalizer.normalize(row['ground_truth'])
        norm_pred = normalizer.normalize(row['prediction'])
        
        print(f"Norm GT: {repr(norm_gt)}")
        print(f"Norm Pred: {repr(norm_pred)}")
        
        # Character level comparison
        print(f"GT chars: {len(row['ground_truth'])}, Pred chars: {len(row['prediction'])}")
        print(f"Norm GT chars: {len(norm_gt)}, Norm Pred chars: {len(norm_pred)}")
        
        # Check if completely different
        if norm_gt and norm_pred:
            common_chars = set(norm_gt) & set(norm_pred)
            print(f"Common characters: {len(common_chars)} out of {len(set(norm_gt))}")
        
        print("-" * 80)
        
    # Check character distribution
    print("\n=== CHARACTER ANALYSIS ===")
    all_gt_chars = ''.join(pred_df['ground_truth'].fillna(''))
    all_pred_chars = ''.join(pred_df['prediction'].fillna(''))
    
    gt_char_set = set(all_gt_chars)
    pred_char_set = set(all_pred_chars)
    
    print(f"Ground truth unique chars: {len(gt_char_set)}")
    print(f"Prediction unique chars: {len(pred_char_set)}")
    print(f"Common chars: {len(gt_char_set & pred_char_set)}")
    
    print(f"\nGT sample chars: {sorted(list(gt_char_set))[:20]}")
    print(f"Pred sample chars: {sorted(list(pred_char_set))[:20]}")


if __name__ == "__main__":
    main()
