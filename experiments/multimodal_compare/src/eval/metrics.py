"""
Evaluation metrics for speech recognition

Provides CER (Character Error Rate) and WER (Word Error Rate) computation
with support for Bengali text normalization.
"""

import jiwer
import numpy as np
from typing import List, Tuple, Dict
import re
import unicodedata
from pathlib import Path
import sys

# Import text normalization
sys.path.append(str(Path(__file__).parent.parent))
from utils.text_norm import BengaliTextNormalizer


class SpeechRecognitionMetrics:
    """Metrics calculator for speech recognition evaluation"""
    
    def __init__(self, normalize_for_eval: bool = True):
        """
        Initialize metrics calculator
        
        Args:
            normalize_for_eval: Whether to apply text normalization before computing metrics
        """
        self.normalize_for_eval = normalize_for_eval
        if normalize_for_eval:
            self.normalizer = BengaliTextNormalizer()
    
    def normalize_text(self, text: str) -> str:
        """Normalize text for evaluation"""
        if not self.normalize_for_eval:
            return text
        
        # Use the normalizer's normalize method
        return self.normalizer.normalize(text)
    
    def compute_cer(self, predictions: List[str], references: List[str]) -> Dict[str, float]:
        """
        Compute Character Error Rate (CER)
        
        Args:
            predictions: List of predicted texts
            references: List of reference texts
            
        Returns:
            Dictionary with CER metrics
        """
        if len(predictions) != len(references):
            raise ValueError("Predictions and references must have the same length")
        
        total_chars = 0
        total_errors = 0
        cer_scores = []
        
        for pred, ref in zip(predictions, references):
            # Normalize texts
            pred_norm = self.normalize_text(pred)
            ref_norm = self.normalize_text(ref)
            
            # Compute character-level edit distance
            errors = self._edit_distance(pred_norm, ref_norm)
            chars = len(ref_norm)
            
            # Handle empty reference
            if chars == 0:
                cer = 1.0 if len(pred_norm) > 0 else 0.0
            else:
                cer = errors / chars
            
            total_errors += errors
            total_chars += chars
            cer_scores.append(cer)
        
        # Overall CER
        overall_cer = total_errors / max(total_chars, 1)
        
        return {
            'cer': overall_cer,
            'cer_mean': np.mean(cer_scores),
            'cer_std': np.std(cer_scores),
            'total_characters': total_chars,
            'total_errors': total_errors,
            'per_utterance_cer': cer_scores
        }
    
    def compute_wer(self, predictions: List[str], references: List[str]) -> Dict[str, float]:
        """
        Compute Word Error Rate (WER) using jiwer
        
        Args:
            predictions: List of predicted texts
            references: List of reference texts
            
        Returns:
            Dictionary with WER metrics
        """
        if len(predictions) != len(references):
            raise ValueError("Predictions and references must have the same length")
        
        # Normalize texts
        pred_norm = [self.normalize_text(pred) for pred in predictions]
        ref_norm = [self.normalize_text(ref) for ref in references]
        
        # Compute WER using jiwer
        try:
            # Overall WER
            overall_wer = jiwer.wer(ref_norm, pred_norm)
            
            # Per-utterance WER
            wer_scores = []
            for pred, ref in zip(pred_norm, ref_norm):
                try:
                    wer = jiwer.wer(ref, pred)
                    wer_scores.append(wer)
                except:
                    # Handle edge cases (empty strings, etc.)
                    if not ref and not pred:
                        wer_scores.append(0.0)
                    elif not ref:
                        wer_scores.append(1.0)  # Insertion errors
                    else:
                        wer_scores.append(1.0)  # Deletion errors
            
            return {
                'wer': overall_wer,
                'wer_mean': np.mean(wer_scores),
                'wer_std': np.std(wer_scores),
                'per_utterance_wer': wer_scores
            }
            
        except Exception as e:
            print(f"Error computing WER: {e}")
            # Fallback to manual computation
            return self._compute_wer_manual(pred_norm, ref_norm)
    
    def _compute_wer_manual(self, predictions: List[str], references: List[str]) -> Dict[str, float]:
        """Manual WER computation as fallback"""
        total_words = 0
        total_errors = 0
        wer_scores = []
        
        for pred, ref in zip(predictions, references):
            pred_words = pred.split()
            ref_words = ref.split()
            
            errors = self._edit_distance(pred_words, ref_words)
            words = len(ref_words)
            
            if words == 0:
                wer = 1.0 if len(pred_words) > 0 else 0.0
            else:
                wer = errors / words
            
            total_errors += errors
            total_words += words
            wer_scores.append(wer)
        
        overall_wer = total_errors / max(total_words, 1)
        
        return {
            'wer': overall_wer,
            'wer_mean': np.mean(wer_scores),
            'wer_std': np.std(wer_scores),
            'per_utterance_wer': wer_scores
        }
    
    def _edit_distance(self, seq1, seq2):
        """Compute edit distance between two sequences"""
        len1, len2 = len(seq1), len(seq2)
        
        # Create DP table
        dp = [[0] * (len2 + 1) for _ in range(len1 + 1)]
        
        # Initialize base cases
        for i in range(len1 + 1):
            dp[i][0] = i
        for j in range(len2 + 1):
            dp[0][j] = j
        
        # Fill DP table
        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                if seq1[i-1] == seq2[j-1]:
                    dp[i][j] = dp[i-1][j-1]
                else:
                    dp[i][j] = 1 + min(
                        dp[i-1][j],     # deletion
                        dp[i][j-1],     # insertion
                        dp[i-1][j-1]    # substitution
                    )
        
        return dp[len1][len2]
    
    def compute_all_metrics(self, predictions: List[str], references: List[str]) -> Dict[str, float]:
        """
        Compute both CER and WER metrics
        
        Args:
            predictions: List of predicted texts
            references: List of reference texts
            
        Returns:
            Dictionary with all metrics
        """
        cer_metrics = self.compute_cer(predictions, references)
        wer_metrics = self.compute_wer(predictions, references)
        
        # Combine metrics
        all_metrics = {}
        all_metrics.update(cer_metrics)
        all_metrics.update(wer_metrics)
        
        return all_metrics


