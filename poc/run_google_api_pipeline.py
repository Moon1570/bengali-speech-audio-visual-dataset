# run_pipeline.py

import os
import json

from utils.slice_video_by_silence import split_video_by_silence
from utils.transcribe_chunks import transcribe_chunks
from utils.prepare_video_folder import prepare_video_dir
from utils.split_by_silence import split_into_chunks
from utils.prepare_video_folder import is_video_already_processed, mark_video_as_processed
from utils.transcribe_chunks_google import transcribe_chunks_google

video_path = "downloads/aRHpoSebPPI.mp4"
#video_path = "downloads/fhvsdhvhiusu_g.mp4"  # Update this to your video file path
video_id = os.path.splitext(os.path.basename(video_path))[0]

# Set base output directory
output_root = "outputs"  # you can also derive this from prepare_video_dir if needed

if is_video_already_processed(video_id, output_root):
    print(f"✅ {video_id} already processed. Skipping.")
else:
    # Step 1: Setup folder & extract audio
    base_dir, video_out, audio_out = prepare_video_dir(video_path, video_id)

    # Step 2: Silence-based splitting
    timestamps = split_into_chunks(video_out, audio_out, base_dir)

    # Step 3: Transcription
    #transcribe_chunks_google(os.path.join(base_dir, "chunks"))

    # Step 4: Mark as processed
    metadata = {
        "video_id": video_id,
        "chunks": len(timestamps),
        "timestamps": timestamps
    }
    mark_video_as_processed(video_id, metadata, output_root)
    print(f"✅ {video_id} processed and logged.")