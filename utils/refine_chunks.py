import cv2
import numpy as np
from moviepy.editor import VideoFileClip
import os
from .face_detection import detect_faces_in_frame


def analyze_face_timeline_in_chunk(video_path, start_time, end_time, sample_rate=0.1):
    """
    Analyze face presence throughout a chunk timeline with high resolution.
    
    Args:
        video_path: Path to the video file
        start_time: Start time of chunk in seconds
        end_time: End time of chunk in seconds
        sample_rate: How often to sample (in seconds) for face detection
    
    Returns:
        List of (timestamp, has_face) tuples
    """
    video = VideoFileClip(video_path)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    # Sample at high resolution within the chunk
    sample_times = np.arange(start_time, end_time, sample_rate)
    face_timeline = []
    
    for t in sample_times:
        if t >= video.duration:
            break
            
        frame = video.get_frame(t)
        faces = detect_faces_in_frame(frame, face_cascade)
        has_face = len(faces) > 0
        face_timeline.append((t, has_face))
    
    video.close()
    return face_timeline


def find_face_segments(face_timeline, min_face_duration=0.5, max_gap=0.3):
    """
    Find continuous segments where faces are present, allowing small gaps.
    
    Args:
        face_timeline: List of (timestamp, has_face) tuples
        min_face_duration: Minimum duration for a face segment to be valid
        max_gap: Maximum allowed gap without face (e.g., for blinks) in seconds
    
    Returns:
        List of (start_time, end_time) tuples for face segments
    """
    if not face_timeline:
        return []
    
    face_segments = []
    current_start = None
    last_face_time = None
    
    for i, (timestamp, has_face) in enumerate(face_timeline):
        if has_face:
            if current_start is None:
                # Start of a new face segment
                current_start = timestamp
                last_face_time = timestamp
            else:
                # Continue existing segment
                last_face_time = timestamp
        else:
            # No face detected
            if current_start is not None:
                # Check if gap is too large
                gap = timestamp - last_face_time
                if gap > max_gap:
                    # Gap is too large - end current segment
                    duration = last_face_time - current_start
                    if duration >= min_face_duration:
                        face_segments.append((current_start, last_face_time))
                    current_start = None
                    last_face_time = None
                # else: small gap, continue the segment
    
    # Handle case where chunk ends with faces
    if current_start is not None and last_face_time is not None:
        duration = last_face_time - current_start
        if duration >= min_face_duration:
            face_segments.append((current_start, last_face_time))
    
    return face_segments


def refine_chunk_by_faces(video_path, start_time, end_time, sample_rate=0.1, 
                         min_face_duration=0.5, min_chunk_duration=1.0, max_gap=0.3):
    """
    Refine a chunk to only include segments with faces.
    
    Args:
        video_path: Path to the video file
        start_time: Original start time of chunk
        end_time: Original end time of chunk
        sample_rate: Sampling rate for face detection (seconds)
        min_face_duration: Minimum duration for face segments
        min_chunk_duration: Minimum duration for refined chunks
        max_gap: Maximum gap without face to tolerate (seconds)
    
    Returns:
        List of refined (start_time, end_time) tuples with faces only
    """
    print(f"  Refining chunk {start_time:.2f}s - {end_time:.2f}s...")
    
    # Analyze face presence throughout the chunk
    face_timeline = analyze_face_timeline_in_chunk(video_path, start_time, end_time, sample_rate)
    
    if not face_timeline:
        print(f"    ❌ No timeline data - removing chunk")
        return []
    
    # Find continuous face segments (allowing small gaps for blinks, etc.)
    face_segments = find_face_segments(face_timeline, min_face_duration, max_gap)
    
    if not face_segments:
        print(f"    ❌ No face segments found - removing chunk")
        return []
    
    # Filter segments by minimum duration and validate face presence percentage
    valid_segments = []
    min_face_percentage = 0.95  # Require 95% face presence for benchmarking dataset
    
    for seg_start, seg_end in face_segments:
        duration = seg_end - seg_start
        if duration < min_chunk_duration:
            continue
            
        # Calculate face presence percentage in this segment
        segment_timeline = [(t, has_face) for t, has_face in face_timeline 
                          if seg_start <= t <= seg_end]
        
        if segment_timeline:
            faces_present = sum(1 for _, has_face in segment_timeline if has_face)
            face_percentage = faces_present / len(segment_timeline)
            
            if face_percentage >= min_face_percentage:
                valid_segments.append((seg_start, seg_end))
            else:
                print(f"      ⚠️  Segment {seg_start:.2f}s-{seg_end:.2f}s rejected: "
                      f"only {face_percentage*100:.1f}% face presence (need {min_face_percentage*100:.0f}%)")
    
    if not valid_segments:
        print(f"    ❌ No segments meet quality requirements (95% face presence)")
        return []
    
    # Show refinement results
    original_duration = end_time - start_time
    refined_duration = sum(end - start for start, end in valid_segments)
    
    print(f"    ✅ Refined: {original_duration:.2f}s → {refined_duration:.2f}s "
          f"({len(valid_segments)} segments)")
    
    for i, (seg_start, seg_end) in enumerate(valid_segments):
        print(f"      Segment {i+1}: {seg_start:.2f}s - {seg_end:.2f}s "
              f"(duration: {seg_end - seg_start:.2f}s)")
    
    return valid_segments


