from faster_whisper import WhisperModel

model = WhisperModel("large-v2", device="cpu", compute_type="int8")

segments, _ = model.transcribe("downloads/aRHpoSebPPI_audio.wav", 
                               language="bn", word_timestamps=True)

for segment in segments:
    print(f"Segment: {segment.start:.2f}s --> {segment.end:.2f}s")
    for word in segment.words:
        print(f"  Word: '{word.word}' [{word.start:.2f}s - {word.end:.2f}s]")