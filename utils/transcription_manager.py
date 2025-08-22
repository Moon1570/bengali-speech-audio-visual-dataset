#!/usr/bin/env python3
"""
Transcription Management Utilities
==================================

This module provides utilities for managing transcription processes:
- Video transcription coordination
- Status reporting
- Batch processing management
"""

import os
import time
import logging
from tqdm import tqdm

from .progress_tracking import update_video_progress
from .file_discovery import check_transcription_status, copy_transcripts_to_outputs, save_transcripts_to_input_folder, save_both_models_transcripts
from .audio_processing import cleanup_temporary_files

logger = logging.getLogger(__name__)


def transcribe_video_both_models(video_info, force_retranscribe=False):
    """Transcribe a single video using both Google and Whisper models."""
    from utils.transcribe_chunks import transcribe_chunks  # Whisper
    from utils.transcribe_chunks_google import transcribe_chunks_google  # Google
    
    video_id = video_info['video_id']
    chunks_dir = video_info['chunks_dir']
    audio_count = video_info['audio_count']
    
    logger.info(f"🎯 Processing video: {video_id} ({audio_count} chunks) with BOTH models")
    
    models = ["google", "whisper"]
    success_count = 0
    
    for model in models:
        logger.info(f"🔄 Starting {model.upper()} transcription...")
        
        # Check existing transcription status
        status = check_transcription_status(chunks_dir, model)
        
        if status["complete"] and not force_retranscribe:
            logger.info(f"✅ {model.upper()} transcription already complete for {video_id}")
            logger.info(f"   📊 {status['text_count']}/{status['audio_count']} files transcribed")
            update_video_progress(video_id, model, "completed", status['text_count'], status['audio_count'])
            success_count += 1
            continue
        
        if status["exists"] and not status["complete"]:
            logger.info(f"⚠️  Partial {model.upper()} transcription found for {video_id}")
            logger.info(f"   📊 {status['text_count']}/{status['audio_count']} files completed")
            logger.info(f"   🔄 Continuing {model.upper()} transcription...")
            update_video_progress(video_id, model, "partial", status['text_count'], status['audio_count'])
        
        try:
            start_time = time.time()
            
            # Perform transcription
            if model == "whisper":
                logger.info(f"🤖 Starting Whisper transcription for {video_id}")
                transcribe_chunks(chunks_dir, show_progress=True)
            elif model == "google":
                logger.info(f"🗣️  Starting Google Speech Recognition for {video_id}")
                transcribe_chunks_google(chunks_dir, show_progress=True)
                
            # Verify completion
            final_status = check_transcription_status(chunks_dir, model)
            duration = time.time() - start_time
            
            if final_status["complete"]:
                logger.info(f"✅ {model.upper()} transcription completed for {video_id} in {duration:.1f}s")
                logger.info(f"   📊 {final_status['text_count']} files transcribed successfully")
                logger.info(f"   ⚡ Rate: {final_status['text_count']/duration:.1f} chunks/second")
                update_video_progress(video_id, model, "completed", final_status['text_count'], final_status['audio_count'])
                success_count += 1
            else:
                logger.warning(f"⚠️  {model.upper()} transcription incomplete for {video_id}")
                logger.warning(f"   📊 {final_status['text_count']}/{final_status['audio_count']} files completed")
                update_video_progress(video_id, model, "partial", final_status['text_count'], final_status['audio_count'])
                
        except Exception as e:
            logger.error(f"❌ Error transcribing {video_id} with {model.upper()}: {str(e)}")
            update_video_progress(video_id, model, "failed", 0, audio_count)
    
    # Save results using the both models format if at least one succeeded
    if success_count > 0:
        # Save in separate google/whisper folders with transcription.txt
        if video_info.get('is_temporary', False):
            original_file_path = video_info.get('original_file_path')
            save_both_models_transcripts(video_info, original_file_path)
        else:
            # For pre-processed files, also use both models saving
            save_both_models_transcripts(video_info)
        
        logger.info(f"🎉 Both models processing completed! Successfully transcribed with {success_count}/2 models")
        return success_count == 2  # Return True only if both models succeeded
    else:
        logger.error(f"❌ Both models failed for {video_id}")
        return False


