"""
Usage: 

python experiments/multimodal_compare/src/utils/prepare_manifest.py \
  --audio_dir data/audio \
  --video_normal_dir data/video_normal \
  --video_bbox_dir data/video_bbox \
  --video_cropped_dir data/video_cropped \
  --google_json data/google_transcripts.json \
  --whisper_json data/whisper_transcripts.json \
  --out_csv experiments/multimodal_compare/manifests/manifest.csv

Or to add experiment data:

python experiments/multimodal_compare/src/utils/prepare_manifest.py \
  --experiment_data_dir experiments/experiment_data \
  --yt_id h9OrOkhODmY \
  --out_csv experiments/multimodal_compare/manifests/manifest.csv


"""


import os
import csv
import json
import argparse
import random
from pathlib import Path

def read_existing_manifest(csv_path):
    """Read existing manifest CSV and return set of processed utt_ids"""
    if not os.path.exists(csv_path):
        return set()
    
    processed_ids = set()
    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["utt_id"]:  # Skip empty rows
                processed_ids.add(row["utt_id"])
    return processed_ids

def read_text_file(file_path):
    """Read text content from file"""
    if not os.path.exists(file_path):
        return ""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read().strip()

def add_experiment_data(experiment_data_dir, yt_id, out_csv):
    """Add data from experiment_data directory to the manifest"""
    experiment_data_dir = Path(experiment_data_dir)
    yt_dir = experiment_data_dir / yt_id
    
    if not yt_dir.exists():
        print(f"Error: Directory {yt_dir} does not exist")
        return
    
    # Read existing manifest to check for already processed IDs
    processed_ids = read_existing_manifest(out_csv)
    
    # Define expected subdirectories
    audio_dir = yt_dir / "audio"
    video_normal_dir = yt_dir / "video_normal"
    video_bbox_dir = yt_dir / "video_bbox"
    video_cropped_dir = yt_dir / "video_cropped"
    transcripts_google_dir = yt_dir / "transcripts_google"
    transcripts_whisper_dir = yt_dir / "transcripts_whisper"
    
    rows = []
    existing_rows = []
    
    # Read existing data if file exists
    if os.path.exists(out_csv):
        with open(out_csv, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            existing_rows = [row for row in reader if row["utt_id"]]  # Skip empty rows
    
    # Process audio files
    if audio_dir.exists():
        for wav_file in audio_dir.glob("*.wav"):
            utt_id = wav_file.stem
            
            # Skip if already processed
            if utt_id in processed_ids:
                print(f"Skipping {utt_id} - already processed")
                continue
            
            # Extract chunk_id from utt_id (e.g., h9OrOkhODmY_chunk_000 -> chunk_000)
            parts = utt_id.split("_")
            if len(parts) >= 3 and parts[0] == yt_id:
                chunk_id = "_".join(parts[1:])
            else:
                chunk_id = utt_id.replace(f"{yt_id}_", "")
            
            # Build paths and check existence
            video_normal_path = video_normal_dir / f"{utt_id}.mp4"
            video_bbox_path = video_bbox_dir / f"{utt_id}_with_bboxes.mp4"
            video_cropped_path = video_cropped_dir / f"{utt_id}.mp4"
            google_txt_path = transcripts_google_dir / f"{utt_id}.txt"
            whisper_txt_path = transcripts_whisper_dir / f"{utt_id}.txt"
            
            # Read transcript content
            google_txt = read_text_file(google_txt_path)
            whisper_txt = read_text_file(whisper_txt_path)
            
            row = {
                "utt_id": utt_id,
                "yt_id": yt_id,
                "chunk_id": chunk_id,
                "audio_path": str(wav_file),
                "video_normal_path": str(video_normal_path) if video_normal_path.exists() else "",
                "video_bbox_path": str(video_bbox_path) if video_bbox_path.exists() else "",
                "video_cropped_path": str(video_cropped_path) if video_cropped_path.exists() else "",
                "google_txt": google_txt,
                "whisper_txt": whisper_txt,
                "split": "",  # Will be assigned later
                "poi": ""     # Point of interest - empty for now
            }
            rows.append(row)
    
    if not rows:
        print(f"No new data found for {yt_id}")
        return
    
    # Combine existing and new rows
    all_rows = existing_rows + rows
    
    # Assign splits if there are new rows
    if rows:
        # Group by yt_id for split assignment
        yt_ids = list(set([r["yt_id"] for r in all_rows]))
        random.seed(42)  # For reproducible splits
        random.shuffle(yt_ids)
        n = len(yt_ids)
        train_ids = set(yt_ids[:int(0.8*n)])
        val_ids = set(yt_ids[int(0.8*n):int(0.9*n)])
        test_ids = set(yt_ids[int(0.9*n):])
        
        for r in all_rows:
            if not r["split"]:  # Only assign split if not already assigned
                if r["yt_id"] in train_ids:
                    r["split"] = "train"
                elif r["yt_id"] in val_ids:
                    r["split"] = "val"
                else:
                    r["split"] = "test"
    
    # Write updated CSV
    fieldnames = ["utt_id", "yt_id", "chunk_id", "audio_path", "video_normal_path", 
                  "video_bbox_path", "video_cropped_path", "google_txt", "whisper_txt", "split", "poi"]
    
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(all_rows)
    
    print(f"Added {len(rows)} new entries for {yt_id} to {out_csv}")

def build_manifest(audio_dir, video_dirs, google_json, whisper_json, out_csv, seed=42):
    random.seed(seed)
    
    audio_dir = Path(audio_dir)
    video_dirs = {k: Path(v) for k,v in video_dirs.items()}
    
    # Load transcripts if available
    google_data = json.load(open(google_json)) if google_json else {}
    whisper_data = json.load(open(whisper_json)) if whisper_json else {}
    
    rows = []
    for wav in audio_dir.glob("*.wav"):
        utt_id = wav.stem  # yt123_chunk_0
        yt_id = utt_id.split("_")[0]
        chunk_id = "_".join(utt_id.split("_")[1:])
        
        row = {
            "utt_id": utt_id,
            "yt_id": yt_id,
            "chunk_id": chunk_id,
            "audio_path": str(wav),
            "video_normal_path": str(video_dirs["normal"] / f"{utt_id}.mp4") if (video_dirs["normal"] / f"{utt_id}.mp4").exists() else "",
            "video_bbox_path": str(video_dirs["bbox"] / f"{utt_id}.mp4") if (video_dirs["bbox"] / f"{utt_id}.mp4").exists() else "",
            "video_cropped_path": str(video_dirs["cropped"] / f"{utt_id}.mp4") if (video_dirs["cropped"] / f"{utt_id}.mp4").exists() else "",
            "google_txt": google_data.get(utt_id, ""),
            "whisper_txt": whisper_data.get(utt_id, ""),
            "split": "",  # Will be assigned later
            "poi": ""     # Point of interest - empty for now
        }
        rows.append(row)
    
    # Group by yt_id for split
    yt_ids = list(set([r["yt_id"] for r in rows]))
    random.shuffle(yt_ids)
    n = len(yt_ids)
    train_ids = set(yt_ids[:int(0.8*n)])
    val_ids   = set(yt_ids[int(0.8*n):int(0.9*n)])
    test_ids  = set(yt_ids[int(0.9*n):])
    
    for r in rows:
        if r["yt_id"] in train_ids:
            r["split"] = "train"
        elif r["yt_id"] in val_ids:
            r["split"] = "val"
        else:
            r["split"] = "test"
    
    # Write CSV
    fieldnames = ["utt_id", "yt_id", "chunk_id", "audio_path", "video_normal_path", 
                  "video_bbox_path", "video_cropped_path", "google_txt", "whisper_txt", "split", "poi"]
    
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio_dir", default=None)
    parser.add_argument("--video_normal_dir", default=None)
    parser.add_argument("--video_bbox_dir", default=None)
    parser.add_argument("--video_cropped_dir", default=None)
    parser.add_argument("--google_json", default=None)
    parser.add_argument("--whisper_json", default=None)
    parser.add_argument("--out_csv", required=True)
    
    # New arguments for experiment data
    parser.add_argument("--experiment_data_dir", default=None, 
                       help="Path to experiment data directory")
    parser.add_argument("--yt_id", default=None,
                       help="YouTube ID to process from experiment data")
    
    args = parser.parse_args()

    if args.experiment_data_dir and args.yt_id:
        # Process experiment data
        add_experiment_data(args.experiment_data_dir, args.yt_id, args.out_csv)
    elif args.audio_dir:
        # Original manifest building
        if not all([args.video_normal_dir, args.video_bbox_dir, args.video_cropped_dir]):
            parser.error("When using --audio_dir, all video directories must be specified")
        
        build_manifest(
            args.audio_dir,
            {
                "normal": args.video_normal_dir,
                "bbox": args.video_bbox_dir,
                "cropped": args.video_cropped_dir,
            },
            args.google_json,
            args.whisper_json,
            args.out_csv
        )
    else:
        parser.error("Either provide --audio_dir with video directories, or --experiment_data_dir with --yt_id")