def refine_all_chunks_by_faces(video_path, timestamps, sample_rate=0.1, 
                              min_face_duration=0.5, min_chunk_duration=1.0, 
                              max_gap=0.3, show_progress=True):
    """
    Refine all chunks to only include face segments.
    
    Args:
        video_path: Path to the video file
        timestamps: List of original (start, end) timestamps
        sample_rate: Sampling rate for face detection (seconds)
        min_face_duration: Minimum duration for face segments
        min_chunk_duration: Minimum duration for refined chunks
        max_gap: Maximum gap without face to tolerate (seconds)
        show_progress: Whether to show progress
    
    Returns:
        List of refined timestamps with only face segments
    """
    print(f"\n🎯 Refining {len(timestamps)} chunks to remove non-face segments...")
    print(f"Refinement parameters:")
    print(f"  - Sample rate: {sample_rate}s (checking every {sample_rate}s)")
    print(f"  - Max gap without face: {max_gap}s")
    print(f"  - Min face duration: {min_face_duration}s")
    print(f"  - Min chunk duration: {min_chunk_duration}s")
    
    refined_timestamps = []
    
    for i, (start, end) in enumerate(timestamps):
        if show_progress and i % 10 == 0:
            print(f"\nProcessing chunk {i+1}/{len(timestamps)}...")
        
        # Refine this chunk
        face_segments = refine_chunk_by_faces(
            video_path, start, end, sample_rate, 
            min_face_duration, min_chunk_duration, max_gap
        )
        
        # Add all valid face segments
        refined_timestamps.extend(face_segments)
    
    print(f"\n🎯 Refinement results:")
    print(f"  Original chunks: {len(timestamps)}")
    print(f"  Refined chunks: {len(refined_timestamps)}")
    
    if len(timestamps) > 0:
        original_total = sum(end - start for start, end in timestamps)
        refined_total = sum(end - start for start, end in refined_timestamps)
        reduction = ((original_total - refined_total) / original_total) * 100 if original_total > 0 else 0
        
        print(f"  Total duration: {original_total:.1f}s → {refined_total:.1f}s")
        print(f"  Reduction: {reduction:.1f}% (removed non-face segments)")
    
    return refined_timestamps


def save_refinement_preview(video_path, original_timestamps, refined_timestamps, 
                           output_dir, max_previews=3):
    """
    Save preview images showing before/after refinement.
    
    Args:
        video_path: Path to the video file
        original_timestamps: Original chunk timestamps
        refined_timestamps: Refined chunk timestamps
        output_dir: Directory to save preview images
        max_previews: Maximum number of preview comparisons to save
    """
    preview_dir = os.path.join(output_dir, "refinement_previews")
    os.makedirs(preview_dir, exist_ok=True)
    
    video = VideoFileClip(video_path)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    for i in range(min(len(original_timestamps), max_previews)):
        orig_start, orig_end = original_timestamps[i]
        
        # Find corresponding refined segments
        refined_segments = [
            (start, end) for start, end in refined_timestamps 
            if start >= orig_start and end <= orig_end
        ]
        
        if not refined_segments:
            continue
        
        # Create comparison image
        fig_height = 200
        fig_width = 800
        comparison_img = np.zeros((fig_height * 2, fig_width, 3), dtype=np.uint8)
        
        # Original chunk (top half)
        orig_mid = (orig_start + orig_end) / 2
        orig_frame = video.get_frame(orig_mid).copy()
        orig_frame = cv2.resize(orig_frame, (fig_width, fig_height))
        faces = detect_faces_in_frame(orig_frame, face_cascade)
        for (x, y, w, h) in faces:
            cv2.rectangle(orig_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        comparison_img[:fig_height] = orig_frame
        
        # Refined segment (bottom half)
        if refined_segments:
            ref_start, ref_end = refined_segments[0]  # Show first refined segment
            ref_mid = (ref_start + ref_end) / 2
            ref_frame = video.get_frame(ref_mid).copy()
            ref_frame = cv2.resize(ref_frame, (fig_width, fig_height))
            faces = detect_faces_in_frame(ref_frame, face_cascade)
            for (x, y, w, h) in faces:
                cv2.rectangle(ref_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            comparison_img[fig_height:] = ref_frame
        
        # Add text labels
        cv2.putText(comparison_img, f"Original: {orig_start:.1f}s-{orig_end:.1f}s", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        if refined_segments:
            ref_text = f"Refined: {len(refined_segments)} segments"
            cv2.putText(comparison_img, ref_text, 
                       (10, fig_height + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Save comparison image
        preview_path = os.path.join(preview_dir, f"refinement_{i:03d}.jpg")
        cv2.imwrite(preview_path, comparison_img)
    
    video.close()
    print(f"Saved {min(len(original_timestamps), max_previews)} refinement previews in {preview_dir}")
