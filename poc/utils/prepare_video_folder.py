from moviepy.editor import VideoFileClip
import os
import json

def prepare_video_dir(video_path, video_id, output_root="outputs"):
    os.makedirs(output_root, exist_ok=True)
    base_path = os.path.join(output_root, video_id)
    os.makedirs(base_path, exist_ok=True)

    # Copy/rename the video
    video_out_path = os.path.join(base_path, "video.mp4")
    if video_path != video_out_path:
        os.system(f'cp "{video_path}" "{video_out_path}"')

    # Extract audio
    video = VideoFileClip(video_out_path)
    audio_path = os.path.join(base_path, "video.wav")
    video.audio.write_audiofile(audio_path, fps=16000, nbytes=2, codec="pcm_s16le")

    # Write metadata
    metadata = {
        "video_id": video_id,
        "duration": video.duration,
        "fps": video.fps,
        "size": video.size,
    }
    with open(os.path.join(base_path, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=4)

    return base_path, video_out_path, audio_path



def is_video_already_processed(video_id, output_dir):
    log_path = os.path.join(output_dir, "processed.json")
    if not os.path.exists(log_path):
        return False

    with open(log_path, "r") as f:
        processed_log = json.load(f)
    return video_id in processed_log


def mark_video_as_processed(video_id, metadata, output_dir):
    log_path = os.path.join(output_dir, "processed.json")

    # ✅ Ensure directory exists
    os.makedirs(output_dir, exist_ok=True)

    if os.path.exists(log_path):
        with open(log_path, "r") as f:
            processed = json.load(f)
    else:
        processed = {}

    processed[video_id] = metadata

    with open(log_path, "w") as f:
        json.dump(processed, f, indent=2)