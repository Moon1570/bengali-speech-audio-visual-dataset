"""
Score ASR predictions against ground truth

Takes predictions CSV and test_gold CSV, computes CER/WER metrics.
"""

import pandas as pd
import argparse
import yaml
import torch
import csv
from pathlib import Path
from typing import Dict, List, Tuple
import logging
import sys

# Import our modules
sys.path.append(str(Path(__file__).parent.parent))
from eval.metrics import SpeechRecognitionMetrics
from data.dataset_audio_ctc import AudioCTCDataset
from models.audio_ctc import create_audio_ctc_model
from utils.text_norm import BengaliTextNormalizer


def load_predictions_csv(predictions_file: str) -> Dict[str, str]:
    """
    Load predictions from CSV file
    
    Args:
        predictions_file: Path to predictions CSV
        
    Returns:
        Dictionary mapping utt_id to predicted text
    """
    predictions = {}
    
    try:
        with open(predictions_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                utt_id = row['utt_id']
                pred_text = row.get('pred_text', '').strip()
                predictions[utt_id] = pred_text
    except Exception as e:
        print(f"Error reading predictions file: {e}")
        return {}
    
    return predictions


def load_test_gold_csv(test_gold_file: str) -> Dict[str, str]:
    """
    Load ground truth from test_gold CSV file
    
    Args:
        test_gold_file: Path to test_gold CSV
        
    Returns:
        Dictionary mapping utt_id to ground truth text
    """
    ground_truth = {}
    
    try:
        with open(test_gold_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                utt_id = row['utt_id']
                
                # Use gold_txt if available, otherwise fall back to best available transcript
                gold_txt = row.get('gold_txt', '').strip()
                if gold_txt:
                    ground_truth[utt_id] = gold_txt
                else:
                    # Fall back to original transcripts
                    google_txt = row.get('google_txt', '').strip()
                    whisper_txt = row.get('whisper_txt', '').strip()
                    
                    # Choose better transcript
                    if len(whisper_txt) > len(google_txt) and whisper_txt:
                        ground_truth[utt_id] = whisper_txt
                    elif google_txt:
                        ground_truth[utt_id] = google_txt
                    elif whisper_txt:
                        ground_truth[utt_id] = whisper_txt
                    else:
                        print(f"Warning: No ground truth for {utt_id}")
    except Exception as e:
        print(f"Error reading test_gold file: {e}")
        return {}
    
    return ground_truth


def align_predictions_and_references(
    predictions: Dict[str, str],
    ground_truth: Dict[str, str]
) -> Tuple[List[str], List[str], List[str]]:
    """
    Align predictions with ground truth
    
    Args:
        predictions: Dictionary of predictions
        ground_truth: Dictionary of ground truth
        
    Returns:
        Tuple of (utt_ids, aligned_predictions, aligned_references)
    """
    utt_ids = []
    aligned_predictions = []
    aligned_references = []
    
    # Find common utterances
    common_utts = set(predictions.keys()) & set(ground_truth.keys())
    
    if not common_utts:
        print("Warning: No common utterances found between predictions and ground truth")
        return [], [], []
    
    print(f"Found {len(common_utts)} common utterances")
    
    # Sort for consistent ordering
    for utt_id in sorted(common_utts):
        utt_ids.append(utt_id)
        aligned_predictions.append(predictions[utt_id])
        aligned_references.append(ground_truth[utt_id])
    
    return utt_ids, aligned_predictions, aligned_references


def create_detailed_results_csv(
    utt_ids: List[str],
    predictions: List[str],
    references: List[str],
    cer_scores: List[float],
    wer_scores: List[float],
    output_file: str
):
    """
    Create detailed results CSV with per-utterance metrics
    
    Args:
        utt_ids: List of utterance IDs
        predictions: List of predictions
        references: List of references
        cer_scores: List of CER scores
        wer_scores: List of WER scores
        output_file: Output CSV file path
    """
    results_data = []
    
    for utt_id, pred, ref, cer, wer in zip(utt_ids, predictions, references, cer_scores, wer_scores):
        results_data.append({
            'utt_id': utt_id,
            'prediction': pred,
            'reference': ref,
            'cer': cer,
            'wer': wer
        })
    
    # Save to CSV
    df = pd.DataFrame(results_data)
    df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"Detailed results saved to: {output_file}")


def evaluate_asr_predictions(
    predictions_file: str,
    test_gold_file: str,
    output_dir: str = None,
    detailed_csv: bool = True
) -> Dict[str, float]:
    """
    Evaluate ASR predictions against ground truth
    
    Args:
        predictions_file: Path to predictions CSV
        test_gold_file: Path to test_gold CSV
        output_dir: Output directory for detailed results
        detailed_csv: Whether to save detailed per-utterance results
        
    Returns:
        Dictionary with evaluation metrics
    """
    print("Loading predictions and ground truth...")
    
    # Load data
    predictions = load_predictions_csv(predictions_file)
    ground_truth = load_test_gold_csv(test_gold_file)
    
    print(f"Loaded {len(predictions)} predictions")
    print(f"Loaded {len(ground_truth)} ground truth entries")
    
    # Align data
    utt_ids, aligned_preds, aligned_refs = align_predictions_and_references(
        predictions, ground_truth
    )
    
    if not aligned_preds:
        print("Error: No aligned data found")
        return {}
    
    print(f"Evaluating {len(aligned_preds)} utterances...")
    
    # Compute metrics
    metrics_calc = SpeechRecognitionMetrics(normalize_for_eval=True)
    metrics = metrics_calc.compute_all_metrics(aligned_preds, aligned_refs)
    
    # Print results
    print("\n" + "="*50)
    print("EVALUATION RESULTS")
    print("="*50)
    print(f"Total utterances evaluated: {len(aligned_preds)}")
    print(f"Character Error Rate (CER): {metrics['cer']:.4f} ({metrics['cer']*100:.2f}%)")
    print(f"Word Error Rate (WER): {metrics['wer']:.4f} ({metrics['wer']*100:.2f}%)")
    print(f"CER (mean ± std): {metrics['cer_mean']:.4f} ± {metrics['cer_std']:.4f}")
    print(f"WER (mean ± std): {metrics['wer_mean']:.4f} ± {metrics['wer_std']:.4f}")
    print("="*50)
    
    # Save detailed results if requested
    if detailed_csv and output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        detailed_file = output_dir / "detailed_results.csv"
        create_detailed_results_csv(
            utt_ids,
            aligned_preds,
            aligned_refs,
            metrics['per_utterance_cer'],
            metrics['per_utterance_wer'],
            str(detailed_file)
        )
    
    return metrics


def generate_predictions_from_model(
    model_checkpoint: str,
    config_file: str,
    test_manifest: str,
    output_file: str
) -> str:
    """
    Generate predictions from a trained model
    
    Args:
        model_checkpoint: Path to model checkpoint
        config_file: Path to config file
        test_manifest: Path to test manifest (or use test split from train manifest)
        output_file: Output predictions CSV file
        
    Returns:
        Path to generated predictions file
    """
    print("Generating predictions from model...")
    
    # Load config
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    # Load model
    print("Loading model...")
    checkpoint = torch.load(model_checkpoint, map_location=device)
    vocab_size = checkpoint['vocab_size']
    
    model = create_audio_ctc_model(
        vocab_size=vocab_size,
        mel_bins=config['data']['mel_bins'],
        model_size="small"
    )
    model.load_state_dict(checkpoint['model_state_dict'])
    model = model.to(device)
    model.eval()
    
    # Load test dataset
    print("Loading test dataset...")
    from data.dataset_audio_ctc import create_dataloader
    
    test_loader = create_dataloader(
        manifest_csv=test_manifest,
        charset_file=config['text']['charset'],
        split="test",  # Use test split
        sample_rate=config['data']['sample_rate'],
        mel_bins=config['data']['mel_bins'],
        win_ms=config['data']['win_ms'],
        hop_ms=config['data']['hop_ms'],
        bucketing_sec=0,  # No bucketing for inference
        num_workers=config['data']['num_workers'],
        shuffle=False
    )
    
    # Generate predictions
    print("Generating predictions...")
    predictions_data = []
    
    with torch.no_grad():
        for batch in test_loader:
            audios = batch['audios'].to(device)
            audio_lens = batch['audio_lens'].to(device)
            utt_ids = batch['utt_ids']
            
            # Forward pass
            log_probs, output_lengths = model(audios, audio_lens)
            
            # Decode
            decoded_sequences = model.decode_greedy(log_probs, output_lengths)
            
            # Convert to text
            dataset = test_loader.dataset
            for utt_id, decoded in zip(utt_ids, decoded_sequences):
                pred_text = dataset.indices_to_text(decoded)
                predictions_data.append({
                    'utt_id': utt_id,
                    'pred_text': pred_text
                })
    
    # Save predictions
    df = pd.DataFrame(predictions_data)
    df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"Saved {len(predictions_data)} predictions to: {output_file}")
    
    return output_file


