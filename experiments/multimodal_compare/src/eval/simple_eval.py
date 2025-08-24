#!/usr/bin/env python3
"""
Simple raw evaluation without text normalization
"""

import pandas as pd
import editdistance

def compute_raw_cer(pred, ref):
    """Compute raw character error rate"""
    if len(ref) == 0:
        return 1.0 if len(pred) > 0 else 0.0
    return editdistance.eval(pred, ref) / len(ref)

def compute_raw_wer(pred, ref):
    """Compute raw word error rate"""
    pred_words = pred.split()
    ref_words = ref.split()
    if len(ref_words) == 0:
        return 1.0 if len(pred_words) > 0 else 0.0
    return editdistance.eval(pred_words, ref_words) / len(ref_words)

def main():
    # Load predictions
    df = pd.read_csv("experiments/multimodal_compare/results/test_predictions.csv")
    
    print(f"Evaluating {len(df)} predictions...")
    
    cers = []
    wers = []
    
    for _, row in df.iterrows():
        pred = row['prediction'] if pd.notna(row['prediction']) else ""
        ref = row['ground_truth'] if pd.notna(row['ground_truth']) else ""
        
        cer = compute_raw_cer(pred, ref)
        wer = compute_raw_wer(pred, ref)
        
        cers.append(cer)
        wers.append(wer)
        
        print(f"{row['utt_id']}: CER={cer:.3f}, WER={wer:.3f}")
    
    avg_cer = sum(cers) / len(cers)
    avg_wer = sum(wers) / len(wers)
    
    print(f"\n=== AUDIO CTC BASELINE RESULTS ===")
    print(f"Character Error Rate (CER): {avg_cer:.4f} ({avg_cer*100:.2f}%)")
    print(f"Word Error Rate (WER): {avg_wer:.4f} ({avg_wer*100:.2f}%)")
    print(f"Number of test samples: {len(df)}")
    print("="*50)

if __name__ == "__main__":
    main()
