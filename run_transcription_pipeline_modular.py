#!/usr/bin/env python3
"""
Bengali Speech Audio-Visual Dataset - Independent Transcription Pipeline
========================================================================

This script provides an independent transcription pipeline that can work with:
1. Raw video files (MP4, AVI, etc.) - extracts audio and transcribes
2. Raw audio files (WAV, MP3, etc.) - transcribes directly
3. Pre-processed chunks from main pipeline - transcribes existing chunks

Usage:
    python run_transcription_pipeline.py --path video.mp4 --model google
    python run_transcription_pipeline.py --path audio.wav --model whisper
    python run_transcription_pipeline.py --path directory/ --batch --model google
"""

import os
import sys
import argparse
import logging
import time
import tempfile
import shutil

# Import modular utilities
from utils.audio_processing import check_dependencies
from utils.progress_tracking import (
    start_session, end_session, show_progress_history, clear_progress_history
)
from utils.file_discovery import (
    find_processable_videos, validate_video_structure, 
    prepare_video_for_transcription, check_transcription_status
)
from utils.transcription_manager import (
    transcribe_video, transcribe_video_both_models, generate_transcription_report, process_batch_items
)

# Create logs directory
os.makedirs("logs", exist_ok=True)

# Configure logging
log_file_path = os.path.join("logs", "transcription_pipeline.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(log_file_path, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Independent transcription pipeline for Bengali speech audio-visual dataset",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Transcribe a video file directly
  python run_transcription_pipeline.py --path video.mp4 --model google
  
  # Transcribe an audio file directly  
  python run_transcription_pipeline.py --path audio.wav --model whisper
  
  # Batch process directory with mixed files
  python run_transcription_pipeline.py --path data/videos/ --batch --model google
  
  # Process pre-processed chunks (from main pipeline)
  python run_transcription_pipeline.py --path outputs/video_name --model google
  
  # Show historical progress and statistics
  python run_transcription_pipeline.py --show-history
        """
    )
    
    parser.add_argument(
        "--path",
        type=str,
        help="Path to video/audio file, directory with media files, or pre-processed video directory"
    )
    
    parser.add_argument(
        "--model",
        choices=["whisper", "google", "both"],
        default="google",
        help="Transcription model to use (default: google). Use 'both' to run both models and save transcription.txt in separate folders"
    )
    
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Process all files in the specified directory"
    )
    
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-transcription even if already completed"
    )
    
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Generate status report without performing transcription"
    )
    
    parser.add_argument(
        "--show-history",
        action="store_true",
        help="Show historical progress and session statistics"
    )
    
    parser.add_argument(
        "--clear-history",
        action="store_true",
        help="Clear all historical progress data (use with caution)"
    )
    
    # Audio processing parameters
    parser.add_argument(
        "--silence-thresh",
        type=int,
        default=-40,
        help="Silence threshold in dB for splitting audio (default: -40)"
    )
    
    parser.add_argument(
        "--min-silence-len",
        type=int,
        default=500,
        help="Minimum silence length in ms for splitting (default: 500)"
    )
    
    parser.add_argument(
        "--keep-silence",
        type=int,
        default=100,
        help="Silence padding in ms (default: 100)"
    )
    
    args = parser.parse_args()
    
    # Check dependencies
    dependencies = check_dependencies()
    if not dependencies['moviepy']:
        logger.warning("⚠️  MoviePy not available. Video processing will be disabled.")
        logger.info("   Install with: pip install moviepy")
    
    if not dependencies['pydub']:
        logger.warning("⚠️  Pydub not available. Audio processing will be disabled.")
        logger.info("   Install with: pip install pydub")
    
    # Handle special commands that don't require path
    if args.show_history:
        show_progress_history()
        sys.exit(0)
    
    if args.clear_history:
        clear_progress_history()
        sys.exit(0)
    
    # Validate path is provided for normal operations
    if not args.path:
        logger.error("❌ --path argument is required")
        parser.print_help()
        sys.exit(1)
    
    # Validate path exists
    if not os.path.exists(args.path):
        logger.error(f"❌ Path does not exist: {args.path}")
        sys.exit(1)
    
    logger.info("🚀 Starting Independent Bengali Speech Transcription Pipeline")
    logger.info(f"📁 Target path: {args.path}")
    logger.info(f"🤖 Model: {args.model}")
    logger.info(f"🔄 Batch mode: {args.batch}")
    logger.info(f"💪 Force retranscribe: {args.force}")
    
    # Prepare silence detection parameters
    silence_params = {
        "min_silence_len": args.min_silence_len,
        "silence_thresh": args.silence_thresh,
        "keep_silence": args.keep_silence
    }
    
    # Start session tracking
    session_info = {
        "model": args.model,
        "mode": "batch" if args.batch else "single",
        "target_path": args.path
    }
    session_id = start_session(session_info)
    
    # Create temporary directory for processing
    temp_dir = tempfile.mkdtemp(prefix="transcription_")
    logger.info(f"📂 Using temporary directory: {temp_dir}")
    
    try:
        if args.batch:
            # Batch processing mode
            if not os.path.isdir(args.path):
                logger.error(f"❌ Batch mode requires a directory, got: {args.path}")
                sys.exit(1)
                
            logger.info("🔍 Scanning for processable files...")
            processable_items = find_processable_videos(args.path)
            
            if not processable_items:
                logger.warning(f"⚠️  No processable files found in {args.path}")
                logger.info("   Looking for: video files (.mp4, .avi, etc.), audio files (.wav, .mp3, etc.), or pre-processed directories")
                end_session(session_id, {"videos_processed": 0, "videos_successful": 0, "videos_failed": 0, 
                                       "total_chunks": 0, "chunks_transcribed": 0, "duration_seconds": 0})
                sys.exit(1)
            
            logger.info(f"📦 Found {len(processable_items)} processable items")
            
            if args.report_only:
                # Generate report for pre-processed items only
                pre_processed = [item for item in processable_items if not item.get('needs_processing', False)]
                if pre_processed:
                    generate_transcription_report(pre_processed, args.model)
                else:
                    logger.info("📋 No pre-processed items found for report generation.")
                logger.info("📋 Report generation complete. Exiting without transcription.")
                end_session(session_id, {"videos_processed": 0, "videos_successful": 0, "videos_failed": 0,
                                       "total_chunks": 0, "chunks_transcribed": 0, "duration_seconds": 0})
                sys.exit(0)
            
            # Process all items
            successful, failed, total_chunks, final_transcribed, duration = process_batch_items(
                processable_items, args.model, args.force, temp_dir, silence_params
            )
            
            # End session tracking
            final_stats = {
                "videos_processed": len(processable_items),
                "videos_successful": successful,
                "videos_failed": failed,
                "total_chunks": total_chunks,
                "chunks_transcribed": final_transcribed,
                "duration_seconds": duration
            }
            end_session(session_id, final_stats)
            
            logger.info("=" * 60)
            logger.info(f"🏁 BATCH PROCESSING COMPLETE")
            logger.info(f"✅ Successful: {successful}")
            logger.info(f"❌ Failed: {failed}")
            logger.info(f"📊 Success rate: {(successful/(successful+failed)*100):.1f}%" if (successful+failed) > 0 else "N/A")
            logger.info(f"⏱️  Total duration: {duration:.1f} seconds")
            if len(processable_items) > 0:
                logger.info(f"⚡ Processing rate: {len(processable_items)/duration:.2f} items/second")
            if final_transcribed > 0:
                logger.info(f"🎵 Chunk transcription rate: {final_transcribed/duration:.1f} chunks/second")
            logger.info("=" * 60)
            
        else:
            # Single file/directory processing mode
            from utils.audio_processing import is_video_file, is_audio_file
            from pathlib import Path
            
            if os.path.isfile(args.path):
                # Single file
                if not (is_video_file(args.path) or is_audio_file(args.path)):
                    logger.error(f"❌ Unsupported file type: {args.path}")
                    logger.info("   Supported: video files (.mp4, .avi, etc.) and audio files (.wav, .mp3, etc.)")
                    sys.exit(1)
                
                file_name = Path(args.path).stem
                item_info = {
                    'video_id': file_name,
                    'file_path': args.path,
                    'file_type': 'video' if is_video_file(args.path) else 'audio',
                    'needs_processing': True
                }
                
                # Prepare for transcription
                video_info = prepare_video_for_transcription(item_info, temp_dir, silence_params)
                if video_info is None:
                    logger.error(f"❌ Failed to prepare {args.path} for transcription")
                    sys.exit(1)
                
            elif os.path.isdir(args.path):
                # Check if it's a pre-processed directory
                is_valid, result = validate_video_structure(args.path)
                if is_valid:
                    video_info = result
                else:
                    logger.error(f"❌ {result}")
                    logger.info("   For batch processing of raw files, use --batch flag")
                    sys.exit(1)
            else:
                logger.error(f"❌ Invalid path: {args.path}")
                sys.exit(1)
            
            if args.report_only and not video_info.get('needs_processing', False):
                if args.model == "both":
                    # For both models, check both google and whisper status
                    google_status = check_transcription_status(video_info['chunks_dir'], "google")
                    whisper_status = check_transcription_status(video_info['chunks_dir'], "whisper")
                    logger.info("=" * 60)
                    logger.info(f"📊 TRANSCRIPTION STATUS: {video_info['video_id']}")
                    logger.info("=" * 60)
                    logger.info(f"🤖 Model: BOTH (Google + Whisper)")
                    logger.info(f"🎵 Audio chunks: {google_status['audio_count']}")
                    logger.info(f"📝 Google transcribed: {google_status['text_count']}")
                    logger.info(f"📝 Whisper transcribed: {whisper_status['text_count']}")
                    logger.info(f"✅ Google complete: {'Yes' if google_status['complete'] else 'No'}")
                    logger.info(f"✅ Whisper complete: {'Yes' if whisper_status['complete'] else 'No'}")
                    if google_status['audio_count'] > 0:
                        google_rate = (google_status['text_count'] / google_status['audio_count']) * 100
                        whisper_rate = (whisper_status['text_count'] / whisper_status['audio_count']) * 100
                        logger.info(f"📈 Google completion rate: {google_rate:.1f}%")
                        logger.info(f"📈 Whisper completion rate: {whisper_rate:.1f}%")
                    total_transcribed = google_status['text_count'] + whisper_status['text_count']
                else:
                    status = check_transcription_status(video_info['chunks_dir'], args.model)
                    total_transcribed = status['text_count']
                    logger.info("=" * 60)
                    logger.info(f"📊 TRANSCRIPTION STATUS: {video_info['video_id']}")
                    logger.info("=" * 60)
                    logger.info(f"🤖 Model: {args.model}")
                    logger.info(f"🎵 Audio chunks: {status['audio_count']}")
                    logger.info(f"📝 Transcribed: {status['text_count']}")
                    logger.info(f"✅ Complete: {'Yes' if status['complete'] else 'No'}")
                    if status['audio_count'] > 0:
                        completion_rate = (status['text_count'] / status['audio_count']) * 100
                        logger.info(f"📈 Completion rate: {completion_rate:.1f}%")
                
                logger.info("=" * 60)
                end_session(session_id, {"videos_processed": 1, "videos_successful": 0, "videos_failed": 0,
                                       "total_chunks": video_info['audio_count'], "chunks_transcribed": total_transcribed, 
                                       "duration_seconds": 0})
                sys.exit(0)
            
            # Process single item
            start_time = time.time()
            if args.model == "both":
                success = transcribe_video_both_models(video_info, args.force)
            else:
                success = transcribe_video(video_info, args.model, args.force)
            duration = time.time() - start_time
            
            # Get final transcription count
            try:
                if args.model == "both":
                    google_status = check_transcription_status(video_info['chunks_dir'], "google")
                    whisper_status = check_transcription_status(video_info['chunks_dir'], "whisper")
                    final_transcribed = google_status['text_count'] + whisper_status['text_count']
                else:
                    final_status = check_transcription_status(video_info['chunks_dir'], args.model)
                    final_transcribed = final_status['text_count']
            except:
                final_transcribed = 0
            
            # Process single item
            start_time = time.time()
            success = transcribe_video(video_info, args.model, args.force)
            duration = time.time() - start_time
            
            # Get final transcription count
            try:
                final_status = check_transcription_status(video_info['chunks_dir'], args.model)
                final_transcribed = final_status['text_count']
            except:
                final_transcribed = 0
            
            # End session tracking
            final_stats = {
                "videos_processed": 1,
                "videos_successful": 1 if success else 0,
                "videos_failed": 0 if success else 1,
                "total_chunks": video_info['audio_count'],
                "chunks_transcribed": final_transcribed,
                "duration_seconds": duration
            }
            end_session(session_id, final_stats)
            
            if success:
                logger.info("🎉 Single file transcription completed successfully!")
                logger.info(f"⏱️  Duration: {duration:.1f} seconds")
                if final_transcribed > 0:
                    logger.info(f"⚡ Rate: {final_transcribed/duration:.1f} chunks/second")
            else:
                logger.error("❌ Single file transcription failed!")
                sys.exit(1)
                
    finally:
        # Clean up temporary directory
        try:
            shutil.rmtree(temp_dir)
            logger.info(f"🧹 Cleaned up temporary directory: {temp_dir}")
        except Exception as e:
            logger.warning(f"⚠️  Could not clean up temporary directory: {e}")


if __name__ == "__main__":
    main()
