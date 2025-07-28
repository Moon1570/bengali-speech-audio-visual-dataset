# utils/transcribe_chunks_google.py
import os
import speech_recognition as sr
from pydub import AudioSegment, effects

def preprocess_audio(path, max_duration=10_000):
    audio = AudioSegment.from_wav(path)
    # Normalize
    audio = effects.normalize(audio)
    # Trim long segments
    if len(audio) > max_duration:
        audio = audio[:max_duration]
    return audio

def transcribe_chunks_google(chunks_dir):
    audio_dir = os.path.join(chunks_dir, "audio")
    text_dir = os.path.join(chunks_dir, "text_google")
    os.makedirs(text_dir, exist_ok=True)

    recognizer = sr.Recognizer()

    for file in sorted(os.listdir(audio_dir)):
        if not file.endswith(".wav"):
            continue

        audio_path = os.path.join(audio_dir, file)
        processed = preprocess_audio(audio_path)

        # Export to a temporary normalized trimmed WAV
        tmp_path = os.path.join(audio_dir, f"_tmp_{file}")
        processed.export(tmp_path, format="wav")

        with sr.AudioFile(tmp_path) as source:
            audio = recognizer.record(source)
            try:
                result = recognizer.recognize_google(audio, language="bn-BD")
                print(f"{file} ✅: {result}")
                with open(os.path.join(text_dir, file.replace(".wav", ".txt")), "w") as f:
                    f.write(result)
            except sr.UnknownValueError:
                print(f"{file} ❌: Could not understand")
            except sr.RequestError as e:
                print(f"{file} ❌: API error: {e}")

        os.remove(tmp_path)  # Clean up