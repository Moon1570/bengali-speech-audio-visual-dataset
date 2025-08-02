#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import argparse
import subprocess
from pathlib import Path

def get_video_info(video_path):
    """Get video information using ffprobe"""
    command = f'ffprobe -v quiet -print_format json -show_format -show_streams "{video_path}"'
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        import json
        info = json.loads(result.stdout)
        
        # Find video stream
        video_stream = None
        audio_stream = None
        
        for stream in info['streams']:
            if stream['codec_type'] == 'video' and video_stream is None:
                video_stream = stream
            elif stream['codec_type'] == 'audio' and audio_stream is None:
                audio_stream = stream
        
        duration = float(info['format']['duration']) if 'duration' in info['format'] else None
        
        return {
            'duration': duration,
            'video_stream': video_stream,
            'audio_stream': audio_stream,
            'format': info['format']
        }
    
    return None

def cut_video_by_time(input_video, output_dir, start_time, duration, chunk_name=None):
    """
    Cut a specific segment from video
    
    Args:
        input_video: Path to input video
        output_dir: Output directory
        start_time: Start time in seconds
        duration: Duration in seconds
        chunk_name: Optional custom name for chunk
    """
    os.makedirs(output_dir, exist_ok=True)
    
    if chunk_name is None:
        chunk_name = f"chunk_{start_time:06.1f}s_{duration:06.1f}s.mp4"
    
    output_path = os.path.join(output_dir, chunk_name)
    
    # Use ffmpeg to extract segment
    command = f'ffmpeg -y -i "{input_video}" -ss {start_time} -t {duration} -c copy "{output_path}"'
    
    print(f"Extracting: {start_time}s - {start_time + duration}s -> {chunk_name}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ Created: {output_path}")
        return output_path
    else:
        print(f"❌ Error: {result.stderr}")
        return None

def cut_video_by_silence(input_video, output_dir, silence_threshold=-30, min_silence_duration=1.0, min_chunk_duration=5.0):
    """
    Cut video based on silence detection
    
    Args:
        input_video: Path to input video
        output_dir: Output directory
        silence_threshold: Silence threshold in dB (default: -30dB)
        min_silence_duration: Minimum silence duration to split (default: 1.0s)
        min_chunk_duration: Minimum chunk duration (default: 5.0s)
    """
    print(f"🔍 Detecting silence in: {input_video}")
    
    # Step 1: Detect silence using ffmpeg
    silence_detect_cmd = f'ffmpeg -i "{input_video}" -af "silencedetect=noise={silence_threshold}dB:d={min_silence_duration}" -f null - 2>&1'
    
    result = subprocess.run(silence_detect_cmd, shell=True, capture_output=True, text=True)
    
    # Parse silence detection output
    silence_starts = []
    silence_ends = []
    
    for line in result.stderr.split('\n'):
        if 'silence_start:' in line:
            time_str = line.split('silence_start: ')[1].split(' ')[0]
            silence_starts.append(float(time_str))
        elif 'silence_end:' in line:
            time_str = line.split('silence_end: ')[1].split(' ')[0]
            silence_ends.append(float(time_str))
    
    print(f"Found {len(silence_starts)} silence regions")
    
    # Get video duration
    video_info = get_video_info(input_video)
    total_duration = video_info['duration'] if video_info else None
    
    if total_duration is None:
        print("❌ Could not get video duration")
        return []
    
    # Calculate chunk boundaries
    chunk_boundaries = [0.0]  # Start with beginning
    
    # Add silence boundaries
    for start, end in zip(silence_starts, silence_ends):
        # Use middle of silence as split point
        split_point = (start + end) / 2
        chunk_boundaries.append(split_point)
    
    chunk_boundaries.append(total_duration)  # End with video end
    chunk_boundaries = sorted(set(chunk_boundaries))  # Remove duplicates and sort
    
    # Create chunks
    chunks = []
    os.makedirs(output_dir, exist_ok=True)
    
    for i in range(len(chunk_boundaries) - 1):
        start_time = chunk_boundaries[i]
        end_time = chunk_boundaries[i + 1]
        duration = end_time - start_time
        
        # Skip very short chunks
        if duration < min_chunk_duration:
            print(f"⏭️  Skipping short chunk: {duration:.1f}s")
            continue
        
        chunk_name = f"silence_chunk_{i:03d}_{start_time:06.1f}s.mp4"
        chunk_path = cut_video_by_time(input_video, output_dir, start_time, duration, chunk_name)
        
        if chunk_path:
            chunks.append(chunk_path)
    
    return chunks

