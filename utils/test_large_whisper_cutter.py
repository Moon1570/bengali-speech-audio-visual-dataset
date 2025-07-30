import whisper
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip

# Load and transcribe Bangla audio
model = whisper.load_model("large")
result = model.transcribe("downloads/flMKyqVWNG1.mp4", language="bn", word_timestamps=True)

# Debug: Show first few transcription segments
print("Total transcription segments:", len(result["segments"]))
for i, seg in enumerate(result["segments"][:3]):
    print(f"\nSegment {i}:")
    print("Text:", seg.get("text"))
    print("Words:", seg.get("words"))

# Combine words into sentence chunks
segments = []
current_text = ""
current_start = None

for seg in result['segments']:
    words = seg.get("words", [])
    for word in words:
        w = word.get("word", "").strip()
        if not w:
            continue
        if current_start is None:
            current_start = word['start']
        current_text += w + " "
        if w.endswith(('।', '.', '?', '!')):  # Bangla or English sentence end
            segments.append((current_start, word['end'], current_text.strip()))
            current_text = ""
            current_start = None

# If no segments were detected, fallback to using full segment cuts
if not segments:
    print("⚠️ No sentence-ending punctuation found. Falling back to segment cuts.")
    for i, seg in enumerate(result['segments']):
        start = seg['start']
        end = seg['end']
        text = seg['text']
        segments.append((start, end, text))

print("Total output chunks to save:", len(segments))

# Cut and save each segment
for i, (start, end, text) in enumerate(segments):
    print(f"Saving chunk {i}: {start:.2f}s to {end:.2f}s")
    ffmpeg_extract_subclip("downloads/flMKyqVWNG1.mp4", start, end, targetname=f"video_chunks/flMKyqVWNG1/chunk_{i}.mp4")
    with open(f"text_chunks/flMKyqVWNG1/chunk_{i}.txt", "w", encoding="utf-8") as f:
        f.write(text)
