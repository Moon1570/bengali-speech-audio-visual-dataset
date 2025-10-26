#!/usr/bin/env python3
"""
File Discovery Utilities
=========================

This module provides utilities for discovering and organizing media files:
- Finding processable videos and audio files
- Detecting pre-processed directories
- Organizing file structures for transcription
"""

import os
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


def find_processable_videos(root_dir):
    """
    Find all processable items in a directory.
    
    Returns a list of items that can be processed, including:
    - Pre-processed video directories (with chunks/audio/*.wav)
    - Raw video files
    - Raw audio files
    """
    from .audio_processing import is_video_file, is_audio_file
    
    processable = []
    
    if not os.path.isdir(root_dir):
        logger.error(f"❌ Not a directory: {root_dir}")
        return processable
    
    for item in os.listdir(root_dir):
        item_path = os.path.join(root_dir, item)
        
        if os.path.isdir(item_path):
            # Check if it's a pre-processed directory
            chunks_dir = os.path.join(item_path, "chunks")
            audio_dir = os.path.join(chunks_dir, "audio")
            
            if os.path.exists(audio_dir):
                wav_files = [f for f in os.listdir(audio_dir) if f.endswith(".wav")]
                if wav_files:
                    processable.append({
                        'video_id': item,
                        'video_dir': item_path,
                        'chunks_dir': chunks_dir,
                        'audio_count': len(wav_files),
                        'needs_processing': False,
                        'file_type': 'pre_processed'
                    })
                    
        elif os.path.isfile(item_path):
            # Check if it's a raw video or audio file
            if is_video_file(item_path):
                file_name = Path(item_path).stem
                processable.append({
                    'video_id': file_name,
                    'file_path': item_path,
                    'file_type': 'video',
                    'needs_processing': True
                })
            elif is_audio_file(item_path):
                file_name = Path(item_path).stem
                processable.append({
                    'video_id': file_name,
                    'file_path': item_path,
                    'file_type': 'audio',
                    'needs_processing': True
                })
                
    return processable


def check_transcription_status(chunks_dir, model):
    """Check if transcription already exists and get status."""
    text_dir = os.path.join(chunks_dir, "text" if model == "whisper" else "text_google")
    audio_dir = os.path.join(chunks_dir, "audio")
    
    if not os.path.exists(text_dir):
        return {"exists": False, "complete": False, "audio_count": 0, "text_count": 0}
    
    if not os.path.exists(audio_dir):
        return {"exists": False, "complete": False, "audio_count": 0, "text_count": 0}
    
    audio_files = [f for f in os.listdir(audio_dir) if f.endswith(".wav")]
    text_files = [f for f in os.listdir(text_dir) if f.endswith(".txt")]
    
    audio_count = len(audio_files)
    text_count = len(text_files)
    
    return {
        "exists": True,
        "complete": audio_count == text_count and audio_count > 0,
        "audio_count": audio_count,
        "text_count": text_count
    }


def prepare_video_for_transcription(item_info, temp_dir, silence_params):
    """
    Prepare a video item for transcription.
    
    Args:
        item_info: Dictionary containing video information
        temp_dir: Temporary directory for processing
        silence_params: Parameters for silence detection
        
    Returns:
        Dictionary with video information ready for transcription
    """
    from .audio_processing import create_chunks_structure
    
    if not item_info.get('needs_processing', False):
        # Already pre-processed
        return item_info
    
    # Process raw file
    file_path = item_info['file_path']
    logger.info(f"🔄 Processing raw file: {os.path.basename(file_path)}")
    
    # Create chunks structure
    video_info = create_chunks_structure(file_path, temp_dir, silence_params)
    
    if video_info is None:
        logger.error(f"❌ Failed to create chunks for: {file_path}")
        return None
    
    # Add original file information
    video_info['original_file_path'] = file_path
    video_info['input_folder'] = os.path.dirname(file_path)
    
    return video_info


