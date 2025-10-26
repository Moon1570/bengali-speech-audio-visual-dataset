import os

import numpy as np
import noisereduce as nr
from moviepy.editor import VideoFileClip
from pydub import AudioSegment, silence

from .face_detection import filter_chunks_with_faces, save_face_detection_preview
from .refine_chunks import refine_all_chunks_by_faces, save_refinement_preview


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

def get_silence_preset(preset_name):
    """
    Get silence detection parameters for different presets.
    
    Presets:
    - very_sensitive: Splits on very short pauses (word-level, -16 dB)
    - sensitive: Splits on short pauses (phrase-level, -18 dB)
    - balanced: Default - sentence-level pauses (-20 dB)
    - conservative: Only major pauses (paragraph-level, -22 dB)
    - very_conservative: Very long pauses only (-25 dB)
    
    Returns:
        dict: Parameters for silence detection
    """
    presets = {
        'very_sensitive': {
            'min_silence_len': 400,      # 400ms minimum silence
            'silence_offset': -16,       # dBFS offset from audio level
            'keep_silence': 100,         # Keep 100ms silence padding
            'max_chunk_len': 15000,      # Max 15s per chunk
            'description': 'Very sensitive - splits on short pauses (word-level)'
        },
        'sensitive': {
            'min_silence_len': 500,      # 500ms minimum silence
            'silence_offset': -18,       # dBFS offset from audio level
            'keep_silence': 120,         # Keep 120ms silence padding
            'max_chunk_len': 18000,      # Max 18s per chunk
            'description': 'Sensitive - splits on phrase-level pauses'
        },
        'balanced': {
            'min_silence_len': 700,      # 700ms minimum silence (DEFAULT)
            'silence_offset': -20,       # dBFS offset from audio level
            'keep_silence': 150,         # Keep 150ms silence padding
            'max_chunk_len': 20000,      # Max 20s per chunk
            'description': 'Balanced - sentence-level boundaries (default)'
        },
        'conservative': {
            'min_silence_len': 900,      # 900ms minimum silence
            'silence_offset': -22,       # dBFS offset from audio level
            'keep_silence': 180,         # Keep 180ms silence padding
            'max_chunk_len': 25000,      # Max 25s per chunk
            'description': 'Conservative - paragraph-level boundaries'
        },
        'very_conservative': {
            'min_silence_len': 1200,     # 1200ms minimum silence
            'silence_offset': -25,       # dBFS offset from audio level
            'keep_silence': 200,         # Keep 200ms silence padding
            'max_chunk_len': 30000,      # Max 30s per chunk
            'description': 'Very conservative - major topic changes only'
        }
    }
    
    if preset_name not in presets:
        print(f"⚠️  Unknown preset '{preset_name}', using 'balanced'")
        return presets['balanced']
    
    return presets[preset_name]


