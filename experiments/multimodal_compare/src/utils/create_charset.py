#!/usr/bin/env python3
"""
Script to generate charset file from train split transcripts.
Scans Google and Whisper transcripts to extract unique characters.

Usage:
python experiments/multimodal_compare/src/utils/create_charset.py \
  --manifest_csv experiments/multimodal_compare/manifests/manifest.csv \
  --out_charset experiments/multimodal_compare/manifests/charset.txt
"""

import csv
import argparse
import unicodedata
from collections import Counter


def normalize_text(text):
    """Apply basic normalization - NFC normalize and strip"""
    if not text:
        return ""
    # NFC normalize (canonical decomposition followed by canonical composition)
    normalized = unicodedata.normalize('NFC', text.strip())
    return normalized


def extract_characters_from_manifest(manifest_csv, splits=['train']):
    """Extract all unique characters from specified splits in manifest"""
    char_counter = Counter()
    total_transcripts = 0
    processed_transcripts = 0
    
    print(f"Extracting characters from splits: {', '.join(splits)}")
    
    with open(manifest_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            if not row['utt_id']:  # Skip empty rows
                continue
                
            if row['split'] not in splits:
                continue
                
            total_transcripts += 1
            
            # Process Google transcript
            google_txt = row.get('google_txt', '').strip()
            if google_txt:
                normalized_google = normalize_text(google_txt)
                for char in normalized_google:
                    char_counter[char] += 1
                processed_transcripts += 1
            
            # Process Whisper transcript  
            whisper_txt = row.get('whisper_txt', '').strip()
            if whisper_txt:
                normalized_whisper = normalize_text(whisper_txt)
                for char in normalized_whisper:
                    char_counter[char] += 1
                processed_transcripts += 1
    
    print(f"Processed {processed_transcripts} transcripts from {total_transcripts} total samples")
    return char_counter


def analyze_character_distribution(char_counter):
    """Analyze and categorize characters"""
    categories = {
        'bengali_letters': [],
        'bengali_digits': [],
        'bengali_marks': [],
        'latin_letters': [],
        'latin_digits': [],
        'punctuation': [],
        'whitespace': [],
        'other': []
    }
    
    for char, count in char_counter.most_common():
        unicode_name = unicodedata.name(char, f'UNKNOWN-{ord(char):04X}')
        category = unicodedata.category(char)
        
        if 'BENGALI' in unicode_name:
            if 'LETTER' in unicode_name:
                categories['bengali_letters'].append((char, count, unicode_name))
            elif 'DIGIT' in unicode_name:
                categories['bengali_digits'].append((char, count, unicode_name))
            elif category.startswith('M'):  # Marks (combining characters)
                categories['bengali_marks'].append((char, count, unicode_name))
            else:
                categories['other'].append((char, count, unicode_name))
        elif category == 'Ll' or category == 'Lu':  # Latin letters
            categories['latin_letters'].append((char, count, unicode_name))
        elif category == 'Nd' and ord(char) < 128:  # ASCII digits
            categories['latin_digits'].append((char, count, unicode_name))
        elif category.startswith('P'):  # Punctuation
            categories['punctuation'].append((char, count, unicode_name))
        elif category.startswith('Z'):  # Whitespace/separators
            categories['whitespace'].append((char, count, unicode_name))
        else:
            categories['other'].append((char, count, unicode_name))
    
    return categories


def save_charset(char_counter, out_charset, include_analysis=True):
    """Save charset to file with analysis"""
    
    # Get all unique characters sorted by frequency (most common first)
    unique_chars = [char for char, count in char_counter.most_common()]
    
    # Add space if not present (it should be)
    if ' ' not in unique_chars:
        unique_chars.insert(0, ' ')
    
    # Add CTC blank token (typically represented as <blank> or <ctc_blank>)
    charset_with_ctc = ['<blank>'] + unique_chars
    
    # Save to file
    with open(out_charset, 'w', encoding='utf-8') as f:
        for char in charset_with_ctc:
            f.write(char + '\n')
    
    print(f"\nSaved charset with {len(charset_with_ctc)} characters to {out_charset}")
    print(f"  - CTC blank token: <blank>")
    print(f"  - Unique characters: {len(unique_chars)}")
    
    if include_analysis:
        # Create analysis file
        analysis_file = out_charset.replace('.txt', '_analysis.txt')
        
        categories = analyze_character_distribution(char_counter)
        
        with open(analysis_file, 'w', encoding='utf-8') as f:
            f.write("CHARACTER SET ANALYSIS\n")
            f.write("=====================\n\n")
            
            f.write(f"Total unique characters: {len(unique_chars)}\n")
            f.write(f"Total character occurrences: {sum(char_counter.values())}\n\n")
            
            for category, chars in categories.items():
                if chars:
                    f.write(f"{category.upper().replace('_', ' ')} ({len(chars)} chars):\n")
                    f.write("-" * (len(category) + 10) + "\n")
                    for char, count, unicode_name in chars[:10]:  # Top 10 most frequent
                        if char == '\n':
                            f.write(f"  '\\n' (newline) -> {count:6d} times | {unicode_name}\n")
                        elif char == '\t':
                            f.write(f"  '\\t' (tab) -> {count:6d} times | {unicode_name}\n")
                        elif char == ' ':
                            f.write(f"  ' ' (space) -> {count:6d} times | {unicode_name}\n")
                        else:
                            f.write(f"  '{char}' -> {count:6d} times | {unicode_name}\n")
                    
                    if len(chars) > 10:
                        f.write(f"  ... and {len(chars) - 10} more\n")
                    f.write("\n")
        
        print(f"Saved character analysis to {analysis_file}")
        
        # Print summary
        print("\nCharacter distribution summary:")
        for category, chars in categories.items():
            if chars:
                total_count = sum(count for char, count, name in chars)
                print(f"  {category.replace('_', ' ').title()}: {len(chars)} chars ({total_count:,} occurrences)")


def main():
    parser = argparse.ArgumentParser(description="Generate charset file from manifest transcripts")
    parser.add_argument("--manifest_csv", required=True,
                       help="Path to manifest CSV file")
    parser.add_argument("--out_charset", required=True,
                       help="Output path for charset file")
    parser.add_argument("--splits", nargs='+', default=['train'],
                       help="Splits to include (default: train)")
    parser.add_argument("--no_analysis", action='store_true',
                       help="Skip character analysis file")
    
    args = parser.parse_args()
    
    # Extract characters from manifest
    char_counter = extract_characters_from_manifest(args.manifest_csv, args.splits)
    
    if not char_counter:
        print("No characters found in specified splits")
        return
    
    # Save charset
    save_charset(char_counter, args.out_charset, not args.no_analysis)
    
    print(f"\nCharset generation complete!")
    print(f"Use this charset file for CTC training with {len(char_counter) + 1} total tokens (including <blank>)")


if __name__ == "__main__":
    main()
