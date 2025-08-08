import os

import numpy as np
import noisereduce as nr
from moviepy.editor import VideoFileClip
from pydub import AudioSegment, silence

from .face_detection import filter_chunks_with_faces, save_face_detection_preview


def reduce_noise(audio_seg, noise_duration_ms=500):
    samples = np.array(audio_seg.get_array_of_samples(), dtype=float)
    sr = audio_seg.frame_rate
    noise_sample = samples[:int(sr * (noise_duration_ms / 1000))]
    reduced = nr.reduce_noise(y=samples, y_noise=noise_sample, sr=sr)
    return AudioSegment(
        reduced.astype(np.int16).tobytes(),
        frame_rate=sr,
        sample_width=audio_seg.sample_width,
        channels=audio_seg.channels,
    )

def dynamic_silence_thresh(audio_seg, percentile=5, frame_ms=20):
    samples = np.array(audio_seg.get_array_of_samples())
    samples = samples.astype(float)
    frame_len = int(audio_seg.frame_rate * frame_ms / 1000)
    rms_values = [
        np.sqrt(np.mean(samples[i:i+frame_len] ** 2))
        for i in range(0, len(samples), frame_len)
    ]
    non_zero_rms = [v for v in rms_values if v > 0]
    if not non_zero_rms:
        return audio_seg.dBFS - 16
    
    # Convert RMS to dBFS manually since AudioSegment.rms_to_dBFS doesn't exist
    rms_percentile = np.percentile(non_zero_rms, percentile)
    # Convert RMS to dBFS: 20 * log10(rms / max_possible_value)
    # For 16-bit audio, max value is 32768
    max_value = 1 << (audio_seg.sample_width * 8 - 1)
    est_thresh_dbfs = 20 * np.log10(rms_percentile / max_value)
    return est_thresh_dbfs

def merge_close_chunks(timestamps, min_gap=0.25):
    if not timestamps:
        return []
    
    merged = []
    prev_start, prev_end = timestamps[0]
    
    for start, end in timestamps[1:]:
        # Only merge if the gap is smaller than min_gap AND the resulting chunk isn't too long
        gap = start - prev_end
        combined_duration = end - prev_start
        
        if gap < min_gap and combined_duration < 30.0:  # Don't merge if result > 30 seconds
            prev_end = end  # Extend the current chunk
        else:
            merged.append((prev_start, prev_end))  # Save the current chunk
            prev_start, prev_end = start, end      # Start a new chunk
    
    merged.append((prev_start, prev_end))  # Don't forget the last chunk
    return merged

def split_into_chunks(video_path, audio_path, output_dir, min_silence_len=200,
                      keep_silence=100, max_chunk_len=10000, filter_faces=True,
                      face_threshold=0.3, sample_interval=0.5):
    chunks_dir = os.path.join(output_dir, "chunks")
    audio_out = os.path.join(chunks_dir, "audio")
    video_out = os.path.join(chunks_dir, "video")
    os.makedirs(audio_out, exist_ok=True)
    os.makedirs(video_out, exist_ok=True)

    # Load and preprocess audio
    print("Loading and denoising audio...")
    audio_seg = AudioSegment.from_wav(audio_path)
    audio_seg = reduce_noise(audio_seg)

    print("Estimating silence threshold...")
    dynamic_thresh = dynamic_silence_thresh(audio_seg)
    
    # Use a more reasonable silence threshold (not too low)
    # If dynamic threshold is too low, use a higher default
    silence_thresh = max(dynamic_thresh, audio_seg.dBFS - 25)  # More sensitive for sentence breaks
    
    print(f"Dynamic threshold: {dynamic_thresh:.2f} dBFS")
    print(f"Using silence threshold: {silence_thresh:.2f} dBFS")
    print(f"Audio dBFS: {audio_seg.dBFS:.2f} dBFS")

    # Split audio
    raw_chunks = silence.split_on_silence(
        audio_seg,
        min_silence_len=min_silence_len,
        silence_thresh=silence_thresh,
        keep_silence=keep_silence
    )

    print(f"Found {len(raw_chunks)} raw chunks from silence detection")
    
    # If no chunks found (no silence detected), force split by max length
    if len(raw_chunks) <= 1:
        print("No silence detected, forcing split by max chunk length...")
        raw_chunks = []
        for i in range(0, len(audio_seg), max_chunk_len):
            raw_chunks.append(audio_seg[i:i + max_chunk_len])

    # Enforce max length per chunk
    final_chunks = []
    for chunk in raw_chunks:
        if len(chunk) <= max_chunk_len:
            final_chunks.append(chunk)
        else:
            for i in range(0, len(chunk), max_chunk_len):
                final_chunks.append(chunk[i:i + max_chunk_len])

    # Generate timestamps
    timestamps = []
    cursor = 0
    for chunk in final_chunks:
        start = cursor
        end = start + len(chunk)
        timestamps.append((start / 1000, end / 1000))  # seconds
        cursor = end

    # Keep chunks small - disable merging for sentence-level granularity
    print("Keeping chunks small for sentence-level processing...")
    print(f"Total chunks before face filtering: {len(timestamps)}")
    
    # Filter chunks by face detection if enabled
    if filter_faces:
        print("\n🔍 Filtering chunks by face detection...")
        timestamps = filter_chunks_with_faces(
            video_path, timestamps, 
            sample_interval=sample_interval,
            face_threshold=face_threshold
        )
        
        # Save face detection previews
        save_face_detection_preview(video_path, timestamps, output_dir)
    
    # Show final chunk statistics
    if len(timestamps) > 0:
        short_chunks = [end - start for start, end in timestamps if (end - start) < 5.0]
        medium_chunks = [end - start for start, end in timestamps if 5.0 <= (end - start) < 10.0]
        long_chunks = [end - start for start, end in timestamps if (end - start) >= 10.0]
        
        print(f"\nFinal chunk statistics:")
        print(f"  Total chunks: {len(timestamps)}")
        print(f"  Short chunks (<5s): {len(short_chunks)}")
        print(f"  Medium chunks (5-10s): {len(medium_chunks)}")
        print(f"  Long chunks (>=10s): {len(long_chunks)}")
        
        # Show first few chunks as examples
        for i, (start, end) in enumerate(timestamps[:5]):
            duration = end - start
            print(f"  Chunk {i}: {start:.2f}s - {end:.2f}s (duration: {duration:.2f}s)")
        if len(timestamps) > 5:
            print(f"  ... and {len(timestamps) - 5} more chunks")
    else:
        print("⚠️ No chunks remaining after face filtering!")
        return []

    # Export audio and video
    video = VideoFileClip(video_path)
    for i, (start, end) in enumerate(timestamps):
        print(f"Saving chunk {i:03d} [{start:.2f}s - {end:.2f}s]...")
        chunk_audio = audio_seg[int(start * 1000):int(end * 1000)]
        chunk_audio.export(os.path.join(audio_out, f"chunk_{i:03d}.wav"), format="wav")
        subclip = video.subclip(start, end)
        subclip.write_videofile(
            os.path.join(video_out, f"chunk_{i:03d}.mp4"),
            codec="libx264",
            audio_codec="aac",
            verbose=False,
            logger=None
        )

    return timestamps
