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


"""


import os
import csv
import json
import argparse
import random
from pathlib import Path

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
            "whisper_txt": whisper_data.get(utt_id, "")
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
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio_dir", required=True)
    parser.add_argument("--video_normal_dir", required=True)
    parser.add_argument("--video_bbox_dir", required=True)
    parser.add_argument("--video_cropped_dir", required=True)
    parser.add_argument("--google_json", default=None)
    parser.add_argument("--whisper_json", default=None)
    parser.add_argument("--out_csv", required=True)
    args = parser.parse_args()

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
