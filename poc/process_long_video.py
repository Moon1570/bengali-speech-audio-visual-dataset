#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import argparse
import subprocess
import json
import time
from pathlib import Path

def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"Running: {description}")
    print(f"Command: {command}")
    
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error in {description}:")
        print(f"stdout: {result.stdout}")
        print(f"stderr: {result.stderr}")
        return False
    
    print(f"✅ {description} completed successfully")
    return True

def get_video_duration(video_path):
    """Get video duration in seconds using ffprobe"""
    command = f'ffprobe -v quiet -show_entries format=duration -of csv=p=0 "{video_path}"'
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        return float(result.stdout.strip())
    else:
        print(f"Error getting video duration: {result.stderr}")
        return None

def cut_video_chunks(input_video, output_dir, chunk_duration=30, overlap=5):
    """
    Cut video into chunks with optional overlap
    
    Args:
        input_video: Path to input video file
        output_dir: Directory to save chunks
        chunk_duration: Duration of each chunk in seconds
        overlap: Overlap between chunks in seconds
    
    Returns:
        List of chunk file paths
    """
    print(f"\n🎬 Cutting video into {chunk_duration}s chunks...")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Get video duration
    total_duration = get_video_duration(input_video)
    if total_duration is None:
        return []
    
    print(f"Total video duration: {total_duration:.2f} seconds")
    
    chunk_files = []
    chunk_num = 0
    start_time = 0
    
    while start_time < total_duration:
        # Calculate end time
        end_time = min(start_time + chunk_duration, total_duration)
        actual_duration = end_time - start_time
        
        # Skip very short chunks
        if actual_duration < 5:
            break
            
        # Generate chunk filename
        chunk_name = f"chunk_{chunk_num:03d}.mp4"
        chunk_path = os.path.join(output_dir, chunk_name)
        
        # Extract chunk using ffmpeg
        command = f'ffmpeg -y -i "{input_video}" -ss {start_time} -t {actual_duration} -c copy "{chunk_path}"'
        
        if run_command(command, f"Extracting chunk {chunk_num} ({start_time:.1f}s - {end_time:.1f}s)"):
            chunk_files.append(chunk_path)
            print(f"  📹 Created: {chunk_name}")
        
        chunk_num += 1
        start_time += chunk_duration - overlap  # Move start with overlap
    
    print(f"✅ Created {len(chunk_files)} video chunks")
    return chunk_files

def extract_audio_from_chunk(video_path, audio_output_dir):
    """Extract audio from a video chunk"""
    video_name = Path(video_path).stem
    audio_path = os.path.join(audio_output_dir, f"{video_name}.wav")
    
    # Create audio output directory
    os.makedirs(audio_output_dir, exist_ok=True)
    
    # Extract audio using ffmpeg
    command = f'ffmpeg -y -i "{video_path}" -ac 1 -ar 16000 -vn "{audio_path}"'
    
    if run_command(command, f"Extracting audio from {video_name}"):
        return audio_path
    return None

