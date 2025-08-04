import os
import speech_recognition as sr
from pydub import AudioSegment, effects
from tqdm import tqdm

def preprocess_audio(path, max_duration=10_000):
    audio = AudioSegment.from_wav(path)
    # Normalize audio
    audio = effects.normalize(audio)
    # Trim long segments to max_duration (10 sec by default)
    if len(audio) > max_duration:
        audio = audio[:max_duration]
    return audio

def transcribe_chunks_google(chunks_dir, show_progress=False):
    audio_dir = os.path.join(chunks_dir, "audio")
    text_dir = os.path.join(chunks_dir, "text_google")
    os.makedirs(text_dir, exist_ok=True)

    files = sorted([f for f in os.listdir(audio_dir) if f.endswith(".wav")])
    recognizer = sr.Recognizer()

    iterator = tqdm(files, desc="Transcribing (Google)", unit="chunk") if show_progress else files

    for file in iterator:
        audio_path = os.path.join(audio_dir, file)
        processed = preprocess_audio(audio_path)

        # Export to a temporary normalized trimmed WAV
        tmp_path = os.path.join(audio_dir, f"_tmp_{file}")
        processed.export(tmp_path, format="wav")

        text_file = os.path.join(text_dir, file.replace(".wav", ".txt"))

        # Skip if already transcribed
        if os.path.exists(text_file):
            os.remove(tmp_path)  # Clean up temp file
            continue

        try:
            with sr.AudioFile(tmp_path) as source:
                audio = recognizer.record(source)
                result = recognizer.recognize_google(audio, language="bn-BD")
                with open(text_file, "w", encoding="utf-8") as f:
                    f.write(result)
        except sr.UnknownValueError:
            with open(text_file, "w", encoding="utf-8") as f:
                f.write("[Unrecognized Speech]")
        except sr.RequestError as e:
            with open(text_file, "w", encoding="utf-8") as f:
                f.write(f"[API Error: {e}]")

        # Clean up temp file
        os.remove(tmp_path)