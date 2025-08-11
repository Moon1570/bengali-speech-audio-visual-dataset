#!/usr/bin/env python3
"""
Progress Tracking Utilities
============================

This module provides utilities for tracking transcription progress including:
- Session management
- Progress persistence
- Video completion tracking
- Historical statistics
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Progress tracking file
PROGRESS_FILE = os.path.join("logs", "transcription_progress.json")


def load_progress():
    """Load transcription progress from file."""
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            logger.warning("⚠️  Could not load progress file, starting fresh")
    
    return {
        "sessions": [],
        "completed_videos": {},
        "last_updated": None
    }


def save_progress(progress_data):
    """Save transcription progress to file."""
    try:
        progress_data["last_updated"] = datetime.now().isoformat()
        os.makedirs(os.path.dirname(PROGRESS_FILE), exist_ok=True)
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, indent=2, ensure_ascii=False)
    except IOError as e:
        logger.warning(f"⚠️  Could not save progress: {e}")


def update_video_progress(video_id, model, status, chunks_transcribed=0, total_chunks=0):
    """Update progress for a specific video."""
    progress = load_progress()
    
    video_key = f"{video_id}_{model}"
    progress["completed_videos"][video_key] = {
        "video_id": video_id,
        "model": model,
        "status": status,  # "completed", "partial", "failed", "pending"
        "chunks_transcribed": chunks_transcribed,
        "total_chunks": total_chunks,
        "completion_rate": (chunks_transcribed / total_chunks * 100) if total_chunks > 0 else 0,
        "last_updated": datetime.now().isoformat()
    }
    
    save_progress(progress)


def start_session(session_info):
    """Start a new transcription session and track it."""
    progress = load_progress()
    
    session = {
        "session_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "start_time": datetime.now().isoformat(),
        "end_time": None,
        "model": session_info.get("model"),
        "mode": session_info.get("mode"),  # "single", "batch"
        "target_path": session_info.get("target_path"),
        "videos_processed": 0,
        "videos_successful": 0,
        "videos_failed": 0,
        "total_chunks": 0,
        "chunks_transcribed": 0,
        "status": "running"
    }
    
    progress["sessions"].append(session)
    save_progress(progress)
    
    logger.info(f"📊 Started session: {session['session_id']}")
    return session["session_id"]


def end_session(session_id, final_stats):
    """End a transcription session and update final statistics."""
    progress = load_progress()
    
    for session in progress["sessions"]:
        if session.get("session_id") == session_id:
            session.update({
                "end_time": datetime.now().isoformat(),
                "videos_processed": final_stats.get("videos_processed", 0),
                "videos_successful": final_stats.get("videos_successful", 0),
                "videos_failed": final_stats.get("videos_failed", 0),
                "total_chunks": final_stats.get("total_chunks", 0),
                "chunks_transcribed": final_stats.get("chunks_transcribed", 0),
                "status": "completed",
                "duration_seconds": final_stats.get("duration_seconds", 0)
            })
            break
    
    save_progress(progress)
    logger.info(f"📊 Ended session: {session_id}")


def get_session_stats():
    """Get overall session statistics."""
    progress = load_progress()
    
    total_sessions = len(progress["sessions"])
    completed_sessions = len([s for s in progress["sessions"] if s.get("status") == "completed"])
    total_videos_processed = sum(s.get("videos_processed", 0) for s in progress["sessions"])
    total_successful = sum(s.get("videos_successful", 0) for s in progress["sessions"])
    
    return {
        "total_sessions": total_sessions,
        "completed_sessions": completed_sessions,
        "total_videos_processed": total_videos_processed,
        "total_successful": total_successful,
        "success_rate": (total_successful / total_videos_processed * 100) if total_videos_processed > 0 else 0
    }


def show_progress_history():
    """Display detailed progress history and statistics."""
    progress = load_progress()
    
    logger.info("=" * 70)
    logger.info("📊 TRANSCRIPTION PROGRESS HISTORY")
    logger.info("=" * 70)
    
    if not progress["sessions"]:
        logger.info("📋 No transcription sessions found.")
        return
    
    # Overall statistics
    stats = get_session_stats()
    logger.info(f"🔄 Total sessions: {stats['total_sessions']}")
    logger.info(f"✅ Completed sessions: {stats['completed_sessions']}")
    logger.info(f"🎯 Total videos processed: {stats['total_videos_processed']}")
    logger.info(f"📈 Overall success rate: {stats['success_rate']:.1f}%")
    logger.info(f"📅 Last updated: {progress.get('last_updated', 'Never')}")
    
    logger.info("\n" + "─" * 70)
    logger.info("📋 RECENT SESSIONS")
    logger.info("─" * 70)
    
    # Show last 10 sessions
    recent_sessions = sorted(progress["sessions"], 
                           key=lambda x: x.get("start_time", ""), 
                           reverse=True)[:10]
    
    for session in recent_sessions:
        start_time = datetime.fromisoformat(session["start_time"]).strftime("%Y-%m-%d %H:%M:%S")
        duration = "Running..." if session.get("status") == "running" else f"{session.get('duration_seconds', 0):.1f}s"
        
        logger.info(f"🗓️  {session['session_id']} | {start_time}")
        logger.info(f"   📱 Model: {session.get('model', 'N/A')} | Mode: {session.get('mode', 'N/A')}")
        logger.info(f"   📊 Videos: {session.get('videos_successful', 0)}/{session.get('videos_processed', 0)} | Duration: {duration}")
        logger.info(f"   📁 Path: {session.get('target_path', 'N/A')}")
        logger.info("")
    
    # Show video completion status
    if progress["completed_videos"]:
        logger.info("─" * 70)
        logger.info("🎬 VIDEO COMPLETION STATUS")
        logger.info("─" * 70)
        
        for video_key, video_data in list(progress["completed_videos"].items())[-20:]:  # Last 20 videos
            status_emoji = {"completed": "✅", "partial": "⚠️", "failed": "❌", "pending": "⏳"}
            emoji = status_emoji.get(video_data["status"], "❓")
            
            logger.info(f"{emoji} {video_data['video_id']} ({video_data['model']})")
            logger.info(f"   📊 {video_data['chunks_transcribed']}/{video_data['total_chunks']} chunks ({video_data['completion_rate']:.1f}%)")
            logger.info(f"   📅 {datetime.fromisoformat(video_data['last_updated']).strftime('%Y-%m-%d %H:%M:%S')}")
    
    logger.info("=" * 70)


def clear_progress_history():
    """Clear all progress history data."""
    try:
        if os.path.exists(PROGRESS_FILE):
            # Create backup before clearing
            backup_file = f"{PROGRESS_FILE}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.rename(PROGRESS_FILE, backup_file)
            logger.info(f"📦 Progress history backed up to: {backup_file}")
        
        # Initialize fresh progress file
        fresh_progress = {
            "sessions": [],
            "completed_videos": {},
            "last_updated": datetime.now().isoformat()
        }
        save_progress(fresh_progress)
        
        logger.info("🧹 Progress history cleared successfully!")
        logger.info("💡 You can restore from the backup file if needed.")
        
    except Exception as e:
        logger.error(f"❌ Error clearing progress history: {e}")