def copy_transcripts_to_outputs(video_info, model):
    """
    Copy transcription results to organized outputs directory.
    
    Args:
        video_info: Dictionary containing video information
        model: Transcription model used ('whisper' or 'google')
    """
    # Determine whether this was a temporary (raw-file) processing or a pre-processed input
    is_temporary = video_info.get('is_temporary', False)
    
    video_id = video_info['video_id']
    chunks_dir = video_info['chunks_dir']
    
    # Source text directory
    text_dir = os.path.join(chunks_dir, "text" if model == "whisper" else "text_google")
    
    if not os.path.exists(text_dir):
        logger.warning(f"⚠️  No transcription results found for {video_id}")
        return
    
    try:
        if is_temporary:
            # Target outputs directory for temporary/raw-file processing
            outputs_dir = os.path.join("outputs", video_id)
            output_chunks_dir = os.path.join(outputs_dir, "chunks")
            output_text_dir = os.path.join(output_chunks_dir, "text" if model == "whisper" else "text_google")

            # Create target directory structure
            os.makedirs(output_text_dir, exist_ok=True)

            # Copy transcription files
            import shutil
            text_files = [f for f in os.listdir(text_dir) if f.endswith(".txt")]

            for text_file in text_files:
                src_path = os.path.join(text_dir, text_file)
                dst_path = os.path.join(output_text_dir, text_file)
                shutil.copy2(src_path, dst_path)

            logger.info(f"📋 Copied {len(text_files)} transcripts to: {output_text_dir}")

            # Also copy audio chunks for reference
            audio_dir = os.path.join(chunks_dir, "audio")
            output_audio_dir = os.path.join(output_chunks_dir, "audio")

            if os.path.exists(audio_dir):
                os.makedirs(output_audio_dir, exist_ok=True)
                wav_files = [f for f in os.listdir(audio_dir) if f.endswith(".wav")]

                for wav_file in wav_files:
                    src_path = os.path.join(audio_dir, wav_file)
                    dst_path = os.path.join(output_audio_dir, wav_file)
                    shutil.copy2(src_path, dst_path)

                logger.info(f"🎵 Copied {len(wav_files)} audio chunks to: {output_audio_dir}")

            # Create metadata file
            metadata = {
                "video_id": video_id,
                "model": model,
                "audio_chunks": video_info.get('audio_count', 0),
                "transcription_files": len(text_files),
                "processed_timestamp": str(datetime.now()),
                "source_file": video_info.get('source_file', 'unknown')
            }

            metadata_path = os.path.join(outputs_dir, "metadata.json")
            import json
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            logger.info(f"📄 Created metadata file: {metadata_path}")

        else:
            # Pre-processed input: create sibling transcripts_{model} folder next to the input directory
            # Prefer video_dir if available, otherwise try chunks_dir parent
            video_dir = video_info.get('video_dir')
            if video_dir and os.path.exists(video_dir):
                parent_dir = os.path.dirname(video_dir)
            else:
                # Fallback: use parent of chunks_dir
                parent_dir = os.path.dirname(os.path.dirname(chunks_dir))

            target_folder = os.path.join(parent_dir, f"transcripts_{model}")
            os.makedirs(target_folder, exist_ok=True)

            # Combine chunks into single transcript file named <video_id>.txt
            transcript_path = os.path.join(target_folder, f"{video_id}.txt")
            combined = combine_chunks_to_single_file(text_dir, transcript_path)

            # Copy individual chunk files for reference
            import shutil
            chunks_out_dir = os.path.join(target_folder, "chunks")
            os.makedirs(chunks_out_dir, exist_ok=True)
            text_files = [f for f in os.listdir(text_dir) if f.endswith(".txt")]
            for text_file in text_files:
                src_path = os.path.join(text_dir, text_file)
                dst_path = os.path.join(chunks_out_dir, text_file)
                shutil.copy2(src_path, dst_path)

            logger.info(f"📄 Saved combined transcript to: {transcript_path} (combined {combined} chunks)")
            logger.info(f"📋 Copied {len(text_files)} individual chunk transcripts to: {chunks_out_dir}")

            # Create a lightweight metadata file next to transcripts
            metadata = {
                "video_id": video_id,
                "model": model,
                "audio_chunks": video_info.get('audio_count', 0),
                "transcription_files": len(text_files),
                "processed_timestamp": str(datetime.now()),
                "source_dir": video_dir or chunks_dir
            }
            metadata_path = os.path.join(target_folder, "metadata.json")
            import json
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            logger.info(f"📄 Created metadata file: {metadata_path}")
    
    except Exception as e:
        logger.error(f"❌ Failed to copy transcripts for {video_id}: {e}")


