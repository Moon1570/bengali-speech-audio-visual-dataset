import os
import ffmpeg
import logging

# Set up logging
logging.basicConfig(
    filename='audio_extraction.log',  # Log to this file
    level=logging.INFO,  # Log level (INFO will capture info, warnings, and errors)
    format='%(asctime)s - %(levelname)s - %(message)s'  # Log message format
)

# Directory paths
VIDEO_DIR = 'downloads'  # Where the videos are stored
AUDIO_DIR = 'audio'  # Folder to save extracted audio files

# Ensure AUDIO_DIR exists
if not os.path.exists(AUDIO_DIR):
    os.makedirs(AUDIO_DIR)

# Function to extract audio from a video file
def extract_audio(video_file):
    video_path = os.path.join(VIDEO_DIR, video_file)
    audio_path = os.path.join(AUDIO_DIR, f"{os.path.splitext(video_file)[0]}.wav")  # Output audio in WAV format

    try:
        # Extract audio using ffmpeg
        ffmpeg.input(video_path).output(audio_path).run()
        logging.info(f"Audio extracted for {video_file} to {audio_path}")
    except ffmpeg.Error as e:
        logging.error(f"Error extracting audio from {video_file}: {e}")

# Process all video files in the VIDEO_DIR folder
def extract_audio_from_videos():
    video_files = [f for f in os.listdir(VIDEO_DIR) if f.endswith('.mp4')]  # Assuming .mp4 files

    for video_file in video_files:
        extract_audio(video_file)

if __name__ == '__main__':
    extract_audio_from_videos()