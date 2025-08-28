"""
Bengali Text Normalization Utility

This module provides functions for normalizing Bengali text to ensure consistency
across transcripts and evaluation metrics.

Author: Audio-Visual Speech Recognition Team
Date: August 2025
"""

import unicodedata
import re
from typing import Optional


class BengaliTextNormalizer:
    """Bengali text normalization with configurable options."""
    
    def __init__(
        self,
        normalize_unicode: bool = True,
        collapse_whitespace: bool = True,
        normalize_punctuation: bool = True,
        digit_mode: str = "keep_original",  # "keep_original", "to_bengali", "to_latin"
        remove_special_chars: bool = False,
        lowercase: bool = False
    ):
        """
        Initialize the normalizer with configuration options.
        
        Args:
            normalize_unicode: Apply NFC Unicode normalization
            collapse_whitespace: Collapse multiple whitespace to single space
            normalize_punctuation: Normalize punctuation variants
            digit_mode: How to handle digits - "keep_original", "to_bengali", "to_latin"
            remove_special_chars: Remove special characters except basic punctuation
            lowercase: Convert to lowercase (mainly for Latin characters)
        """
        self.normalize_unicode = normalize_unicode
        self.collapse_whitespace = collapse_whitespace
        self.normalize_punctuation = normalize_punctuation
        self.digit_mode = digit_mode
        self.remove_special_chars = remove_special_chars
        self.lowercase = lowercase
        
        # Bengali to Latin digit mapping
        self.bengali_to_latin = {
            '০': '0', '১': '1', '২': '2', '৩': '3', '৪': '4',
            '৫': '5', '৬': '6', '৭': '7', '৮': '8', '৯': '9'
        }
        
        # Latin to Bengali digit mapping
        self.latin_to_bengali = {v: k for k, v in self.bengali_to_latin.items()}
        
        # Common punctuation variants to normalize
        self.punct_variants = {
            # Different types of quotes
            '"': '"', '"': '"', ''': "'", ''': "'",
            # Different types of dashes
            '–': '-', '—': '-', '―': '-',
            # Different ellipsis
            '…': '...',
            # Different brackets
            '（': '(', '）': ')',
            '［': '[', '］': ']',
            '｛': '{', '｝': '}',
        }
    
    def _normalize_unicode(self, text: str) -> str:
        """Apply NFC Unicode normalization."""
        return unicodedata.normalize('NFC', text)
    
    def _collapse_whitespace(self, text: str) -> str:
        """Collapse multiple whitespace characters to single space."""
        # Replace all whitespace variants with regular space
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _normalize_punctuation_variants(self, text: str) -> str:
        """Normalize punctuation variants."""
        for variant, standard in self.punct_variants.items():
            text = text.replace(variant, standard)
        return text
    
    def _convert_digits(self, text: str, mode: str) -> str:
        """Convert digits between Bengali and Latin numerals."""
        if mode == "to_bengali":
            for latin, bengali in self.latin_to_bengali.items():
                text = text.replace(latin, bengali)
        elif mode == "to_latin":
            for bengali, latin in self.bengali_to_latin.items():
                text = text.replace(bengali, latin)
        # "keep_original" does nothing
        return text
    
    def _remove_special_characters(self, text: str) -> str:
        """Remove special characters, keeping only letters, digits, and basic punctuation."""
        # Keep Bengali characters, Latin letters, digits, and basic punctuation
        pattern = r'[^\u0980-\u09FF\u0900-\u097Fa-zA-Z0-9\s।,.!?;:()\[\]{}"\'/-]'
        return re.sub(pattern, '', text)
    
    def normalize(self, text: str) -> str:
        """
        Apply all normalization steps based on configuration.
        
        Args:
            text: Input Bengali text to normalize
            
        Returns:
            Normalized text
        """
        if not text or not isinstance(text, str):
            return ""
        
        # Step 1: Unicode normalization
        if self.normalize_unicode:
            text = self._normalize_unicode(text)
        
        # Step 2: Lowercase (before other processing)
        if self.lowercase:
            text = text.lower()
        
        # Step 3: Punctuation normalization
        if self.normalize_punctuation:
            text = self._normalize_punctuation_variants(text)
        
        # Step 4: Digit conversion
        if self.digit_mode != "keep_original":
            text = self._convert_digits(text, self.digit_mode)
        
        # Step 5: Remove special characters
        if self.remove_special_chars:
            text = self._remove_special_characters(text)
        
        # Step 6: Whitespace normalization (last to clean up)
        if self.collapse_whitespace:
            text = self._collapse_whitespace(text)
        
        return text
    
    def normalize_batch(self, texts: list) -> list:
        """Normalize a batch of texts."""
        return [self.normalize(text) for text in texts]


