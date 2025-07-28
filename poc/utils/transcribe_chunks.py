import os
from banglaspeech2text import Speech2Text

def transcribe_chunks(chunks_dir):
    audio_dir = os.path.join(chunks_dir, "audio")
    text_dir = os.path.join(chunks_dir, "text")
    os.makedirs(text_dir, exist_ok=True)

    asr = Speech2Text(model="large")
    for file in sorted(os.listdir(audio_dir)):
        if file.endswith(".wav"):
            path = os.path.join(audio_dir, file)
            text = asr.recognize(path)
            with open(os.path.join(text_dir, file.replace(".wav", ".txt")), "w") as f:
                f.write(text)