# utils/slice_video_by_silence.py
from pydub import AudioSegment, silence
from moviepy.editor import VideoFileClip
import os

def split_video_by_silence(video_path, output_dir, min_silence_len=700, silence_thresh=-40):
    os.makedirs(output_dir, exist_ok=True)

    # Extract audio and convert to wav
    video = VideoFileClip(video_path)
    audio = video.audio
    audio_path = os.path.join(output_dir, "temp_audio.wav")
    audio.write_audiofile(audio_path, fps=16000, nbytes=2, codec="pcm_s16le")

    # Load with pydub
    audio_seg = AudioSegment.from_wav(audio_path)
    chunks = silence.split_on_silence(audio_seg, min_silence_len=min_silence_len, silence_thresh=silence_thresh)

    timestamps = []
    cursor = 0
    for i, chunk in enumerate(chunks):
        start = cursor
        end = start + len(chunk)
        timestamps.append((start / 1000, end / 1000))  # convert to seconds
        cursor = end

    # Slice video using moviepy
    for idx, (start, end) in enumerate(timestamps):
        subclip = video.subclip(start, end)
        out_path = os.path.join(output_dir, f"chunk_{idx:03d}.mp4")
        subclip.write_videofile(out_path, codec="libx264", audio_codec="aac", verbose=False, logger=None)

    print(f"✅ Sliced {len(timestamps)} video segments into: {output_dir}")
    return timestamps