def transcribe_video(video_info, model, force_retranscribe=False):
    """Transcribe a single video using the specified model."""
    from utils.transcribe_chunks import transcribe_chunks  # Whisper
    from utils.transcribe_chunks_google import transcribe_chunks_google  # Google
    
    video_id = video_info['video_id']
    chunks_dir = video_info['chunks_dir']
    audio_count = video_info['audio_count']
    
    logger.info(f"🎯 Processing video: {video_id} ({audio_count} chunks)")
    
    # Check existing transcription status
    status = check_transcription_status(chunks_dir, model)
    
    if status["complete"] and not force_retranscribe:
        logger.info(f"✅ Transcription already complete for {video_id} using {model}")
        logger.info(f"   📊 {status['text_count']}/{status['audio_count']} files transcribed")
        update_video_progress(video_id, model, "completed", status['text_count'], status['audio_count'])
        
        # Save to input folder if it's a temporary processing (raw file)
        if video_info.get('is_temporary', False):
            original_file_path = video_info.get('original_file_path')
            save_transcripts_to_input_folder(video_info, model, original_file_path)
        else:
            # For pre-processed files, keep the old behavior
            copy_transcripts_to_outputs(video_info, model)
        return True
    
    if status["exists"] and not status["complete"]:
        logger.info(f"⚠️  Partial transcription found for {video_id}")
        logger.info(f"   📊 {status['text_count']}/{status['audio_count']} files completed")
        logger.info(f"   🔄 Continuing transcription...")
        update_video_progress(video_id, model, "partial", status['text_count'], status['audio_count'])
    
    try:
        start_time = time.time()
        
        # Perform transcription
        if model == "whisper":
            logger.info(f"🤖 Starting Whisper transcription for {video_id}")
            transcribe_chunks(chunks_dir, show_progress=True)
        elif model == "google":
            logger.info(f"🗣️  Starting Google Speech Recognition for {video_id}")
            transcribe_chunks_google(chunks_dir, show_progress=True)
        else:
            logger.error(f"❌ Unknown model: {model}")
            update_video_progress(video_id, model, "failed", 0, audio_count)
            return False
            
        # Verify completion
        final_status = check_transcription_status(chunks_dir, model)
        duration = time.time() - start_time
        
        if final_status["complete"]:
            logger.info(f"✅ Transcription completed for {video_id} in {duration:.1f}s")
            logger.info(f"   📊 {final_status['text_count']} files transcribed successfully")
            logger.info(f"   ⚡ Rate: {final_status['text_count']/duration:.1f} chunks/second")
            update_video_progress(video_id, model, "completed", final_status['text_count'], final_status['audio_count'])
            
            # Save to input folder if it's a temporary processing (raw file)
            if video_info.get('is_temporary', False):
                original_file_path = video_info.get('original_file_path')
                save_transcripts_to_input_folder(video_info, model, original_file_path)
            else:
                # For pre-processed files, keep the old behavior
                copy_transcripts_to_outputs(video_info, model)
            return True
        else:
            logger.warning(f"⚠️  Transcription incomplete for {video_id}")
            logger.warning(f"   📊 {final_status['text_count']}/{final_status['audio_count']} files completed")
            update_video_progress(video_id, model, "partial", final_status['text_count'], final_status['audio_count'])
            return False
            
    except Exception as e:
        logger.error(f"❌ Error transcribing {video_id}: {str(e)}")
        update_video_progress(video_id, model, "failed", 0, audio_count)
        return False