def extract_audio_from_video(video_path, audio_output_path=None, sample_rate=16000, channels=1):
    """
    Extract audio from video file
    
    Args:
        video_path: Path to input video
        audio_output_path: Output audio path (auto-generated if None)
        sample_rate: Audio sample rate (default: 16000 for speech)
        channels: Number of audio channels (default: 1 for mono)
    """
    if audio_output_path is None:
        video_name = Path(video_path).stem
        audio_output_path = f"{video_name}.wav"
    
    # Create output directory
    os.makedirs(os.path.dirname(audio_output_path), exist_ok=True)
    
    # Extract audio using ffmpeg
    command = f'ffmpeg -y -i "{video_path}" -ac {channels} -ar {sample_rate} -vn "{audio_output_path}"'
    
    print(f"🎵 Extracting audio: {video_path} -> {audio_output_path}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ Audio extracted: {audio_output_path}")
        return audio_output_path
    else:
        print(f"❌ Audio extraction failed: {result.stderr}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Video chunking and audio extraction utilities")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Command: chunk by time
    chunk_parser = subparsers.add_parser('chunk-time', help='Cut video into fixed-duration chunks')
    chunk_parser.add_argument('--input', required=True, help='Input video file')
    chunk_parser.add_argument('--output_dir', required=True, help='Output directory for chunks')
    chunk_parser.add_argument('--duration', type=float, default=30.0, help='Chunk duration in seconds (default: 30)')
    chunk_parser.add_argument('--overlap', type=float, default=0.0, help='Overlap between chunks in seconds (default: 0)')
    
    # Command: chunk by silence
    silence_parser = subparsers.add_parser('chunk-silence', help='Cut video based on silence detection')
    silence_parser.add_argument('--input', required=True, help='Input video file')
    silence_parser.add_argument('--output_dir', required=True, help='Output directory for chunks')
    silence_parser.add_argument('--threshold', type=float, default=-30, help='Silence threshold in dB (default: -30)')
    silence_parser.add_argument('--min_silence', type=float, default=1.0, help='Minimum silence duration (default: 1.0s)')
    silence_parser.add_argument('--min_chunk', type=float, default=5.0, help='Minimum chunk duration (default: 5.0s)')
    
    # Command: extract audio
    audio_parser = subparsers.add_parser('extract-audio', help='Extract audio from video')
    audio_parser.add_argument('--input', required=True, help='Input video file')
    audio_parser.add_argument('--output', help='Output audio file (auto-generated if not specified)')
    audio_parser.add_argument('--sample_rate', type=int, default=16000, help='Sample rate (default: 16000)')
    audio_parser.add_argument('--channels', type=int, default=1, help='Number of channels (default: 1)')
    
    # Command: info
    info_parser = subparsers.add_parser('info', help='Get video information')
    info_parser.add_argument('--input', required=True, help='Input video file')
    
    args = parser.parse_args()
    
    if args.command == 'chunk-time':
        # Cut video into fixed-duration chunks
        video_info = get_video_info(args.input)
        if not video_info:
            print("❌ Could not get video information")
            return
        
        total_duration = video_info['duration']
        chunk_duration = args.duration
        overlap = args.overlap
        
        print(f"📹 Video duration: {total_duration:.1f}s")
        print(f"🔪 Chunk duration: {chunk_duration}s with {overlap}s overlap")
        
        chunks = []
        start_time = 0.0
        chunk_num = 0
        
        while start_time < total_duration:
            remaining = total_duration - start_time
            actual_duration = min(chunk_duration, remaining)
            
            if actual_duration < 5.0:  # Skip very short chunks
                break
            
            chunk_name = f"chunk_{chunk_num:03d}.mp4"
            chunk_path = cut_video_by_time(args.input, args.output_dir, start_time, actual_duration, chunk_name)
            
            if chunk_path:
                chunks.append(chunk_path)
            
            chunk_num += 1
            start_time += chunk_duration - overlap
        
        print(f"✅ Created {len(chunks)} chunks")
    
    elif args.command == 'chunk-silence':
        # Cut video based on silence
        chunks = cut_video_by_silence(
            args.input, 
            args.output_dir, 
            args.threshold, 
            args.min_silence, 
            args.min_chunk
        )
        print(f"✅ Created {len(chunks)} chunks based on silence")
    
    elif args.command == 'extract-audio':
        # Extract audio
        extract_audio_from_video(args.input, args.output, args.sample_rate, args.channels)
    
    elif args.command == 'info':
        # Show video info
        info = get_video_info(args.input)
        if info:
            print(f"📹 Video Information for: {args.input}")
            print(f"Duration: {info['duration']:.2f} seconds")
            if info['video_stream']:
                vs = info['video_stream']
                print(f"Video: {vs.get('codec_name', 'unknown')} {vs.get('width', '?')}x{vs.get('height', '?')} @ {vs.get('r_frame_rate', '?')} fps")
            if info['audio_stream']:
                aus = info['audio_stream']
                print(f"Audio: {aus.get('codec_name', 'unknown')} {aus.get('sample_rate', '?')} Hz {aus.get('channels', '?')} channels")
        else:
            print("❌ Could not get video information")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
