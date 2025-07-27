from banglaspeech2text import Speech2Text

# Load the pre-trained Bangla Whisper (large) model
asr = Speech2Text(model="large")  # Options: "base", "small", "medium", "large"

# Path to your WAV audio file
audio_path = 'downloads/aRHpoSebPPI_audio.wav'  # Must be a valid .wav file

# Transcribe with timestamps
results = asr.recognize(audio_path, return_segments=True, word_timestamps=True)

# Print segments (start, end, text)
for i, seg in enumerate(results):
    print(f"Segment {i}:")
    print(f"Start: {seg.start:.2f}s")
    print(f"End: {seg.end:.2f}s")
    print(f"Text: {seg.text}")