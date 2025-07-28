# run_pipeline.py
from utils.slice_video_by_silence import split_video_by_silence
from utils.transcribe_chunks import transcribe_chunks
import os
from utils.prepare_video_folder import prepare_video_dir
from utils.split_by_silence import split_into_chunks


video_path = "downloads/aRHpoSebPPI.mp4"
video_id = os.path.splitext(os.path.basename(video_path))[0]

# Step 1: Setup folder & extract audio
base_dir, video_out, audio_out = prepare_video_dir(video_path, video_id)

# Step 2: Silence-based splitting
timestamps = split_into_chunks(video_out, audio_out, base_dir)

# Step 3: Transcription
transcribe_chunks(os.path.join(base_dir, "chunks"))