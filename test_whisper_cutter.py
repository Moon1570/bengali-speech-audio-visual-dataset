from transformers import WhisperForConditionalGeneration, WhisperProcessor
import torch
import librosa

# Load the pre-trained Whisper model and processor
processor = WhisperProcessor.from_pretrained("bangla-speech-processing/BanglaASR")
model = WhisperForConditionalGeneration.from_pretrained("bangla-speech-processing/BanglaASR")

# Load the audio file
audio_path = 'downloads/aRHpoSebPPI_audio.wav'  # Ensure the path to the audio file is correct
audio, sr = librosa.load(audio_path, sr=16000)  # Load and resample the audio to 16kHz

# Process the audio with WhisperProcessor to extract input features
inputs = processor(audio, return_tensors="pt", sampling_rate=16000)

# Check the structure of inputs (for debugging)
print(f"Processed inputs: {inputs}")

# Generate transcription with the Whisper model
with torch.no_grad():
    # Use the correct input features for generation
    predicted_ids = model.generate(inputs["input_features"])  # Pass input_features
    transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)

# Print the transcription
print(f"Transcription: {transcription[0]}")