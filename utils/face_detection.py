import cv2
import numpy as np
from moviepy.editor import VideoFileClip
import os


def detect_faces_in_frame(frame, face_cascade=None, min_face_size=(30, 30)):
    """
    Detect faces in a single frame using OpenCV's Haar cascade classifier.
    
    Args:
        frame: Input frame (numpy array)
        face_cascade: Pre-loaded face cascade classifier
        min_face_size: Minimum face size to detect (width, height)
    
    Returns:
        List of face bounding boxes [(x, y, w, h), ...]
    """
    if face_cascade is None:
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    # Convert to grayscale for face detection
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    
    # Detect faces
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=min_face_size,
        flags=cv2.CASCADE_SCALE_IMAGE
    )
    
    return faces


def has_face_in_timerange(video_path, start_time, end_time, sample_interval=0.5, 
                         face_threshold=0.3, min_face_size=(30, 30)):
    """
    Check if there are faces in a given time range of a video.
    
    Args:
        video_path: Path to the video file
        start_time: Start time in seconds
        end_time: End time in seconds
        sample_interval: How often to sample frames (seconds)
        face_threshold: Minimum ratio of frames with faces to consider chunk valid
        min_face_size: Minimum face size to detect
    
    Returns:
        bool: True if faces are detected in sufficient frames
    """
    try:
        video = VideoFileClip(video_path)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Sample frames at regular intervals
        sample_times = np.arange(start_time, end_time, sample_interval)
        frames_with_faces = 0
        total_frames = len(sample_times)
        
        if total_frames == 0:
            return False
        
        for t in sample_times:
            if t >= video.duration:
                break
                
            # Get frame at time t
            frame = video.get_frame(t)
            
            # Detect faces
            faces = detect_faces_in_frame(frame, face_cascade, min_face_size)
            
            if len(faces) > 0:
                frames_with_faces += 1
        
        video.close()
        
        # Check if face detection ratio meets threshold
        face_ratio = frames_with_faces / total_frames if total_frames > 0 else 0
        return face_ratio >= face_threshold
        
    except Exception as e:
        print(f"Error detecting faces in timerange {start_time}-{end_time}: {e}")
        return False


def filter_chunks_with_faces(video_path, timestamps, sample_interval=0.5, 
                           face_threshold=0.3, min_face_size=(30, 30), show_progress=True):
    """
    Filter chunks to only keep those with detected faces.
    
    Args:
        video_path: Path to the video file
        timestamps: List of (start, end) time tuples
        sample_interval: How often to sample frames (seconds)
        face_threshold: Minimum ratio of frames with faces to consider chunk valid
        min_face_size: Minimum face size to detect
        show_progress: Whether to show progress
    
    Returns:
        List of filtered timestamps with faces
    """
    filtered_timestamps = []
    
    print(f"Filtering {len(timestamps)} chunks for face presence...")
    print(f"Face detection parameters:")
    print(f"  - Sample interval: {sample_interval}s")
    print(f"  - Face threshold: {face_threshold*100}%")
    print(f"  - Min face size: {min_face_size}")
    
    for i, (start, end) in enumerate(timestamps):
        if show_progress and i % 10 == 0:
            print(f"Processing chunk {i+1}/{len(timestamps)}...")
        
        duration = end - start
        print(f"Checking chunk {i}: {start:.2f}s-{end:.2f}s (duration: {duration:.2f}s)")
        
        if has_face_in_timerange(video_path, start, end, sample_interval, 
                               face_threshold, min_face_size):
            filtered_timestamps.append((start, end))
            print(f"  ✅ Face detected - keeping chunk")
        else:
            print(f"  ❌ No face detected - removing chunk")
    
    print(f"\nFace filtering results:")
    print(f"  Original chunks: {len(timestamps)}")
    print(f"  Chunks with faces: {len(filtered_timestamps)}")
    print(f"  Filtered out: {len(timestamps) - len(filtered_timestamps)}")
    
    return filtered_timestamps


def save_face_detection_preview(video_path, timestamps, output_dir, max_previews=5):
    """
    Save preview images showing face detection for the first few chunks.
    
    Args:
        video_path: Path to the video file
        timestamps: List of (start, end) time tuples
        output_dir: Directory to save preview images
        max_previews: Maximum number of preview images to save
    """
    preview_dir = os.path.join(output_dir, "face_detection_previews")
    os.makedirs(preview_dir, exist_ok=True)
    
    video = VideoFileClip(video_path)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    for i, (start, end) in enumerate(timestamps[:max_previews]):
        mid_time = (start + end) / 2
        frame = video.get_frame(mid_time)
        
        # Make frame writable by copying it
        frame = frame.copy()
        
        # Detect faces
        faces = detect_faces_in_frame(frame, face_cascade)
        
        # Draw bounding boxes around faces
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        
        # Save preview image
        preview_path = os.path.join(preview_dir, f"chunk_{i:03d}_faces.jpg")
        cv2.imwrite(preview_path, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
    
    video.close()
    print(f"Saved {min(len(timestamps), max_previews)} face detection previews in {preview_dir}")
