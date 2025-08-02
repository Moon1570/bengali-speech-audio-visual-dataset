import yt_dlp
import json
import os
import logging

# Set up logging
logging.basicConfig(
    filename='video_downloader.log',  # Log to this file
    level=logging.INFO,  # Log level (INFO will capture info, warnings, and errors)
    format='%(asctime)s - %(levelname)s - %(message)s'  # Log message format
)

# Directory to store downloaded videos
DOWNLOAD_DIR = 'downloads'

# Load video metadata from the JSON file
def load_video_metadata(file_path='news_videos_metadata.json'):
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    else:
        print("Metadata file not found!")
        logging.error("Metadata file not found!")
        return []

# Check if the video has already been downloaded by looking for its file
def is_video_downloaded(video_id):
    return os.path.exists(f'{DOWNLOAD_DIR}/{video_id}.mp4')  # Assuming video files are saved as .mp4

# Download video using yt-dlp
def download_video(video_id):
    video_url = f'https://www.youtube.com/watch?v={video_id}'
    
    # Define options for yt-dlp
    ydl_opts = {
        'format': 'best',  # Download the best available quality
        'outtmpl': f'{DOWNLOAD_DIR}/{video_id}.%(ext)s',  # Save file with video ID as filename
        'noplaylist': True,  # Only download the video, not a playlist
    }

    # Download the video if not already downloaded
    if not is_video_downloaded(video_id):
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                ydl.download([video_url])
                print(f"Downloaded video {video_id}")
                logging.info(f"Downloaded video {video_id}")
            except yt_dlp.utils.DownloadError as e:
                print(f"Error downloading video {video_id}: {e}")
                logging.error(f"Error downloading video {video_id}: {e}")
            except Exception as e:
                print(f"Unexpected error downloading video {video_id}: {e}")
                logging.error(f"Unexpected error downloading video {video_id}: {e}")
    else:
        print(f"Video {video_id} already downloaded. Skipping...")
        logging.info(f"Video {video_id} already downloaded. Skipping...")

# Main function to download videos from the metadata
def download_videos_from_metadata(metadata_file='news_videos_metadata.json'):
    # Load the metadata
    video_metadata = load_video_metadata(metadata_file)
    
    # Create DOWNLOAD_DIR if it doesn't exist
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)

    # Loop through the metadata and download videos
    for video in video_metadata:
        video_id = video['video_id']
        print(f"Checking if video {video_id} is already downloaded...")
        logging.info(f"Checking if video {video_id} is already downloaded...")
        download_video(video_id)

if __name__ == '__main__':
    download_videos_from_metadata()