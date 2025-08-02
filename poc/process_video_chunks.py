#!/usr/bin/env python3
"""
Complete Video Processing Pipeline with SyncNet
Cuts video into chunks, extracts audio, and runs SyncNet analysis
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def run_command(command, description=""):
    """Run a shell command and return success status"""
    print(f"\n{'='*50}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print(f"{'='*50}")
    
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        print("STDOUT:")
        print(result.stdout)
    
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    
    if result.returncode == 0:
        print(f"✅ Success: {description}")
        return True
    else:
        print(f"❌ Failed: {description} (exit code: {result.returncode})")
        return False

def get_video_duration(video_path):
    """Get video duration in seconds using ffprobe"""
    command = f'ffprobe -v quiet -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{video_path}"'
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        try:
            return float(result.stdout.strip())
        except ValueError:
            return None
    return None

def create_chunks(video_path, chunk_duration=30, output_dir="video_chunks"):
    """Split video into chunks of specified duration"""
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Get video duration
    total_duration = get_video_duration(video_path)
    if total_duration is None:
        print("❌ Could not determine video duration")
        return []
    
    print(f"📹 Video duration: {total_duration:.2f} seconds")
    
    chunk_files = []
    start_time = 0
    chunk_idx = 0
    
    while start_time < total_duration:
        # Calculate chunk end time
        end_time = min(start_time + chunk_duration, total_duration)
        actual_duration = end_time - start_time
        
        # Generate chunk filename
        video_name = Path(video_path).stem
        chunk_filename = f"{video_name}_chunk_{chunk_idx:03d}.mp4"
        chunk_path = os.path.join(output_dir, chunk_filename)
        
        # FFmpeg command to extract chunk
        command = f'ffmpeg -y -i "{video_path}" -ss {start_time} -t {actual_duration} -c copy "{chunk_path}"'
        
        if run_command(command, f"Creating chunk {chunk_idx} ({start_time:.1f}s - {end_time:.1f}s)"):
            chunk_files.append(chunk_path)
            print(f"✅ Created: {chunk_path}")
        else:
            print(f"❌ Failed to create chunk {chunk_idx}")
        
        start_time = end_time
        chunk_idx += 1
    
    return chunk_files

def extract_audio(video_path, audio_output_dir="audio_chunks"):
    """Extract audio from video file"""
    
    # Create output directory
    os.makedirs(audio_output_dir, exist_ok=True)
    
    # Generate audio filename
    video_name = Path(video_path).stem
    audio_filename = f"{video_name}.wav"
    audio_path = os.path.join(audio_output_dir, audio_filename)
    
    # FFmpeg command to extract audio
    command = f'ffmpeg -y -i "{video_path}" -acodec pcm_s16le -ar 16000 -ac 1 "{audio_path}"'
    
    if run_command(command, f"Extracting audio from {video_name}"):
        print(f"✅ Audio extracted: {audio_path}")
        return audio_path
    else:
        print(f"❌ Failed to extract audio from {video_name}")
        return None

def run_syncnet_on_chunk(chunk_path, reference_name=None):
    """Run SyncNet pipeline on a video chunk"""
    
    if reference_name is None:
        reference_name = Path(chunk_path).stem
    
    print(f"\n🎯 Running SyncNet on: {chunk_path}")
    print(f"📝 Reference name: {reference_name}")
    
    # Step 1: Run the full pipeline
    pipeline_command = f'python run_pipeline.py --videofile "{chunk_path}" --reference "{reference_name}"'
    if not run_command(pipeline_command, "SyncNet Pipeline (face detection, tracking, cropping)"):
        return False
    
    # Step 2: Run SyncNet analysis
    syncnet_command = f'python run_syncnet.py --videofile "{chunk_path}" --reference "{reference_name}"'
    if not run_command(syncnet_command, "SyncNet Analysis (audio-visual sync)"):
        return False
    
    # Step 3: Generate visualization
    visualize_command = f'python run_visualise.py --videofile "{chunk_path}" --reference "{reference_name}"'
    if not run_command(visualize_command, "SyncNet Visualization"):
        return False
    
    # Check for outputs
    work_dir = f"data/work/pywork/{reference_name}"
    avi_dir = f"data/work/pyavi/{reference_name}"
    
    offsets_file = os.path.join(work_dir, "offsets.txt")
    output_video = os.path.join(avi_dir, "video_out.avi")
    
    results = {
        'reference': reference_name,
        'offsets_file': offsets_file if os.path.exists(offsets_file) else None,
        'output_video': output_video if os.path.exists(output_video) else None,
        'success': True
    }
    
    if results['offsets_file']:
        print(f"✅ Offsets file: {offsets_file}")
        # Read and display offsets
        try:
            with open(offsets_file, 'r') as f:
                content = f.read().strip()
                print(f"📊 Sync Results: {content}")
        except Exception as e:
            print(f"⚠️  Could not read offsets file: {e}")
    
    if results['output_video']:
        print(f"✅ Output video: {output_video}")
    
    return results

def main():
    parser = argparse.ArgumentParser(description='Process video with SyncNet pipeline')
    parser.add_argument('--video', type=str, required=True, help='Path to input video file')
    parser.add_argument('--chunk_duration', type=int, default=30, help='Chunk duration in seconds (default: 30)')
    parser.add_argument('--max_chunks', type=int, default=5, help='Maximum number of chunks to process (default: 5)')
    parser.add_argument('--skip_chunking', action='store_true', help='Skip chunking and process entire video')
    parser.add_argument('--output_dir', type=str, default='processed_output', help='Output directory for results')
    
    args = parser.parse_args()
    
    # Validate input video
    if not os.path.exists(args.video):
        print(f"❌ Video file not found: {args.video}")
        return 1
    
    print(f"🎬 Processing video: {args.video}")
    print(f"📁 Output directory: {args.output_dir}")
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    if args.skip_chunking:
        # Process entire video
        print("\n🎯 Processing entire video (no chunking)")
        reference_name = Path(args.video).stem
        results = run_syncnet_on_chunk(args.video, reference_name)
        
        if results and results['success']:
            print(f"\n✅ Video processing completed successfully!")
            print(f"📊 Results for {reference_name}:")
            if results['offsets_file']:
                print(f"   - Sync analysis: {results['offsets_file']}")
            if results['output_video']:
                print(f"   - Output video: {results['output_video']}")
        else:
            print(f"\n❌ Video processing failed!")
            return 1
    
    else:
        # Create chunks and process them
        chunk_dir = os.path.join(args.output_dir, "chunks")
        audio_dir = os.path.join(args.output_dir, "audio")
        
        print(f"\n✂️  Creating video chunks (duration: {args.chunk_duration}s)")
        chunks = create_chunks(args.video, args.chunk_duration, chunk_dir)
        
        if not chunks:
            print("❌ No chunks were created")
            return 1
        
        print(f"\n📊 Created {len(chunks)} chunks")
        
        # Limit number of chunks to process
        chunks_to_process = chunks[:args.max_chunks]
        if len(chunks) > args.max_chunks:
            print(f"⚠️  Processing only first {args.max_chunks} chunks (limit)")
        
        # Process each chunk
        results = []
        for i, chunk_path in enumerate(chunks_to_process):
            print(f"\n{'='*60}")
            print(f"🎬 Processing chunk {i+1}/{len(chunks_to_process)}: {os.path.basename(chunk_path)}")
            print(f"{'='*60}")
            
            # Extract audio from chunk
            audio_path = extract_audio(chunk_path, audio_dir)
            if not audio_path:
                print(f"⚠️  Skipping chunk {i+1} due to audio extraction failure")
                continue
            
            # Run SyncNet on chunk
            reference_name = Path(chunk_path).stem
            chunk_results = run_syncnet_on_chunk(chunk_path, reference_name)
            
            if chunk_results and chunk_results['success']:
                chunk_results['chunk_path'] = chunk_path
                chunk_results['audio_path'] = audio_path
                results.append(chunk_results)
                print(f"✅ Chunk {i+1} processed successfully!")
            else:
                print(f"❌ Chunk {i+1} processing failed!")
        
        # Summary
        print(f"\n{'='*60}")
        print(f"📋 PROCESSING SUMMARY")
        print(f"{'='*60}")
        print(f"Total chunks created: {len(chunks)}")
        print(f"Chunks processed: {len(chunks_to_process)}")
        print(f"Successful results: {len(results)}")
        
        for i, result in enumerate(results):
            print(f"\n📊 Chunk {i+1}: {result['reference']}")
            if result['offsets_file']:
                try:
                    with open(result['offsets_file'], 'r') as f:
                        content = f.read().strip()
                        print(f"   - Sync: {content}")
                except:
                    print(f"   - Sync: {result['offsets_file']}")
            if result['output_video']:
                print(f"   - Video: {result['output_video']}")
    
    print(f"\n🎉 Processing completed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
