import speech_recognition as sr

r = sr.Recognizer()

audio_path = "downloads/fixed.wav"

try:
    with sr.AudioFile(audio_path) as source:
        audio = r.record(source)

    # Recognize with Google Speech Recognition (Bangla)
    result = r.recognize_google(audio, language="bn-BD")

    print("Transcription:")
    print(result)

except sr.UnknownValueError:
    print("❌ Google Speech Recognition could not understand the audio")
except sr.RequestError as e:
    print(f"❌ Could not request results from Google Speech Recognition service; {e}")