def run_syncnet_pipeline(video_path, reference_name, data_dir, min_track=5, min_face_size=10):
    """
    Run complete SyncNet pipeline on a video chunk
    
    Returns:
        Dictionary with results or None if failed
    """
    print(f"\n🔄 Running SyncNet pipeline for {reference_name}...")
    
    # Step 1: Run preprocessing pipeline
    pipeline_cmd = f'python run_pipeline.py --videofile "{video_path}" --reference {reference_name} --data_dir "{data_dir}" --min_track {min_track} --min_face_size {min_face_size}'
    
    if not run_command(pipeline_cmd, f"SyncNet preprocessing for {reference_name}"):
        return None
    
    # Check if cropped face video was created
    crop_dir = os.path.join(data_dir, 'pycrop', reference_name)
    crop_files = [f for f in os.listdir(crop_dir) if f.endswith('.avi')] if os.path.exists(crop_dir) else []
    
    if not crop_files:
        print(f"❌ No face tracks found for {reference_name}")
        return {"status": "no_faces", "reference": reference_name}
    
    # Step 2: Run SyncNet analysis
    syncnet_cmd = f'python run_syncnet.py --videofile "{os.path.join(crop_dir, crop_files[0])}" --reference {reference_name} --data_dir "{data_dir}"'
    
    if not run_command(syncnet_cmd, f"SyncNet analysis for {reference_name}"):
        return None
    
    # Step 3: Generate visualization (optional)
    viz_cmd = f'python run_visualise.py --videofile "{video_path}" --reference {reference_name} --data_dir "{data_dir}"'
    run_command(viz_cmd, f"SyncNet visualization for {reference_name}")
    
    # Read results
    offsets_file = os.path.join(data_dir, 'pywork', reference_name, 'offsets.txt')
    
    results = {
        "status": "success",
        "reference": reference_name,
        "video_path": video_path,
        "face_tracks": len(crop_files),
        "offsets_file": offsets_file if os.path.exists(offsets_file) else None
    }
    
    # Parse offset results
    if os.path.exists(offsets_file):
        with open(offsets_file, 'r') as f:
            content = f.read().strip()
            if content:
                # Parse multiple tracks: "TRACK 0: OFFSET -1, CONF 7.183"
                lines = content.split('\n')
                tracks = []
                
                for line in lines:
                    line = line.strip()
                    if line and 'TRACK' in line:
                        try:
                            # Parse: "TRACK 0: OFFSET -1, CONF 7.183"
                            parts = line.split(', ')
                            if len(parts) >= 2:
                                offset_part = parts[0].split(': OFFSET ')
                                conf_part = parts[1].split('CONF ')
                                
                                if len(offset_part) >= 2 and len(conf_part) >= 2:
                                    track_info = {
                                        "offset": int(offset_part[1]),
                                        "confidence": float(conf_part[1])
                                    }
                                    tracks.append(track_info)
                        except (ValueError, IndexError) as e:
                            print(f"Warning: Could not parse line '{line}': {e}")
                
                # Use the track with highest confidence
                if tracks:
                    best_track = max(tracks, key=lambda x: x['confidence'])
                    results["offset"] = best_track["offset"]
                    results["confidence"] = best_track["confidence"]
                    results["all_tracks"] = tracks
    
    return results