def save_both_models_transcripts(video_info, original_file_path=None):
    """
    Save transcription results for both Google and Whisper models in separate folders 
    with transcription files named same as the original video file (for "both" model option).
    
    Args:
        video_info: Dictionary containing video information
        original_file_path: Path to the original input file
    """
    video_id = video_info['video_id']
    chunks_dir = video_info['chunks_dir']
    
    # Determine the input folder and original filename
    if original_file_path:
        input_folder = os.path.dirname(original_file_path)
        original_filename = os.path.splitext(os.path.basename(original_file_path))[0]
    else:
        # Try to find the input folder from video_info
        input_folder = video_info.get('input_folder', '.')
        original_filename = video_id
    
    models = [
        ("google", "text_google"),
        ("whisper", "text")
    ]
    
    saved_count = 0
    
    for model, text_dir_name in models:
        text_dir = os.path.join(chunks_dir, text_dir_name)
        
        if not os.path.exists(text_dir):
            logger.warning(f"⚠️  No {model} transcription results found for {video_id}")
            continue
        
        try:
            # Decide target folder. Prefer parent of pre-processed video_dir so transcripts sit next to the video folder.
            if not original_file_path:
                video_dir = video_info.get('video_dir')
                if video_dir and os.path.exists(video_dir):
                    parent_dir = os.path.dirname(video_dir)
                    model_folder = os.path.join(parent_dir, f"transcripts_{model}")
                else:
                    # Fallback to input_folder (could be '.')
                    model_folder = os.path.join(input_folder, f"transcripts_{model}")
            else:
                # For raw/original file input, prefer the parent of the input folder so
                # transcripts are placed alongside the folder that contains the input files
                parent_of_input = os.path.dirname(input_folder)
                model_folder = os.path.join(parent_of_input, f"transcripts_{model}")

            os.makedirs(model_folder, exist_ok=True)

            # Create transcription file with same name as original video file + .txt extension
            transcript_filename = f"{original_filename}.txt"
            transcript_file_path = os.path.join(model_folder, transcript_filename)
            
            # Combine all chunks into the transcription file
            valid_chunks = combine_chunks_to_single_file(text_dir, transcript_file_path)
            
            if valid_chunks > 0:
                logger.info(f"📄 Saved {model} transcription: {transcript_file_path}")
                logger.info(f"📊 Combined {valid_chunks} chunks for {model}")
                saved_count += 1
            else:
                logger.warning(f"⚠️  No valid content found for {model} transcription")
                
        except Exception as e:
            logger.error(f"❌ Error saving {model} transcription: {e}")
    
    if saved_count > 0:
        logger.info(f"✅ Successfully saved transcriptions for {saved_count} model(s) in separate folders")
    else:
        logger.warning(f"⚠️  No transcriptions were saved for {video_id}")


def combine_chunks_to_single_file(text_dir, output_file_path):
    """
    Combine all chunk transcript files into a single file.
    
    Args:
        text_dir: Directory containing chunk text files
        output_file_path: Path where the combined file should be saved
    
    Returns:
        int: Number of chunks combined
    """
    text_files = [f for f in os.listdir(text_dir) if f.endswith(".txt")]
    text_files.sort()  # Ensure proper order
    
    combined_content = []
    valid_chunks = 0
    
    for text_file in text_files:
        text_path = os.path.join(text_dir, text_file)
        try:
            with open(text_path, 'r', encoding='utf-8') as tf:
                content = tf.read().strip()
                if content and content not in ['[Unrecognized Speech]', '']:
                    combined_content.append(content)
                    valid_chunks += 1
        except Exception as e:
            logger.warning(f"⚠️  Error reading {text_file}: {e}")
    
    # Write combined content to output file
    with open(output_file_path, 'w', encoding='utf-8') as f:
        f.write(' '.join(combined_content))
    
    return valid_chunks