def generate_transcription_report(processable_items, model):
    """Generate a summary report of transcription status."""
    from .progress_tracking import get_session_stats
    
    logger.info("📋 Generating transcription status report...")
    
    # Separate pre-processed from raw files
    pre_processed = [item for item in processable_items if not item.get('needs_processing', False)]
    raw_files = [item for item in processable_items if item.get('needs_processing', False)]
    
    total_items = len(processable_items)
    completed_videos = 0
    partial_videos = 0
    pending_videos = 0
    total_audio_chunks = 0
    total_transcribed_chunks = 0
    
    # Analyze pre-processed items
    for item in pre_processed:
        if model == "both":
            google_status = check_transcription_status(item['chunks_dir'], "google")
            whisper_status = check_transcription_status(item['chunks_dir'], "whisper")
            total_audio_chunks += google_status['audio_count']
            total_transcribed_chunks += google_status['text_count'] + whisper_status['text_count']
            
            # Consider complete if both models are complete
            if google_status['complete'] and whisper_status['complete']:
                completed_videos += 1
            elif google_status['exists'] or whisper_status['exists']:
                partial_videos += 1
            else:
                pending_videos += 1
        else:
            status = check_transcription_status(item['chunks_dir'], model)
            total_audio_chunks += status['audio_count']
            total_transcribed_chunks += status['text_count']
            
            if status['complete']:
                completed_videos += 1
            elif status['exists']:
                partial_videos += 1
            else:
                pending_videos += 1
    
    # Raw files count as pending
    pending_videos += len(raw_files)
    
    # Get session statistics
    session_stats = get_session_stats()
    
    logger.info("=" * 60)
    model_display = "BOTH (Google + Whisper)" if model == "both" else model.upper()
    logger.info(f"📊 TRANSCRIPTION REPORT ({model_display} MODEL)")
    logger.info("=" * 60)
    logger.info(f"📁 Total items found: {total_items}")
    logger.info(f"   📦 Pre-processed directories: {len(pre_processed)}")
    logger.info(f"   📄 Raw media files: {len(raw_files)}")
    logger.info(f"✅ Completed videos: {completed_videos}")
    logger.info(f"⚠️  Partial videos: {partial_videos}")
    logger.info(f"⏳ Pending items: {pending_videos}")
    
    if pre_processed:
        logger.info(f"🎵 Total audio chunks (pre-processed): {total_audio_chunks}")
        logger.info(f"📝 Transcribed chunks: {total_transcribed_chunks}")
        
        if total_audio_chunks > 0:
            if model == "both":
                # For both models, we expect double the chunks
                expected_chunks = total_audio_chunks * 2
                completion_rate = (total_transcribed_chunks / expected_chunks) * 100
                logger.info(f"📈 Overall completion rate (both models): {completion_rate:.1f}%")
            else:
                completion_rate = (total_transcribed_chunks / total_audio_chunks) * 100
                logger.info(f"📈 Overall completion rate: {completion_rate:.1f}%")
    
    logger.info("─" * 60)
    logger.info("📊 HISTORICAL SESSION STATS")
    logger.info("─" * 60)
    logger.info(f"🔄 Total sessions run: {session_stats['total_sessions']}")
    logger.info(f"✅ Completed sessions: {session_stats['completed_sessions']}")
    logger.info(f"🎯 Videos processed (all time): {session_stats['total_videos_processed']}")
    logger.info(f"📈 Success rate (all time): {session_stats['success_rate']:.1f}%")
    
    logger.info("=" * 60)


def process_batch_items(processable_items, model, force_retranscribe, temp_dir, silence_params):
    """
    Process a batch of items for transcription.
    
    Returns:
        Tuple of (successful_count, failed_count, total_chunks, final_transcribed, duration)
    """
    from .file_discovery import prepare_video_for_transcription
    
    successful = 0
    failed = 0
    total_chunks = 0
    start_time = time.time()
    processed_videos = []
    
    for item_info in tqdm(processable_items, desc="Processing items", unit="item"):
        try:
            # Prepare item for transcription
            video_info = prepare_video_for_transcription(item_info, temp_dir, silence_params)
            if video_info is None:
                failed += 1
                continue
            
            processed_videos.append(video_info)
            total_chunks += video_info['audio_count']
            
            # Transcribe using appropriate function based on model
            if model == "both":
                if transcribe_video_both_models(video_info, force_retranscribe):
                    successful += 1
                else:
                    failed += 1
            else:
                if transcribe_video(video_info, model, force_retranscribe):
                    successful += 1
                else:
                    failed += 1
                
        except Exception as e:
            logger.error(f"❌ Error processing {item_info.get('video_id', 'unknown')}: {e}")
            failed += 1
        finally:
            # Clean up temporary files if created
            if 'video_info' in locals() and video_info is not None:
                cleanup_temporary_files(video_info)
    
    duration = time.time() - start_time
    
    # Calculate final statistics
    final_transcribed = 0
    for video_info in processed_videos:
        try:
            if model == "both":
                # For both models, count the total from both google and whisper
                google_status = check_transcription_status(video_info['chunks_dir'], "google")
                whisper_status = check_transcription_status(video_info['chunks_dir'], "whisper")
                final_transcribed += google_status['text_count'] + whisper_status['text_count']
            else:
                status = check_transcription_status(video_info['chunks_dir'], model)
                final_transcribed += status['text_count']
        except:
            pass
    
    return successful, failed, total_chunks, final_transcribed, duration