def main():
    parser = argparse.ArgumentParser(description="Evaluate ASR predictions")
    parser.add_argument(
        '--predictions',
        type=str,
        help='Path to predictions CSV file'
    )
    parser.add_argument(
        '--test_gold',
        type=str,
        required=True,
        help='Path to test_gold CSV file'
    )
    parser.add_argument(
        '--output_dir',
        type=str,
        help='Output directory for detailed results'
    )
    parser.add_argument(
        '--model_checkpoint',
        type=str,
        help='Path to model checkpoint (for generating predictions)'
    )
    parser.add_argument(
        '--config',
        type=str,
        help='Path to config file (for generating predictions)'
    )
    parser.add_argument(
        '--test_manifest',
        type=str,
        help='Path to test manifest (for generating predictions)'
    )
    
    args = parser.parse_args()
    
    # Generate predictions if model provided
    if args.model_checkpoint and args.config:
        if not args.test_manifest:
            print("Error: --test_manifest required when using --model_checkpoint")
            return
        
        predictions_file = Path(args.output_dir or ".") / "preds_test.csv"
        args.predictions = generate_predictions_from_model(
            args.model_checkpoint,
            args.config,
            args.test_manifest,
            str(predictions_file)
        )
    
    # Evaluate predictions
    if args.predictions:
        evaluate_asr_predictions(
            args.predictions,
            args.test_gold,
            args.output_dir,
            detailed_csv=True
        )
    else:
        print("Error: Either --predictions or --model_checkpoint must be provided")


if __name__ == "__main__":
    main()