# Predefined normalizers for common use cases
def create_standard_normalizer() -> BengaliTextNormalizer:
    """Create a standard normalizer for general use."""
    return BengaliTextNormalizer(
        normalize_unicode=True,
        collapse_whitespace=True,
        normalize_punctuation=True,
        digit_mode="keep_original",
        remove_special_chars=False,
        lowercase=False
    )


def create_evaluation_normalizer() -> BengaliTextNormalizer:
    """Create a normalizer for evaluation (more aggressive)."""
    return BengaliTextNormalizer(
        normalize_unicode=True,
        collapse_whitespace=True,
        normalize_punctuation=True,
        digit_mode="to_latin",  # Standardize digits for evaluation
        remove_special_chars=True,
        lowercase=True
    )


def create_training_normalizer() -> BengaliTextNormalizer:
    """Create a normalizer for training data preparation."""
    return BengaliTextNormalizer(
        normalize_unicode=True,
        collapse_whitespace=True,
        normalize_punctuation=True,
        digit_mode="to_bengali",  # Keep Bengali digits for training
        remove_special_chars=False,
        lowercase=False
    )


# Convenience functions
def normalize_text(
    text: str,
    mode: str = "standard"
) -> str:
    """
    Normalize text using predefined configurations.
    
    Args:
        text: Input text to normalize
        mode: Normalization mode - "standard", "evaluation", or "training"
        
    Returns:
        Normalized text
    """
    if mode == "standard":
        normalizer = create_standard_normalizer()
    elif mode == "evaluation":
        normalizer = create_evaluation_normalizer()
    elif mode == "training":
        normalizer = create_training_normalizer()
    else:
        raise ValueError(f"Unknown mode: {mode}")
    
    return normalizer.normalize(text)


def normalize_batch(
    texts: list,
    mode: str = "standard"
) -> list:
    """
    Normalize a batch of texts.
    
    Args:
        texts: List of texts to normalize
        mode: Normalization mode - "standard", "evaluation", or "training"
        
    Returns:
        List of normalized texts
    """
    if mode == "standard":
        normalizer = create_standard_normalizer()
    elif mode == "evaluation":
        normalizer = create_evaluation_normalizer()
    elif mode == "training":
        normalizer = create_training_normalizer()
    else:
        raise ValueError(f"Unknown mode: {mode}")
    
    return normalizer.normalize_batch(texts)


if __name__ == "__main__":
    # Example usage
    test_texts = [
        "আমি   খুব   ভালো   আছি।",  # Multiple spaces
        'তিনি বলেছেন "হ্যাঁ"।',      # Quote variants
        "৫টি আপেল এবং 3টি কমলা।",   # Mixed digits
        "এটি—একটি পরীক্ষা।",        # Dash variant
    ]
    
    print("Original texts:")
    for i, text in enumerate(test_texts, 1):
        print(f"{i}. {text}")
    
    print("\\nStandard normalization:")
    standard_norm = normalize_batch(test_texts, "standard")
    for i, text in enumerate(standard_norm, 1):
        print(f"{i}. {text}")
    
    print("\\nEvaluation normalization:")
    eval_norm = normalize_batch(test_texts, "evaluation")
    for i, text in enumerate(eval_norm, 1):
        print(f"{i}. {text}")
    
    print("\\nTraining normalization:")
    train_norm = normalize_batch(test_texts, "training")
    for i, text in enumerate(train_norm, 1):
        print(f"{i}. {text}")
