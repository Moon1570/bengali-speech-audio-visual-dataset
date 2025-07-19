import whisper
import os
import speech_recognition as sr
from pydub import AudioSegment

def amplify_audio(input_file, output_file, gain_dB=10):
    """
    Amplify the audio by a specified gain (in dB) and save it to a new file.
    """
    # Ensure the directory exists
    output_dir = os.path.dirname(output_file)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Load audio file
    audio = AudioSegment.from_wav(input_file)
    
    # Apply gain (amplify the audio)
    amplified_audio = audio + gain_dB  # Increase the audio volume by 10 dB
    
    # Export the amplified audio to a new file
    amplified_audio.export(output_file, format="wav")
    
    print(f"Audio amplified and saved as {output_file}")

def split_audio_into_chunks(audio_path, max_words_per_chunk=20):
    """
    Split the audio into smaller chunks based on sentence boundaries and transcribe them.
    """
    # Amplify the audio to ensure better transcription
    amplified_audio_path = "amplified_" + audio_path
    amplify_audio(audio_path, amplified_audio_path)

    # Initialize Whisper model
    model = whisper.load_model("large")  # Or "base" / "small" / "tiny" based on speed/accuracy tradeoff

    # Initialize audio file
    audio = AudioSegment.from_wav(amplified_audio_path)

    # Create the base directory to save chunks
    base_dir = "audio_chunks"
    os.makedirs(base_dir, exist_ok=True)

    # Create a sub-directory with the full file name (without extension)
    file_name_without_ext = os.path.splitext(os.path.basename(audio_path))[0]
    file_dir = os.path.join(base_dir, file_name_without_ext)
    os.makedirs(file_dir, exist_ok=True)

    # Split the audio into small chunks based on silence or fixed duration
    chunk_duration = 10000  # Duration of each chunk in milliseconds (10 seconds for example)
    audio_chunks = []
    for start_ms in range(0, len(audio), chunk_duration):
        end_ms = min(start_ms + chunk_duration, len(audio))
        audio_chunk = audio[start_ms:end_ms]
        chunk_filename = f"chunk_{start_ms // 1000}.wav"
        chunk_filepath = os.path.join(file_dir, chunk_filename)
        audio_chunk.export(chunk_filepath, format="wav")
        audio_chunks.append(chunk_filepath)
    
    return audio_chunks

def transcribe_audio_chunk(audio_filename, model):
    """
    Transcribe an audio chunk using Whisper.
    """
    result = model.transcribe(audio_filename, language="bn")  # Specify Bengali language ("bn")
    return result["text"]

def slice_transcription(text, max_words_per_chunk=20):
    """
    Split the transcribed text into chunks with a maximum of 20 words per chunk.
    """
    sentences = text.split(".")
    chunks = []
    
    for sentence in sentences:
        words = sentence.split()
        if len(words) > max_words_per_chunk:
            # Split long sentences into chunks of max_words_per_chunk
            for i in range(0, len(words), max_words_per_chunk):
                chunks.append(" ".join(words[i:i+max_words_per_chunk]))
        else:
            chunks.append(sentence)
    
    return chunks

# Example of usage:
audio_path = "denoised_audio/aRHpoSebPPI.wav"  # path to your audio file

# Step 1: Split the audio into chunks
audio_chunks = split_audio_into_chunks(audio_path)

# Step 2: Transcribe each chunk and split the transcription into 20-word parts
model = whisper.load_model("large")  # Load Whisper model
for chunk in audio_chunks:
    transcription = transcribe_audio_chunk(chunk, model)
    if transcription:
        chunks = slice_transcription(transcription)
        print(f"Transcription for chunk {chunk}:")
        print(chunks)
        print("=" * 50)