def evaluate_from_files(predictions_file: str, references_file: str) -> Dict[str, float]:
    """
    Evaluate predictions from text files
    
    Args:
        predictions_file: Path to file with predictions (one per line)
        references_file: Path to file with references (one per line)
        
    Returns:
        Dictionary with evaluation metrics
    """
    # Read predictions
    with open(predictions_file, 'r', encoding='utf-8') as f:
        predictions = [line.strip() for line in f]
    
    # Read references
    with open(references_file, 'r', encoding='utf-8') as f:
        references = [line.strip() for line in f]
    
    # Compute metrics
    metrics_calculator = SpeechRecognitionMetrics()
    metrics = metrics_calculator.compute_all_metrics(predictions, references)
    
    return metrics


if __name__ == "__main__":
    # Test the metrics
    print("Testing SpeechRecognitionMetrics...")
    
    # Example Bengali texts
    predictions = [
        "এটি একটি পরীক্ষা।",
        "আমি বাংলায় কথা বলি",
        "ভুল ট্রান্সক্রিপশন"
    ]
    
    references = [
        "এটি একটি পরীক্ষা।",
        "আমি বাংলায় কথা বলি।",
        "সঠিক ট্রান্সক্রিপশন"
    ]
    
    # Compute metrics
    metrics_calc = SpeechRecognitionMetrics()
    
    print("CER Metrics:")
    cer_metrics = metrics_calc.compute_cer(predictions, references)
    for key, value in cer_metrics.items():
        if key != 'per_utterance_cer':
            print(f"  {key}: {value:.4f}")
    
    print("\nWER Metrics:")
    wer_metrics = metrics_calc.compute_wer(predictions, references)
    for key, value in wer_metrics.items():
        if key != 'per_utterance_wer':
            print(f"  {key}: {value:.4f}")
    
    print("\nAll Metrics:")
    all_metrics = metrics_calc.compute_all_metrics(predictions, references)
    for key, value in all_metrics.items():
        if not key.startswith('per_utterance'):
            print(f"  {key}: {value:.4f}")
    
    print("Metrics test completed!")
