#!/usr/bin/env python3
"""
Reorganize Transcripts - Move transcript files to proper folder structure
==========================================================================

This script moves transcript files from video_normal/ directory into 
a separate transcripts_google/ or transcripts_whisper/ folder at the 
parent level.

Usage:
    python reorganize_transcripts.py <experiment_data_dir> [--model google|whisper]
    
Example:
    python reorganize_transcripts.py experiments/experiment_data/SSYouTubeonline
    python reorganize_transcripts.py experiments/experiment_data/SSYouTubeonline --model google
"""

import os
import sys
import shutil
import argparse
from pathlib import Path


def reorganize_transcripts(experiment_dir, model='google'):
    """
    Reorganize transcript files from video directories to transcripts folder.
    
    Args:
        experiment_dir: Path to experiment data directory (e.g., experiments/experiment_data/SSYouTubeonline)
        model: Model name ('google' or 'whisper')
    """
    print(f"🔄 Reorganizing {model} transcripts in: {experiment_dir}")
    
    # Check if experiment directory exists
    if not os.path.exists(experiment_dir):
        print(f"❌ Error: Directory not found: {experiment_dir}")
        return False
    
    # Define source and target directories
    video_dirs = ['video_normal', 'video_cropped', 'video_bbox']
    transcript_dir = os.path.join(experiment_dir, f"transcripts_{model}")
    
    # Create transcripts directory
    os.makedirs(transcript_dir, exist_ok=True)
    print(f"📁 Created directory: {transcript_dir}")
    
    total_moved = 0
    total_summary_moved = 0
    
    for video_subdir in video_dirs:
        video_path = os.path.join(experiment_dir, video_subdir)
        
        if not os.path.exists(video_path):
            continue
        
        print(f"\n📂 Processing: {video_subdir}/")
        
        # Find all transcript files (.txt files, excluding summary files)
        txt_files = []
        summary_files = []
        
        for file in os.listdir(video_path):
            if file.endswith('.txt'):
                if f'_{model}_summary.txt' in file:
                    summary_files.append(file)
                elif not file.endswith('_summary.txt'):  # Skip any summary files
                    txt_files.append(file)
        
        if not txt_files and not summary_files:
            print(f"   ℹ️  No transcript files found")
            continue
        
        # Move transcript files
        moved_count = 0
        for txt_file in txt_files:
            src_path = os.path.join(video_path, txt_file)
            dst_path = os.path.join(transcript_dir, txt_file)
            
            try:
                shutil.move(src_path, dst_path)
                moved_count += 1
            except Exception as e:
                print(f"   ⚠️  Error moving {txt_file}: {e}")
        
        if moved_count > 0:
            print(f"   ✅ Moved {moved_count} transcript files to transcripts_{model}/")
            total_moved += moved_count
        
        # Handle summary files - keep them in video_normal for reference
        if summary_files:
            print(f"   📋 Kept {len(summary_files)} summary files in {video_subdir}/")
    
    print(f"\n{'='*60}")
    print(f"✅ Reorganization complete!")
    print(f"   Total transcript files moved: {total_moved}")
    print(f"   Target directory: {transcript_dir}")
    print(f"{'='*60}")
    
    return total_moved > 0


def main():
    parser = argparse.ArgumentParser(
        description="Reorganize transcript files into proper folder structure",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Reorganize Google transcripts
  python reorganize_transcripts.py experiments/experiment_data/SSYouTubeonline --model google
  
  # Reorganize Whisper transcripts
  python reorganize_transcripts.py experiments/experiment_data/SSYouTubeonline --model whisper
  
  # Process all experiment directories
  for dir in experiments/experiment_data/*/; do
    python reorganize_transcripts.py "$dir" --model google
  done
        """
    )
    
    parser.add_argument(
        'experiment_dir',
        type=str,
        help='Path to experiment data directory'
    )
    
    parser.add_argument(
        '--model',
        choices=['google', 'whisper', 'both'],
        default='google',
        help='Transcription model (default: google)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without actually moving files'
    )
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No files will be moved")
        print()
    
    # Process based on model selection
    models_to_process = ['google', 'whisper'] if args.model == 'both' else [args.model]
    
    success = True
    for model in models_to_process:
        if args.dry_run:
            # In dry run, just list what would be done
            print(f"Would reorganize {model} transcripts in: {args.experiment_dir}")
            video_dirs = ['video_normal', 'video_cropped', 'video_bbox']
            for video_subdir in video_dirs:
                video_path = os.path.join(args.experiment_dir, video_subdir)
                if os.path.exists(video_path):
                    txt_files = [f for f in os.listdir(video_path) 
                                if f.endswith('.txt') and f'_{model}_summary.txt' not in f 
                                and not f.endswith('_summary.txt')]
                    if txt_files:
                        print(f"   Would move {len(txt_files)} files from {video_subdir}/")
        else:
            result = reorganize_transcripts(args.experiment_dir, model)
            success = success and result
        
        if len(models_to_process) > 1:
            print()  # Blank line between models
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
