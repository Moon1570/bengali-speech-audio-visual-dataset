import os
from banglaspeech2text import Speech2Text
from tqdm import tqdm

def transcribe_chunks(chunks_dir, show_progress=False):
    audio_dir = os.path.join(chunks_dir, "audio")
    text_dir = os.path.join(chunks_dir, "text")
    os.makedirs(text_dir, exist_ok=True)

    files = sorted([f for f in os.listdir(audio_dir) if f.endswith(".wav")])
    asr = Speech2Text(model="large")

    iterator = tqdm(files, desc="Transcribing chunks", unit="chunk") if show_progress else files

    for file in iterator:
        path = os.path.join(audio_dir, file)
        text = asr.recognize(path)
        with open(os.path.join(text_dir, file.replace(".wav", ".txt")), "w", encoding="utf-8") as f:
            f.write(text)