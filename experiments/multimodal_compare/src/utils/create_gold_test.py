#!/usr/bin/env python3
"""
Script to create a balanced gold test set from experiment data.
Distributes 100 samples equally across all unique YouTube IDs in experiment_data.

Usage:
python experiments/multimodal_compare/src/utils/create_gold_test.py \
  --experiment_data_dir experiments/experiment_data \
  --manifest_csv experiments/multimodal_compare/manifests/manifest.csv \
  --out_csv experiments/multimodal_compare/manifests/test_gold.csv \
  --max_samples 100
"""

import os
import csv
import argparse
import random
from pathlib import Path
from collections import defaultdict


def get_unique_videos_from_experiment_data(experiment_data_dir):
    """Get list of unique YouTube IDs from experiment_data directory"""
    experiment_data_dir = Path(experiment_data_dir)
    
    if not experiment_data_dir.exists():
        print(f"Error: Directory {experiment_data_dir} does not exist")
        return []
    
    # Find all YouTube ID directories
    yt_dirs = [d.name for d in experiment_data_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
    
    print(f"Found {len(yt_dirs)} unique YouTube IDs in experiment_data:")
    for yt_id in sorted(yt_dirs):
        print(f"  - {yt_id}")
    
    return sorted(yt_dirs)


def load_manifest(manifest_csv):
    """Load manifest CSV and return rows grouped by yt_id"""
    if not os.path.exists(manifest_csv):
        print(f"Error: Manifest file {manifest_csv} does not exist")
        return {}
    
    yt_groups = defaultdict(list)
    total_rows = 0
    
    with open(manifest_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['utt_id']:  # Skip empty rows
                yt_groups[row['yt_id']].append(row)
                total_rows += 1
    
    print(f"\nLoaded {total_rows} total samples from manifest:")
    for yt_id in sorted(yt_groups.keys()):
        rows = yt_groups[yt_id]
        splits = defaultdict(int)
        for row in rows:
            splits[row['split']] += 1
        
        split_info = ", ".join([f"{split}: {count}" for split, count in splits.items()])
        print(f"  {yt_id}: {len(rows)} samples ({split_info})")
    
    return yt_groups


def create_balanced_gold_test(yt_groups, unique_yt_ids, max_samples=100, seed=42):
    """Create balanced gold test set across all YouTube IDs"""
    random.seed(seed)
    
    # Calculate samples per YouTube ID
    num_videos = len(unique_yt_ids)
    base_samples_per_video = max_samples // num_videos
    extra_samples = max_samples % num_videos
    
    print(f"\nDistributing {max_samples} samples across {num_videos} videos:")
    print(f"  Base samples per video: {base_samples_per_video}")
    print(f"  Extra samples to distribute: {extra_samples}")
    
    gold_samples = []
    
    for i, yt_id in enumerate(unique_yt_ids):
        # Calculate how many samples this video should get
        samples_for_this_video = base_samples_per_video
        if i < extra_samples:  # Distribute extra samples to first few videos
            samples_for_this_video += 1
        
        if yt_id not in yt_groups:
            print(f"  Warning: {yt_id} not found in manifest, skipping")
            continue
        
        available_rows = yt_groups[yt_id]
        
        # Prioritize test split, then val, then train
        test_rows = [row for row in available_rows if row['split'] == 'test']
        val_rows = [row for row in available_rows if row['split'] == 'val']
        train_rows = [row for row in available_rows if row['split'] == 'train']
        
        # Select samples in order of preference
        selected_rows = []
        
        # First, take from test split
        if test_rows:
            selected_from_test = min(len(test_rows), samples_for_this_video)
            selected_rows.extend(random.sample(test_rows, selected_from_test))
        
        # Then from val split if we need more
        remaining_needed = samples_for_this_video - len(selected_rows)
        if remaining_needed > 0 and val_rows:
            selected_from_val = min(len(val_rows), remaining_needed)
            selected_rows.extend(random.sample(val_rows, selected_from_val))
        
        # Finally from train split if we still need more
        remaining_needed = samples_for_this_video - len(selected_rows)
        if remaining_needed > 0 and train_rows:
            selected_from_train = min(len(train_rows), remaining_needed)
            selected_rows.extend(random.sample(train_rows, selected_from_train))
        
        # Add to gold samples
        for row in selected_rows:
            # Choose better transcript (prefer non-empty, longer text)
            google_txt = row.get('google_txt', '').strip()
            whisper_txt = row.get('whisper_txt', '').strip()
            
            # Use the longer non-empty transcript as base, or google as fallback
            if len(whisper_txt) > len(google_txt) and whisper_txt:
                base_txt = whisper_txt
            elif google_txt:
                base_txt = google_txt
            elif whisper_txt:
                base_txt = whisper_txt
            else:
                base_txt = ""
            
            gold_samples.append({
                'utt_id': row['utt_id'],
                'yt_id': row['yt_id'],
                'split': row['split'],
                'base_txt': base_txt,
                'google_txt': google_txt,
                'whisper_txt': whisper_txt,
                'gold_txt': ""  # To be filled manually
            })
        
        print(f"  {yt_id}: Selected {len(selected_rows)} samples (wanted {samples_for_this_video})")
        if len(selected_rows) < samples_for_this_video:
            print(f"    Warning: Only {len(available_rows)} total samples available")
    
    return gold_samples


def save_gold_test_csv(gold_samples, out_csv):
    """Save gold test samples to CSV"""
    # Sort by yt_id then utt_id for consistent ordering
    gold_samples.sort(key=lambda x: (x['yt_id'], x['utt_id']))
    
    fieldnames = ['utt_id', 'yt_id', 'split', 'base_txt', 'google_txt', 'whisper_txt', 'gold_txt']
    
    with open(out_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(gold_samples)
    
    print(f"\nSaved {len(gold_samples)} gold test samples to {out_csv}")
    
    # Print summary
    yt_counts = defaultdict(int)
    split_counts = defaultdict(int)
    for sample in gold_samples:
        yt_counts[sample['yt_id']] += 1
        split_counts[sample['split']] += 1
    
    print("\nFinal distribution:")
    print("By YouTube ID:")
    for yt_id, count in sorted(yt_counts.items()):
        print(f"  {yt_id}: {count} samples")
    
    print("By original split:")
    for split, count in sorted(split_counts.items()):
        print(f"  {split}: {count} samples")


def main():
    parser = argparse.ArgumentParser(description="Create balanced gold test set from experiment data")
    parser.add_argument("--experiment_data_dir", required=True,
                       help="Path to experiment data directory")
    parser.add_argument("--manifest_csv", required=True,
                       help="Path to manifest CSV file")
    parser.add_argument("--out_csv", required=True,
                       help="Output path for gold test CSV")
    parser.add_argument("--max_samples", type=int, default=100,
                       help="Maximum number of gold test samples (default: 100)")
    parser.add_argument("--seed", type=int, default=42,
                       help="Random seed for reproducible sampling (default: 42)")
    
    args = parser.parse_args()
    
    # Get unique videos from experiment_data
    unique_yt_ids = get_unique_videos_from_experiment_data(args.experiment_data_dir)
    
    if not unique_yt_ids:
        print("No unique videos found in experiment_data directory")
        return
    
    # Load manifest
    yt_groups = load_manifest(args.manifest_csv)
    
    if not yt_groups:
        print("No data loaded from manifest")
        return
    
    # Create balanced gold test set
    gold_samples = create_balanced_gold_test(yt_groups, unique_yt_ids, args.max_samples, args.seed)
    
    if not gold_samples:
        print("No gold samples created")
        return
    
    # Save to CSV
    save_gold_test_csv(gold_samples, args.out_csv)


if __name__ == "__main__":
    main()
