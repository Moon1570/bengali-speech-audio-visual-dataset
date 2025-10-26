import os
import argparse
import logging
from tqdm import tqdm

from utils.transcribe_chunks import transcribe_chunks  # Whisper
from utils.transcribe_chunks_google import transcribe_chunks_google  # Google
from utils.prepare_video_folder import prepare_video_dir, is_video_already_processed, mark_video_as_processed
from utils.split_by_silence import split_into_chunks

# ✅ Create logs directory
os.makedirs("logs", exist_ok=True)

# ✅ Configure Logging: Console + File
log_file_path = os.path.join("logs", "pipeline.log")

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
        description="Process a video by splitting it into chunks based on silence, "
                    "and optionally transcribe using Whisper or Google Speech API."
    )
    parser.add_argument(
        "video_path",
        type=str,
        help="Path to the input video file (e.g., downloads/video.mp4)"
    )
    parser.add_argument(
        "--output_root",
        type=str,
        default="outputs",
        help="Directory where processed outputs will be stored (default: outputs)"
    )
    parser.add_argument(
        "--transcribe",
        action="store_true",
        help="Enable transcription after splitting the video into chunks"
    )
    parser.add_argument(
        "--model",
        choices=["whisper", "google"],
        default="whisper",
        help="Transcription model to use (default: whisper). Options: whisper, google"
    )
    parser.add_argument(
        "--filter-faces",
        action="store_true",
        default=True,
        help="Filter chunks to only keep those with detected faces (default: True)"
    )
    parser.add_argument(
        "--no-filter-faces",
        action="store_true",
        help="Disable face filtering (keep all chunks)"
    )
    parser.add_argument(
        "--face-threshold",
        type=float,
        default=0.3,
        help="Minimum ratio of frames with faces to keep chunk (default: 0.3)"
    )
    parser.add_argument(
        "--sample-interval",
        type=float,
        default=0.5,
        help="Interval in seconds for sampling frames for face detection (default: 0.5)"
    )
    parser.add_argument(
        "--refine-chunks",
        action="store_true",
        default=True,
        help="Refine chunks to remove non-face segments (default: True)"
    )
    parser.add_argument(
        "--no-refine-chunks",
        action="store_true",
        help="Disable chunk refinement (keep full chunks)"
    )
    parser.add_argument(
        "--refine-sample-rate",
        type=float,
        default=0.1,
        help="Sample rate in seconds for chunk refinement (default: 0.1)"
    )
    parser.add_argument(
        "--min-face-duration",
        type=float,
        default=0.5,
        help="Minimum duration for face segments in refinement (default: 0.5)"
    )
    parser.add_argument(
        "--min-chunk-duration",
        type=float,
        default=1.0,
        help="Minimum duration for refined chunks (default: 1.0)"
    )
    parser.add_argument(
        "--reduce-noise",
        action="store_true",
        help="Enable noise reduction (spectral gating) during audio processing"
    )
    parser.add_argument(
        "--silence-preset",
        choices=["very_sensitive", "sensitive", "balanced", "conservative", "very_conservative"],
        default="balanced",
        help="Silence detection sensitivity preset (default: balanced). "
             "very_sensitive: word-level, sensitive: phrase-level, balanced: sentence-level, "
             "conservative: paragraph-level, very_conservative: major pauses only"
    )
    parser.add_argument(
        "--custom-silence-thresh",
        type=float,
        help="Custom silence threshold in dBFS (e.g., -40.0). Overrides preset threshold."
    )
    parser.add_argument(
        "--custom-min-silence",
        type=int,
        help="Custom minimum silence length in milliseconds (e.g., 500). Overrides preset."
    )

    args = parser.parse_args()
    video_path = args.video_path
    video_id = os.path.splitext(os.path.basename(video_path))[0]

    logger.info(f"Starting processing for video: {video_id}")

    # ✅ Check if already processed
    if is_video_already_processed(video_id, args.output_root):
        logger.info(f"✅ {video_id} already processed. Skipping.")
        return

    try:
        # ✅ Step 1: Setup folder & extract audio
        logger.info("📂 Preparing video directory and extracting audio...")
        base_dir, video_out, audio_out = prepare_video_dir(video_path, video_id)

        # ✅ Step 2: Silence-based splitting
        logger.info("🔍 Splitting video into chunks based on silence...")
        
        # Determine face filtering setting
        filter_faces = args.filter_faces and not args.no_filter_faces
        refine_chunks = args.refine_chunks and not args.no_refine_chunks
        
        timestamps = split_into_chunks(
            video_out, audio_out, base_dir,
            silence_preset=args.silence_preset,
            custom_silence_thresh=args.custom_silence_thresh,
            custom_min_silence_len=args.custom_min_silence,
            filter_faces=filter_faces,
            face_threshold=args.face_threshold,
            sample_interval=args.sample_interval,
            refine_chunks=refine_chunks,
            refine_sample_rate=args.refine_sample_rate,
            min_face_duration=args.min_face_duration,
            min_chunk_duration=args.min_chunk_duration,
            apply_noise_reduction=args.reduce_noise
        )

        for _ in tqdm(range(len(timestamps)), desc="Creating chunks", unit="chunk"):
            pass
        logger.info(f"✅ Split into {len(timestamps)} chunks.")

        # ✅ Step 3: Optional transcription
        if args.transcribe:
            chunks_dir = os.path.join(base_dir, "chunks")
            logger.info(f"📝 Starting transcription using {args.model}...")
            
            if args.model == "google":
                transcribe_chunks_google(chunks_dir, show_progress=True)
            else:
                transcribe_chunks(chunks_dir, show_progress=True)

            logger.info(f"✅ Transcription completed using {args.model}.")

        # ✅ Step 4: Mark as processed
        metadata = {
            "video_id": video_id,
            "chunks": len(timestamps),
            "timestamps": timestamps
        }
        mark_video_as_processed(video_id, metadata, args.output_root)
        logger.info(f"✅ {video_id} processed and logged successfully.")

    except Exception as e:
        logger.error(f"❌ Error processing video {video_id}: {e}", exc_info=True)


if __name__ == "__main__":
    main()