def save_transcripts_to_input_folder(video_info, model, original_file_path=None):
    """
    Save transcription results directly to the input folder alongside the source file.
    For batch processing, creates a single file with the same name as the input file.
    
    Args:
        video_info: Dictionary containing video information
        model: Transcription model used ('whisper' or 'google')
        original_file_path: Path to the original input file
    """
    video_id = video_info['video_id']
    chunks_dir = video_info['chunks_dir']
    
    # Source text directory
    text_dir = os.path.join(chunks_dir, "text" if model == "whisper" else "text_google")
    
    if not os.path.exists(text_dir):
        logger.warning(f"⚠️  No transcription results found for {video_id}")
        return
    
    # Determine the input folder and original filename
    if original_file_path:
        input_folder = os.path.dirname(original_file_path)
        original_filename = os.path.splitext(os.path.basename(original_file_path))[0]
    else:
        # Try to find the input folder from video_info
        input_folder = video_info.get('input_folder', '.')
        original_filename = video_id
    
    try:
        # Create model-specific transcription folder at parent level (sibling to video_normal/)
        transcription_folder_name = f"{model}_transcription"
        parent_folder = os.path.dirname(input_folder)  # Go one level up
        transcription_folder = os.path.join(parent_folder, transcription_folder_name)
        os.makedirs(transcription_folder, exist_ok=True)
        
        # Create single transcript file with same name as input file
        transcript_filename = f"{original_filename}.txt"
        transcript_file_path = os.path.join(transcription_folder, transcript_filename)

        # Combine all chunks into a single file
        valid_chunks = combine_chunks_to_single_file(text_dir, transcript_file_path)

        logger.info(f"📄 Saved combined transcript: {transcript_file_path}")
        logger.info(f"📊 Combined {valid_chunks} chunks into single file")

        # Also create the sibling transcripts_{model} directory for detailed chunks
        # Determine the correct location for transcripts folder
        video_dir = video_info.get('video_dir')
        
        if video_dir and os.path.exists(video_dir):
            # Pre-processed directory: put transcripts at same level as video_dir
            parent_dir = os.path.dirname(video_dir)
            transcript_dir = os.path.join(parent_dir, f"transcripts_{model}")
        else:
            # Batch processing of raw files in a directory:
            # Put transcripts at the same level as the input folder
            # Check if input_folder looks like it's part of a structured dataset
            # (e.g., experiments/experiment_data/SSYouTubeonline/video_normal/)
            if os.path.basename(input_folder).startswith('video_') or \
               'video_normal' in input_folder or \
               'video_cropped' in input_folder or \
               'video_bbox' in input_folder:
                # This is a video subfolder - put transcripts at parent level
                parent_of_input = os.path.dirname(input_folder)
                transcript_dir = os.path.join(parent_of_input, f"transcripts_{model}")
            else:
                # Regular folder - put transcripts as sibling
                parent_of_input = os.path.dirname(input_folder) if input_folder != '.' else '.'
                transcript_dir = os.path.join(parent_of_input, f"transcripts_{model}")

        os.makedirs(transcript_dir, exist_ok=True)

        # Copy individual chunk files for detailed reference
        import shutil
        text_files = [f for f in os.listdir(text_dir) if f.endswith(".txt")]

        for text_file in text_files:
            src_path = os.path.join(text_dir, text_file)
            dst_path = os.path.join(transcript_dir, text_file)
            shutil.copy2(src_path, dst_path)

        logger.info(f"📋 Also saved {len(text_files)} individual chunks to: {transcript_dir}")

        # Create a summary file in the transcription folder
        summary_file = os.path.join(transcription_folder, f"{original_filename}_{model}_summary.txt")
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"Transcription Summary\n")
            f.write(f"====================\n\n")
            f.write(f"Source: {original_filename}\n")
            f.write(f"Model: {model}\n")
            f.write(f"Chunks: {len(text_files)}\n")
            f.write(f"Valid chunks: {valid_chunks}\n")
            f.write(f"Timestamp: {datetime.now()}\n\n")
            f.write(f"Combined transcript saved as: {transcript_filename}\n")
            f.write(f"Individual chunks saved in: {os.path.basename(transcript_dir)}/\n\n")
            
            # Include transcription content preview
            for text_file in sorted(text_files):
                text_path = os.path.join(text_dir, text_file)
                try:
                    with open(text_path, 'r', encoding='utf-8') as tf:
                        content = tf.read().strip()
                        if content:
                            f.write(f"{text_file}: {content}\n")
                except Exception as e:
                    f.write(f"{text_file}: [Error reading file: {e}]\n")

        logger.info(f"📄 Created summary file: {summary_file}")

    except Exception as e:
        logger.error(f"❌ Failed to save transcripts to input folder for {video_id}: {e}")


def validate_video_structure(video_path):
    """
    Validate that a video directory has the expected structure.
    
    Args:
        video_path: Path to video directory
        
    Returns:
        Tuple of (is_valid, video_info_dict_or_error_message)
    """
    if not os.path.isdir(video_path):
        return False, f"Path is not a directory: {video_path}"
    
    chunks_dir = os.path.join(video_path, "chunks")
    if not os.path.exists(chunks_dir):
        return False, f"Chunks directory not found: {chunks_dir}"
    
    audio_dir = os.path.join(chunks_dir, "audio")
    if not os.path.exists(audio_dir):
        return False, f"Audio chunks not found: {audio_dir}"
    
    wav_files = [f for f in os.listdir(audio_dir) if f.endswith(".wav")]
    if not wav_files:
        return False, f"No .wav files found in: {audio_dir}"
    
    video_id = os.path.basename(video_path)
    video_info = {
        'video_id': video_id,
        'video_dir': video_path,
        'chunks_dir': chunks_dir,
        'audio_count': len(wav_files),
        'needs_processing': False
    }
    
    return True, video_info
