#!/usr/bin/env python3
"""
Audio Processing Utilities
==========================

This module provides utilities for audio and video processing including:
- Video to audio extraction
- Audio splitting by silence
- File type detection
- Chunk creation from raw media files
"""

import os
import logging
from pathlib import Path
import tempfile
import shutil

# Import audio/video processing libraries
try:
    from moviepy.editor import VideoFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    
try:
    from pydub import AudioSegment
    from pydub.silence import split_on_silence
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

logger = logging.getLogger(__name__)


def is_video_file(file_path):
    """Check if file is a video file."""
    video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.webm', '.flv', '.wmv', '.m4v', '.mpg', '.mpeg', '.m2ts'}
    return Path(file_path).suffix.lower() in video_extensions


def is_audio_file(file_path):
    """Check if file is an audio file."""
    audio_extensions = {'.wav', '.mp3', '.m4a', '.aac', '.flac', '.ogg', '.wma'}
    return Path(file_path).suffix.lower() in audio_extensions


def extract_audio_from_video(video_path, output_path):
    """Extract audio from video file."""
    if not MOVIEPY_AVAILABLE:
        raise ImportError("MoviePy is required for video processing. Install with: pip install moviepy")
    
    logger.info(f"🎬 Extracting audio from video: {os.path.basename(video_path)}")
    try:
        video = VideoFileClip(video_path)
        audio = video.audio
        audio.write_audiofile(output_path, verbose=False, logger=None)
        video.close()
        audio.close()
        logger.info(f"✅ Audio extracted to: {output_path}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to extract audio: {e}")
        return False


def split_audio_into_chunks(audio_path, output_dir, min_silence_len=500, silence_thresh=-40, keep_silence=100):
    """Split audio file into chunks based on silence."""
    if not PYDUB_AVAILABLE:
        raise ImportError("Pydub is required for audio processing. Install with: pip install pydub")
    
    logger.info(f"🎵 Splitting audio into chunks: {os.path.basename(audio_path)}")
    
    try:
        # Load audio
        audio = AudioSegment.from_wav(audio_path)
        
        # Split on silence
        chunks = split_on_silence(
            audio,
            min_silence_len=min_silence_len,
            silence_thresh=silence_thresh,
            keep_silence=keep_silence
        )
        
        if not chunks:
            logger.warning("⚠️  No chunks found, creating single chunk")
            chunks = [audio]
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Save chunks
        chunk_files = []
        for i, chunk in enumerate(chunks):
            if len(chunk) < 1000:  # Skip chunks shorter than 1 second
                continue
                
            chunk_filename = f"chunk_{i:03d}.wav"
            chunk_path = os.path.join(output_dir, chunk_filename)
            chunk.export(chunk_path, format="wav")
            chunk_files.append(chunk_path)
        
        logger.info(f"✅ Created {len(chunk_files)} audio chunks")
        return chunk_files
        
    except Exception as e:
        logger.error(f"❌ Failed to split audio: {e}")
        return []


def create_chunks_structure(file_path, temp_dir, silence_params=None):
    """Create chunks structure from video or audio file."""
    if silence_params is None:
        silence_params = {"min_silence_len": 500, "silence_thresh": -40, "keep_silence": 100}
    
    file_name = Path(file_path).stem
    chunks_dir = os.path.join(temp_dir, file_name, "chunks")
    audio_chunks_dir = os.path.join(chunks_dir, "audio")
    
    # Create directory structure
    os.makedirs(audio_chunks_dir, exist_ok=True)
    
    if is_video_file(file_path):
        # Extract audio from video
        temp_audio_path = os.path.join(temp_dir, f"{file_name}.wav")
        if not extract_audio_from_video(file_path, temp_audio_path):
            return None
        source_audio = temp_audio_path
    elif is_audio_file(file_path):
        source_audio = file_path
    else:
        logger.error(f"❌ Unsupported file type: {file_path}")
        return None
    
    # Split audio into chunks
    chunk_files = split_audio_into_chunks(source_audio, audio_chunks_dir, **silence_params)
    
    if not chunk_files:
        return None
    
    return {
        'video_id': file_name,
        'video_dir': os.path.join(temp_dir, file_name),
        'chunks_dir': chunks_dir,
        'audio_count': len(chunk_files),
        'is_temporary': True
    }


def cleanup_temporary_files(video_info):
    """Clean up temporary files if they were created."""
    if video_info.get('is_temporary') and os.path.exists(video_info['video_dir']):
        try:
            shutil.rmtree(video_info['video_dir'])
            logger.info(f"🧹 Cleaned up temporary files for {video_info['video_id']}")
        except Exception as e:
            logger.warning(f"⚠️  Could not clean up temporary files: {e}")


def check_dependencies():
    """Check if required dependencies are available."""
    dependencies = {
        'moviepy': MOVIEPY_AVAILABLE,
        'pydub': PYDUB_AVAILABLE
    }
    
    missing = [name for name, available in dependencies.items() if not available]
    
    if missing:
        logger.warning("⚠️  Some dependencies are missing:")
        for dep in missing:
            if dep == 'moviepy':
                logger.warning("   MoviePy not available. Video processing will be disabled.")
                logger.info("   Install with: pip install moviepy")
            elif dep == 'pydub':
                logger.warning("   Pydub not available. Audio processing will be disabled.")
                logger.info("   Install with: pip install pydub")
    
    return dependencies
