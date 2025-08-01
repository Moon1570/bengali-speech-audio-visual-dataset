import requests
import json
import os
import time
import logging
from dotenv import load_dotenv

# Load the environment variables
load_dotenv()

API_KEY = os.getenv('YT_API_KEY')
if not API_KEY:
    raise ValueError("YouTube API key not found. Please set the YT_API_KEY in your .env file.")

BASE_URL = 'https://www.googleapis.com/youtube/v3/videos'  # Correct endpoint for videos

# Set up logging to log messages to a file and print to console
logging.basicConfig(
    filename='video_fetcher.log',  # Log to this file
    level=logging.INFO,  # Log level (INFO will capture info, warnings, and errors)
    format='%(asctime)s - %(levelname)s - %(message)s'  # Log message format
)

# Load processed video IDs from JSON file
def load_processed_videos(file_path='processed_videos.json'):
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return set(json.load(f))
    return set()

# Save processed video IDs to JSON file
def save_processed_videos(processed_video_ids, file_path='processed_videos.json'):
    with open(file_path, 'w') as f:
        json.dump(list(processed_video_ids), f)

def fetch_video_metadata(video_id, processed_video_ids):
    # Skip if the video has already been processed
    if video_id in processed_video_ids:
        logging.info(f"Video ID {video_id} has already been processed. Skipping...")
        return None

    params = {
        'part': 'snippet,contentDetails,statistics',  # Get basic metadata + content details + statistics (like views, likes)
        'id': video_id,  # Correctly pass the video_id in the 'id' field
        'key': API_KEY
    }
    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()  # Raise an error for bad responses (status code 4xx or 5xx)

        # Debugging: Log all headers to check quota information
        logging.info(f"Response Headers: {response.headers}")
        # log responsee body for debugging
        # logging.info(f"Response Body: {response.text}")

        # Handle quota limit
        remaining_quota = response.headers.get('X-Quota-Remaining')
        if remaining_quota and int(remaining_quota) <= 0:
            logging.warning(f"API quota exceeded. Waiting for an hour before retrying...")
            time.sleep(3600)  # Wait an hour before continuing

        video_data = response.json().get('items', [])
        
        if not video_data:
            logging.warning(f"No data found for video ID: {video_id}")
            return None
        
        video_data = video_data[0]  # Extract the first video item

        # Extract the necessary metadata
        video_metadata = {
            'video_id': video_data['id'],
            'title': video_data['snippet']['title'],
            'description': video_data['snippet']['description'],
            'channel_title': video_data['snippet']['channelTitle'],
            'published_at': video_data['snippet']['publishedAt'],
            'thumbnail': video_data['snippet']['thumbnails']['high']['url'],
            'tags': video_data['snippet'].get('tags', []),  # Tags are optional
            'duration': video_data['contentDetails']['duration'],  # ISO 8601 duration format
            'view_count': video_data['statistics'].get('viewCount', 'N/A'),  # Optional, may not always be available
            'like_count': video_data['statistics'].get('likeCount', 'N/A'),  # Optional
            'comment_count': video_data['statistics'].get('commentCount', 'N/A'),  # Optional
            'fetcbhed_at': time.strftime('%Y-%m-%d %H:%M:%S'),  # Current time when metadata is fetched
            'video_url': f"https://www.youtube.com/watch?v={video_id}",
            'video_path': f"outputs/{video_id}/video.mp4",  # Path
            'audio_path': f"outputs/{video_id}/video.wav",  # Path for audio
            'video_id': video_id,  # Ensure video_id is included in metadata
            'output_dir': f"outputs/{video_id}",  # Directory where video is stored
            'audio_format': 'wav',  # Audio format used
            'video_format': 'mp4',  # Video format used
            'timestamp': time.time()  # Current timestamp for processing time
        }

        # Add the video_id to the processed set to prevent future duplicates
        processed_video_ids.add(video_id)

        # Save the updated processed videos to the JSON file
        save_processed_videos(processed_video_ids)

        return video_metadata

    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed for video ID: {video_id}, Error: {e}")
        return None
    except KeyError as e:
        logging.error(f"Missing expected metadata for video ID: {video_id}, Error: {e}")
        return None

def fetch_news_videos(query, max_results=10):
    video_data = []
    search_url = 'https://www.googleapis.com/youtube/v3/search'
    
    # Fetch search results with videoLicense filter
    params = {
        'part': 'snippet',
        'maxResults': max_results,
        'q': query,
        'type': 'video',
        'videoLicense': 'creativeCommon',  # Only Creative Commons licensed videos
        'key': API_KEY
    }
    try:
        search_response = requests.get(search_url, params=params)
        search_response.raise_for_status()
        search_results = search_response.json().get('items', [])

        if not search_results:
            logging.warning(f"No search results found for query: {query}")
            return video_data

        # For each video, get detailed metadata
        for video in search_results:
            video_id = video['id']['videoId']
            logging.info(f"Fetching metadata for video ID: {video_id}")
            metadata = fetch_video_metadata(video_id, processed_video_ids)
            
            if metadata:
                video_data.append(metadata)

    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching search results: {e}")

    return video_data

if __name__ == '__main__':
    # Load the list of already processed video IDs from the JSON file
    processed_video_ids = load_processed_videos()
    
    query = 'Bengali news'  # Modify this query as needed
    videos = fetch_news_videos(query, max_results=5)
    
    # Save the metadata to a JSON file
    with open('news_videos_metadata.json', 'w') as f:
        json.dump(videos, f, indent=4)
    
    logging.info(f"Metadata saved to 'news_videos_metadata.json'.")
    print(f"Metadata saved to 'news_videos_metadata.json'.")