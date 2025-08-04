import os
import argparse

from utils.slice_video_by_silence import split_video_by_silence
from utils.transcribe_chunks import transcribe_chunks  # Whisper-based transcription
from utils.transcribe_chunks_google import transcribe_chunks_google
from utils.prepare_video_folder import prepare_video_dir
from utils.split_by_silence import split_into_chunks
from utils.prepare_video_folder import is_video_already_processed, mark_video_as_processed


def main():
    parser = argparse.ArgumentParser(description="Process a video: split into chunks, optionally transcribe.")
    parser.add_argument("video_path", type=str, help="Path to the video file")
    parser.add_argument("--output_root", type=str, default="outputs", help="Directory for outputs (default: outputs)")
    parser.add_argument("--transcribe", action="store_true", help="Enable transcription step")
    parser.add_argument("--model", choices=["whisper", "google"], default="whisper",
                        help="Transcription model to use (whisper or google)")
    
    args = parser.parse_args()

    video_path = args.video_path
    video_id = os.path.splitext(os.path.basename(video_path))[0]

    # Check if already processed
    if is_video_already_processed(video_id, args.output_root):
        print(f"✅ {video_id} already processed. Skipping.")
        return

    # Step 1: Setup folder & extract audio
    print("📂 Preparing video directory and extracting audio...")
    base_dir, video_out, audio_out = prepare_video_dir(video_path, video_id)

    # Step 2: Silence-based splitting
    print("🔍 Splitting video into chunks based on silence...")
    timestamps = split_into_chunks(video_out, audio_out, base_dir)
    print(f"✅ Split into {len(timestamps)} chunks.")

    # Step 3: Optional transcription
    if args.transcribe:
        chunks_dir = os.path.join(base_dir, "chunks")
        print(f"📝 Starting transcription using {args.model}...")
        if args.model == "google":
            transcribe_chunks_google(chunks_dir)
        else:
            transcribe_chunks(chunks_dir)
        print(f"✅ Transcription completed using {args.model}.")

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