def split_into_chunks(video_path, audio_path, output_dir, 
                      silence_preset='balanced',
                      custom_silence_thresh=None,
                      custom_min_silence_len=None,
                      min_silence_len=None,  # Deprecated - use custom_min_silence_len or preset
                      keep_silence=None,
                      max_chunk_len=None,
                      filter_faces=True,
                      face_threshold=0.3, sample_interval=0.5, refine_chunks=True,
                      refine_sample_rate=0.03, min_face_duration=0.5, min_chunk_duration=1.0,
                      max_face_gap=0.1, apply_noise_reduction=False):
    # Get preset parameters
    preset_params = get_silence_preset(silence_preset)
    
    # Allow custom overrides
    if custom_min_silence_len is not None:
        preset_params['min_silence_len'] = custom_min_silence_len
    elif min_silence_len is not None:
        # Support deprecated parameter for backward compatibility
        preset_params['min_silence_len'] = min_silence_len
    
    if keep_silence is not None:
        preset_params['keep_silence'] = keep_silence
    
    if max_chunk_len is not None:
        preset_params['max_chunk_len'] = max_chunk_len
    
    # Extract final parameters
    final_min_silence_len = preset_params['min_silence_len']
    final_keep_silence = preset_params['keep_silence']
    final_max_chunk_len = preset_params['max_chunk_len']
    silence_offset = preset_params['silence_offset']
    
    print(f"🎚️  Silence Detection Settings:")
    print(f"   Preset: {silence_preset} - {preset_params['description']}")
    print(f"   Min silence length: {final_min_silence_len}ms")
    print(f"   Silence offset: {silence_offset} dB")
    print(f"   Keep silence padding: {final_keep_silence}ms")
    print(f"   Max chunk length: {final_max_chunk_len/1000:.1f}s")
    
    chunks_dir = os.path.join(output_dir, "chunks")
    audio_out = os.path.join(chunks_dir, "audio")
    video_out = os.path.join(chunks_dir, "video")
    os.makedirs(audio_out, exist_ok=True)
    os.makedirs(video_out, exist_ok=True)

    # Load and preprocess audio
    print("Loading audio...")
    audio_seg = AudioSegment.from_wav(audio_path)
    
    if apply_noise_reduction:
        print("Applying noise reduction...")
        audio_seg = reduce_noise(audio_seg)
    else:
        print("Noise reduction disabled")

    print("Estimating silence threshold...")
    dynamic_thresh = dynamic_silence_thresh(audio_seg)
    
    # Calculate silence threshold based on preset and custom override
    if custom_silence_thresh is not None:
        # Use custom absolute threshold
        silence_thresh = custom_silence_thresh
        print(f"Using custom silence threshold: {silence_thresh:.2f} dBFS")
    else:
        # Use preset offset from audio level
        silence_thresh = max(dynamic_thresh, audio_seg.dBFS + silence_offset)
        print(f"Using preset-based threshold: {silence_thresh:.2f} dBFS (offset: {silence_offset} dB)")
    
    print(f"   Dynamic threshold: {dynamic_thresh:.2f} dBFS")
    print(f"   Audio dBFS: {audio_seg.dBFS:.2f} dBFS")
    print(f"   Final threshold: {silence_thresh:.2f} dBFS")

    # Split audio using final parameters
    raw_chunks = silence.split_on_silence(
        audio_seg,
        min_silence_len=final_min_silence_len,
        silence_thresh=silence_thresh,
        keep_silence=final_keep_silence
    )

    print(f"Found {len(raw_chunks)} raw chunks from silence detection")
    
    # If no chunks found (no silence detected), force split by max length
    if len(raw_chunks) <= 1:
        print("No silence detected, forcing split by max chunk length...")
        raw_chunks = []
        for i in range(0, len(audio_seg), final_max_chunk_len):
            raw_chunks.append(audio_seg[i:i + final_max_chunk_len])

    # Enforce max length per chunk
    final_chunks = []
    for chunk in raw_chunks:
        if len(chunk) <= final_max_chunk_len:
            final_chunks.append(chunk)
        else:
            for i in range(0, len(chunk), final_max_chunk_len):
                final_chunks.append(chunk[i:i + final_max_chunk_len])

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
    
    # Refine chunks to remove non-face segments if enabled
    if refine_chunks and len(timestamps) > 0:
        original_timestamps = timestamps.copy()
        timestamps = refine_all_chunks_by_faces(
            video_path, timestamps,
            sample_rate=refine_sample_rate,
            min_face_duration=min_face_duration,
            min_chunk_duration=min_chunk_duration,
            max_gap=max_face_gap
        )
        
        # Save refinement previews
        save_refinement_preview(video_path, original_timestamps, timestamps, output_dir)
    
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
    import subprocess
    video = VideoFileClip(video_path)
    for i, (start, end) in enumerate(timestamps):
        print(f"Saving chunk {i:03d} [{start:.2f}s - {end:.2f}s]...")
        
        # Extract audio directly from original video using ffmpeg (lossless)
        audio_output = os.path.join(audio_out, f"chunk_{i:03d}.wav")
        duration = end - start
        
        # Use ffmpeg to extract audio without re-encoding quality loss
        ffmpeg_audio_cmd = [
            'ffmpeg', '-y',
            '-ss', str(start),
            '-i', video_path,
            '-t', str(duration),
            '-vn',  # No video
            '-acodec', 'pcm_s16le',  # High quality PCM audio
            '-ar', '44100',  # Sample rate
            '-ac', '2',  # Stereo
            audio_output
        ]
        subprocess.run(ffmpeg_audio_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Extract video chunk
        subclip = video.subclip(start, end)
        subclip.write_videofile(
            os.path.join(video_out, f"chunk_{i:03d}.mp4"),
            codec="libx264",
            audio_codec="aac",
            verbose=False,
            logger=None
        )

    return timestamps
