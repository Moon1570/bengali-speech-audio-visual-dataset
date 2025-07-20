from pydub import AudioSegment
import moviepy.editor as mp
import os

def get_chunk_timestamps(full_audio_path, chunks_dir):
    full_audio = AudioSegment.from_wav(full_audio_path)
    chunk_files = sorted(f for f in os.listdir(chunks_dir) if f.endswith('.wav'))
    timestamps = []
    cursor = 0

    for chunk_file in chunk_files:
        chunk_path = os.path.join(chunks_dir, chunk_file)
        chunk = AudioSegment.from_wav(chunk_path)
        chunk_length = len(chunk)

        start_time = cursor
        end_time = cursor + chunk_length
        timestamps.append((start_time / 1000, end_time / 1000))  # in seconds
        cursor = end_time

    return timestamps

def cut_video_by_audio_chunks(video_path, timestamps, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    for i, (start, end) in enumerate(timestamps):
        out_path = os.path.join(output_dir, f"clip_{i:03d}.mp4")
        print(f"Cutting video from {start:.2f}s to {end:.2f}s -> {out_path}")

        with mp.VideoFileClip(video_path) as video:
            # Round for safety
            start = round(start, 3)
            end = round(end, 3)

            clip = video.subclip(start, end)
            # Force sync with original audio
            if video.audio:
                clip = clip.set_audio(video.audio.subclip(start, end))

            clip.write_videofile(
                out_path,
                codec="libx264",
                audio_codec="aac",
                fps=video.fps,
                verbose=False,
                logger=None
            )

if __name__ == "__main__":
    filename = "aRHpoSebPPI"
    chunks_dir = f"sentence_chunks/{filename}"
    full_audio_path = f"denoised_audio/{filename}.wav"
    video_path = f"downloads/{filename}.mp4"
    video_output_dir = f"video_chunks/{filename}"

    timestamps = get_chunk_timestamps(full_audio_path, chunks_dir)
    cut_video_by_audio_chunks(video_path, timestamps, video_output_dir)