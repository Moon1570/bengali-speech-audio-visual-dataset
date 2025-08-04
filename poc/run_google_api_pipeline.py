# run_pipeline.py

import os
import json
import argparse


from utils.slice_video_by_silence import split_video_by_silence
from utils.transcribe_chunks import transcribe_chunks
from utils.prepare_video_folder import prepare_video_dir
from utils.split_by_silence import split_into_chunks
from utils.prepare_video_folder import is_video_already_processed, mark_video_as_processed
from utils.transcribe_chunks_google import transcribe_chunks_google

def main():
    # CLI Argument Parser
    parser = argparse.ArgumentParser(description="Process video by splitting into chunks and transcribing.")
    parser.add_argument("video_path", type=str, help="Path to the video file")
    parser.add_argument("--output_root", type=str, default="outputs", help="Directory for output files")
    parser.add_argument("--transcribe", action="store_true", help="Enable transcription step")
    args = parser.parse_args()

    video_path = args.video_path
    video_id = os.path.splitext(os.path.basename(video_path))[0]

    # Check if already processed
    if is_video_already_processed(video_id, args.output_root):
        print(f"✅ {video_id} already processed. Skipping.")
        return

    # Step 1: Setup folder & extract audio
    base_dir, video_out, audio_out = prepare_video_dir(video_path, video_id)

    # Step 2: Silence-based splitting
    timestamps = split_into_chunks(video_out, audio_out, base_dir)

    # Step 3: Optional transcription
    if args.transcribe:
        chunks_dir = os.path.join(base_dir, "chunks")
        print("🔍 Starting transcription using Google API...")
        transcribe_chunks_google(chunks_dir)

    # Step 4: Mark as processed
    metadata = {
        "video_id": video_id,
        "chunks": len(timestamps),
        "timestamps": timestamps
    }
    mark_video_as_processed(video_id, metadata, args.output_root)
    print(f"✅ {video_id} processed and logged.")


if __name__ == "__main__":
    main()