def process_long_video(input_video, output_base_dir, chunk_duration=30, overlap=5, min_track=5, min_face_size=10, 
                      min_confidence=2.0, max_abs_offset=10, filter_low_quality=True):
    """
    Main function to process a long video file
    
    Args:
        input_video: Path to input video file
        output_base_dir: Base directory for all outputs
        chunk_duration: Duration of each chunk in seconds
        overlap: Overlap between chunks in seconds
        min_track: Minimum track length for SyncNet
        min_face_size: Minimum face size for SyncNet
        min_confidence: Minimum confidence score to accept chunk (default: 2.0)
        max_abs_offset: Maximum absolute offset in frames to accept chunk (default: 10)
        filter_low_quality: Whether to filter out low-quality chunks (default: True)
    """
    print(f"🎥 Processing long video: {input_video}")
    print(f"📁 Output directory: {output_base_dir}")
    
    # Create output directories
    chunks_dir = os.path.join(output_base_dir, 'chunks')
    audio_dir = os.path.join(output_base_dir, 'audio')
    syncnet_data_dir = os.path.join(output_base_dir, 'syncnet_data')
    
    os.makedirs(output_base_dir, exist_ok=True)
    
    # Step 1: Cut video into chunks
    chunk_files = cut_video_chunks(input_video, chunks_dir, chunk_duration, overlap)
    
    if not chunk_files:
        print("❌ No chunks created. Exiting.")
        return
    
    # Step 2: Process each chunk
    results = []
    accepted_chunks = []
    rejected_chunks = []
    
    for i, chunk_path in enumerate(chunk_files):
        chunk_name = Path(chunk_path).stem
        print(f"\n{'='*60}")
        print(f"Processing chunk {i+1}/{len(chunk_files)}: {chunk_name}")
        print(f"{'='*60}")
        
        # Extract audio
        audio_path = extract_audio_from_chunk(chunk_path, audio_dir)
        
        if audio_path:
            print(f"  🎵 Audio extracted: {audio_path}")
        
        # Run SyncNet analysis
        syncnet_result = run_syncnet_pipeline(
            chunk_path, 
            chunk_name, 
            syncnet_data_dir, 
            min_track=min_track, 
            min_face_size=min_face_size
        )
        
        if syncnet_result:
            syncnet_result["chunk_index"] = i
            syncnet_result["audio_path"] = audio_path
            results.append(syncnet_result)
            
            # Evaluate chunk quality and decide whether to accept/reject
            if syncnet_result["status"] == "success":
                offset = syncnet_result.get("offset", float('inf'))
                confidence = syncnet_result.get("confidence", 0.0)
                
                # Quality check
                abs_offset = abs(offset)
                is_good_confidence = confidence >= min_confidence
                is_good_offset = abs_offset <= max_abs_offset
                
                if filter_low_quality and (not is_good_confidence or not is_good_offset):
                    # Reject this chunk
                    syncnet_result["quality_status"] = "rejected"
                    syncnet_result["rejection_reason"] = []
                    
                    if not is_good_confidence:
                        syncnet_result["rejection_reason"].append(f"low_confidence ({confidence:.3f} < {min_confidence})")
                    if not is_good_offset:
                        syncnet_result["rejection_reason"].append(f"high_offset ({abs_offset} > {max_abs_offset})")
                    
                    rejected_chunks.append(syncnet_result)
                    print(f"  ❌ REJECTED: {', '.join(syncnet_result['rejection_reason'])}")
                    print(f"     Offset={offset}, Confidence={confidence:.3f}")
                else:
                    # Accept this chunk
                    syncnet_result["quality_status"] = "accepted"
                    accepted_chunks.append(syncnet_result)
                    print(f"  ✅ ACCEPTED: Offset={offset}, Confidence={confidence:.3f}")
                    
            elif syncnet_result["status"] == "no_faces":
                syncnet_result["quality_status"] = "rejected"
                syncnet_result["rejection_reason"] = ["no_faces_detected"]
                rejected_chunks.append(syncnet_result)
                print(f"  ❌ REJECTED: No faces detected in this chunk")
    
    # Create filtered output directories for accepted chunks only
    if filter_low_quality and accepted_chunks:
        filtered_chunks_dir = os.path.join(output_base_dir, 'filtered_chunks')
        filtered_audio_dir = os.path.join(output_base_dir, 'filtered_audio')
        
        os.makedirs(filtered_chunks_dir, exist_ok=True)
        os.makedirs(filtered_audio_dir, exist_ok=True)
        
        print(f"\n🔍 Creating filtered dataset with {len(accepted_chunks)} high-quality chunks...")
        
        for chunk_result in accepted_chunks:
            # Copy video chunk
            src_video = chunk_result["video_path"]
            dst_video = os.path.join(filtered_chunks_dir, os.path.basename(src_video))
            import shutil
            shutil.copy2(src_video, dst_video)
            
            # Copy audio file
            src_audio = chunk_result["audio_path"]
            if src_audio and os.path.exists(src_audio):
                dst_audio = os.path.join(filtered_audio_dir, os.path.basename(src_audio))
                shutil.copy2(src_audio, dst_audio)
        
        print(f"  📁 Filtered videos: {filtered_chunks_dir}")
        print(f"  📁 Filtered audio: {filtered_audio_dir}")
    
    # Step 3: Save summary results
    summary_file = os.path.join(output_base_dir, 'processing_summary.json')
    
    summary = {
        "input_video": input_video,
        "total_chunks": len(chunk_files),
        "successful_analysis": len([r for r in results if r["status"] == "success"]),
        "no_faces_chunks": len([r for r in results if r["status"] == "no_faces"]),
        "accepted_chunks": len(accepted_chunks),
        "rejected_chunks": len(rejected_chunks),
        "acceptance_rate": len(accepted_chunks) / len(chunk_files) * 100 if chunk_files else 0,
        "chunk_duration": chunk_duration,
        "overlap": overlap,
        "quality_filters": {
            "min_confidence": min_confidence,
            "max_abs_offset": max_abs_offset,
            "filter_enabled": filter_low_quality
        },
        "processing_time": time.time(),
        "results": results,
        "accepted_chunks": [r["reference"] for r in accepted_chunks],
        "rejected_chunks": [{"reference": r["reference"], "reason": r.get("rejection_reason", [])} for r in rejected_chunks]
    }
    
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n{'='*60}")
    print("📊 PROCESSING SUMMARY")
    print(f"{'='*60}")
    print(f"Total chunks processed: {summary['total_chunks']}")
    print(f"Successful SyncNet analysis: {summary['successful_analysis']}")
    print(f"Chunks with no faces: {summary['no_faces_chunks']}")
    
    if filter_low_quality:
        print(f"✅ Accepted chunks: {summary['accepted_chunks']} ({summary['acceptance_rate']:.1f}%)")
        print(f"❌ Rejected chunks: {summary['rejected_chunks']}")
        print(f"🎯 Quality filters: confidence≥{min_confidence}, |offset|≤{max_abs_offset}")
    
    print(f"Summary saved to: {summary_file}")
    
    # Print individual results
    print(f"\n📋 DETAILED RESULTS:")
    for result in results:
        if result["status"] == "success":
            offset = result.get("offset", "?")
            conf = result.get("confidence", "?")
            status = result.get("quality_status", "unknown")
            status_emoji = "✅" if status == "accepted" else "❌" if status == "rejected" else "⚠️"
            
            print(f"  {status_emoji} {result['reference']}: Offset={offset}, Conf={conf:.3f}")
            
            if status == "rejected" and "rejection_reason" in result:
                print(f"      Reason: {', '.join(result['rejection_reason'])}")
    
    # Print summary of rejected chunks
    if rejected_chunks:
        print(f"\n🗑️  REJECTED CHUNKS SUMMARY:")
        rejection_reasons = {}
        for chunk in rejected_chunks:
            for reason in chunk.get("rejection_reason", []):
                rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1
        
        for reason, count in rejection_reasons.items():
            print(f"  - {reason}: {count} chunks")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process long video with SyncNet analysis")
    parser.add_argument('--input_video', type=str, required=True, help='Path to input video file')
    parser.add_argument('--output_dir', type=str, required=True, help='Output directory for all results')
    parser.add_argument('--chunk_duration', type=int, default=30, help='Duration of each chunk in seconds (default: 30)')
    parser.add_argument('--overlap', type=int, default=5, help='Overlap between chunks in seconds (default: 5)')
    parser.add_argument('--min_track', type=int, default=5, help='Minimum track length for SyncNet (default: 5)')
    parser.add_argument('--min_face_size', type=int, default=10, help='Minimum face size for SyncNet (default: 10)')
    parser.add_argument('--min_confidence', type=float, default=2.0, help='Minimum confidence score to accept chunk (default: 2.0)')
    parser.add_argument('--max_abs_offset', type=int, default=10, help='Maximum absolute offset in frames to accept chunk (default: 10)')
    parser.add_argument('--filter_low_quality', action='store_true', default=True, help='Filter out low-quality chunks (default: True)')
    parser.add_argument('--no_filter', action='store_false', dest='filter_low_quality', help='Disable quality filtering')
    
    args = parser.parse_args()
    
    # Validate input
    if not os.path.exists(args.input_video):
        print(f"❌ Input video file not found: {args.input_video}")
        sys.exit(1)
    
    # Run processing
    process_long_video(
        input_video=args.input_video,
        output_base_dir=args.output_dir,
        chunk_duration=args.chunk_duration,
        overlap=args.overlap,
        min_track=args.min_track,
        min_face_size=args.min_face_size,
        min_confidence=args.min_confidence,
        max_abs_offset=args.max_abs_offset,
        filter_low_quality=args.filter_low_quality
    )
