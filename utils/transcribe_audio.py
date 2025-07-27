import whisper
import os
import logging

# Set up logging
logging.basicConfig(
    filename='transcription.log',  # Log to this file
    level=logging.INFO,  # Log level (INFO will capture info, warnings, and errors)
    format='%(asctime)s - %(levelname)s - %(message)s'  # Log message format
)

# Load Whisper model
model = whisper.load_model("base")  # You can use "small", "medium", or "large" based on your resources

# Directory paths
AUDIO_DIR = 'audio'  # Folder containing audio files
TRANSCRIPT_DIR = 'transcripts'  # Folder to save transcriptions

# Ensure TRANSCRIPT_DIR exists
if not os.path.exists(TRANSCRIPT_DIR):
    os.makedirs(TRANSCRIPT_DIR)

# Function to transcribe audio to text
def transcribe_audio(audio_file):
    audio_path = os.path.join(AUDIO_DIR, audio_file)
    
    # Transcribe audio using Whisper
    result = model.transcribe(audio_path)
    
    # Save transcription to file
    transcript_path = os.path.join(TRANSCRIPT_DIR, f"{os.path.splitext(audio_file)[0]}.txt")
    with open(transcript_path, 'w') as f:
        f.write(result['text'])

    logging.info(f"Transcription saved for {audio_file} at {transcript_path}")

# Process all audio files in the AUDIO_DIR folder
def transcribe_audio_from_files():
    audio_files = [f for f in os.listdir(AUDIO_DIR) if f.endswith('.wav')]  # Assuming audio files are in WAV format

    for audio_file in audio_files:
        transcribe_audio(audio_file)

if __name__ == '__main__':
    transcribe_audio_from_files()