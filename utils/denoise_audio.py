import noisereduce as nr
import librosa
import soundfile as sf
import os
import logging

# Set up logging
logging.basicConfig(
    filename='denoising.log',  # Log to this file
    level=logging.INFO,  # Log level (INFO will capture info, warnings, and errors)
    format='%(asctime)s - %(levelname)s - %(message)s'  # Log message format
)

# Directories
AUDIO_DIR = 'audio'  # Folder containing the audio files
DENOISED_DIR = 'denoised_audio'  # Folder to save denoised audio files

# Ensure the denoised audio directory exists
if not os.path.exists(DENOISED_DIR):
    os.makedirs(DENOISED_DIR)

# Function to reduce noise in audio file
def denoise_audio(audio_file):
    audio_path = os.path.join(AUDIO_DIR, audio_file)
    denoised_path = os.path.join(DENOISED_DIR, audio_file)

    # Load the audio file using librosa
    y, sr = librosa.load(audio_path, sr=None)  # `sr=None` to preserve original sample rate

    # Apply noise reduction using noisereduce
    reduced_noise = nr.reduce_noise(y=y, sr=sr)

    # Save the denoised audio using soundfile
    sf.write(denoised_path, reduced_noise, sr)
    logging.info(f"Denoised audio saved to {denoised_path}")

# Process all audio files in the AUDIO_DIR folder
def denoise_all_audio_files():
    audio_files = [f for f in os.listdir(AUDIO_DIR) if f.endswith('.wav')]  # Assuming audio files are in WAV format

    for audio_file in audio_files:
        denoise_audio(audio_file)

if __name__ == '__main__':
    denoise_all_audio_files()