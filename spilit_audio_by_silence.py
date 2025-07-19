from pydub import AudioSegment
from pydub.silence import split_on_silence
import os

def split_audio_on_silence(audio_path, output_dir, min_silence_len=700, silence_thresh=-40, keep_silence=300):
    """
    Splits the audio based on silence and saves the chunks.
    
    Parameters:
    - min_silence_len: minimum length of silence (in ms) that will be used to split.
    - silence_thresh: silence threshold in dBFS (decibels relative to full scale).
    - keep_silence: amount of silence to leave at the beginning and end of each chunk.
    """
    # Load the audio file
    audio = AudioSegment.from_wav(audio_path)
    
    # Split based on silence
    chunks = split_on_silence(
        audio,
        min_silence_len=min_silence_len,
        silence_thresh=silence_thresh,
        keep_silence=keep_silence
    )
    
    # Prepare output directory
    os.makedirs(output_dir, exist_ok=True)
    
    chunk_files = []
    for i, chunk in enumerate(chunks):
        chunk_path = os.path.join(output_dir, f"chunk_{i}.wav")
        chunk.export(chunk_path, format="wav")
        chunk_files.append(chunk_path)
    
    print(f"{len(chunk_files)} chunks saved in {output_dir}")
    return chunk_files

# Example usage
split_audio_on_silence(
    audio_path="denoised_audio/aRHpoSebPPI.wav",
    output_dir="sentence_chunks/aRHpoSebPPI",
    min_silence_len=600,     # can tweak between 500–1000
    silence_thresh=-40,      # adjust based on your audio loudness
    keep_silence=250         # optional: keep some silence around sentences
)