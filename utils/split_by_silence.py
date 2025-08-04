from pydub import AudioSegment, silence
from moviepy.editor import VideoFileClip
import os

def split_into_chunks(video_path, audio_path, output_dir, min_silence_len=300, silence_thresh=None, max_chunk_len=10000):
    chunks_dir = os.path.join(output_dir, "chunks")
    os.makedirs(chunks_dir, exist_ok=True)
    video_out = os.path.join(chunks_dir, "video")
    audio_out = os.path.join(chunks_dir, "audio")
    os.makedirs(video_out, exist_ok=True)
    os.makedirs(audio_out, exist_ok=True)

    # Load audio
    audio_seg = AudioSegment.from_wav(audio_path)
    if silence_thresh is None:
        silence_thresh = audio_seg.dBFS - 16

    raw_chunks = silence.split_on_silence(
        audio_seg,
        min_silence_len=min_silence_len,
        silence_thresh=silence_thresh,
        keep_silence=150
    )

    # Enforce max_chunk_len (e.g., 10s)
    final_chunks = []
    for chunk in raw_chunks:
        if len(chunk) <= max_chunk_len:
            final_chunks.append(chunk)
        else:
            for i in range(0, len(chunk), max_chunk_len):
                final_chunks.append(chunk[i:i + max_chunk_len])

    # Save chunks and track timestamps
    timestamps = []
    cursor = 0
    for i, chunk in enumerate(final_chunks):
        start = cursor
        end = start + len(chunk)
        timestamps.append((start / 1000, end / 1000))
        cursor = end

        chunk.export(os.path.join(audio_out, f"chunk_{i:03d}.wav"), format="wav")

    # Slice video based on timestamps
    video = VideoFileClip(video_path)
    for i, (start, end) in enumerate(timestamps):
        subclip = video.subclip(start, end)
        subclip.write_videofile(os.path.join(video_out, f"chunk_{i:03d}.mp4"), codec="libx264", audio_codec="aac", verbose=False, logger=None)

    return timestamps