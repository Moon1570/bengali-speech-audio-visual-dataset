#!/usr/bin/env python3
"""
Test Google Speech Recognition in isolation
"""

import os
import sys
import speech_recognition as sr
from pydub import AudioSegment, effects

def preprocess_audio(path, max_duration=10_000):
    """Same preprocessing as in transcribe_chunks_google.py"""
    audio = AudioSegment.from_wav(path)
    # Normalize audio
    audio = effects.normalize(audio)
    # Trim long segments to max_duration (10 sec by default)
    if len(audio) > max_duration:
        audio = audio[:max_duration]
    return audio

def test_google_transcription(audio_file):
    """Test Google transcription on a single audio file"""
    print(f"Testing: {audio_file}")
    print("="*70)
    
    if not os.path.exists(audio_file):
        print(f"❌ File not found: {audio_file}")
        return False
    
    # Check audio file info
    try:
        audio = AudioSegment.from_wav(audio_file)
        print(f"📊 Audio info:")
        print(f"   Duration: {len(audio)/1000:.2f}s")
        print(f"   Channels: {audio.channels}")
        print(f"   Sample rate: {audio.frame_rate}Hz")
        print(f"   Sample width: {audio.sample_width} bytes")
        print(f"   dBFS: {audio.dBFS:.1f}")
        print()
    except Exception as e:
        print(f"❌ Error loading audio: {e}")
        return False
    
    # Test 1: Direct transcription (no preprocessing)
    print("Test 1: Direct transcription (no preprocessing)")
    print("-"*70)
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
            result = recognizer.recognize_google(audio_data, language="bn-BD")
            print(f"✅ SUCCESS: {result}")
            return True
    except sr.UnknownValueError:
        print("❌ UnknownValueError - Google could not understand the audio")
    except sr.RequestError as e:
        print(f"❌ RequestError - {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    print()
    
    # Test 2: With preprocessing (same as transcribe_chunks_google.py)
    print("Test 2: With preprocessing (normalize + trim to 10s)")
    print("-"*70)
    try:
        processed = preprocess_audio(audio_file)
        tmp_path = "/tmp/test_preprocessed.wav"
        processed.export(tmp_path, format="wav")
        
        print(f"📊 Preprocessed audio:")
        print(f"   Duration: {len(processed)/1000:.2f}s")
        print(f"   dBFS: {processed.dBFS:.1f}")
        print()
        
        with sr.AudioFile(tmp_path) as source:
            audio_data = recognizer.record(source)
            result = recognizer.recognize_google(audio_data, language="bn-BD")
            print(f"✅ SUCCESS: {result}")
            os.remove(tmp_path)
            return True
    except sr.UnknownValueError:
        print("❌ UnknownValueError - Google could not understand the audio")
    except sr.RequestError as e:
        print(f"❌ RequestError - {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        if os.path.exists("/tmp/test_preprocessed.wav"):
            os.remove("/tmp/test_preprocessed.wav")
    print()
    
    # Test 3: With ambient noise adjustment
    print("Test 3: With ambient noise adjustment")
    print("-"*70)
    try:
        recognizer.energy_threshold = 300
        with sr.AudioFile(audio_file) as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio_data = recognizer.record(source)
            result = recognizer.recognize_google(audio_data, language="bn-BD")
            print(f"✅ SUCCESS: {result}")
            return True
    except sr.UnknownValueError:
        print("❌ UnknownValueError - Google could not understand the audio")
    except sr.RequestError as e:
        print(f"❌ RequestError - {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    print()
    
    # Test 4: Try different language codes
    print("Test 4: Try different language codes")
    print("-"*70)
    langs = [
        ('bn-BD', 'Bengali (Bangladesh)'),
        ('bn-IN', 'Bengali (India)'),
        ('hi-IN', 'Hindi'),
        ('en-US', 'English (US)'),
        ('en-IN', 'English (India)')
    ]
    
    with sr.AudioFile(audio_file) as source:
        audio_data = recognizer.record(source)
        for lang_code, lang_name in langs:
            try:
                result = recognizer.recognize_google(audio_data, language=lang_code)
                print(f"✅ {lang_name} ({lang_code}): {result}")
                return True
            except sr.UnknownValueError:
                print(f"❌ {lang_name} ({lang_code}): No match")
            except Exception as e:
                print(f"❌ {lang_name} ({lang_code}): {e}")
    print()
    
    # Test 5: Try first 5 seconds only
    print("Test 5: Try first 5 seconds only")
    print("-"*70)
    try:
        audio = AudioSegment.from_wav(audio_file)
        short_audio = audio[:5000]  # First 5 seconds
        tmp_path = "/tmp/test_short.wav"
        short_audio.export(tmp_path, format="wav")
        
        with sr.AudioFile(tmp_path) as source:
            audio_data = recognizer.record(source)
            result = recognizer.recognize_google(audio_data, language="bn-BD")
            print(f"✅ SUCCESS: {result}")
            os.remove(tmp_path)
            return True
    except sr.UnknownValueError:
        print("❌ UnknownValueError - Google could not understand the audio")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if os.path.exists("/tmp/test_short.wav"):
            os.remove("/tmp/test_short.wav")
    print()
    
    print("="*70)
    print("❌ ALL TESTS FAILED")
    print("Possible issues:")
    print("  1. Audio contains no clear speech")
    print("  2. Audio quality is too poor")
    print("  3. Speech is in a different language")
    print("  4. Background noise/music is too loud")
    print("  5. Google API rate limiting or connectivity issues")
    return False

if __name__ == "__main__":
    # Default test files if no argument provided
    default_test_files = [
        "outputs/A00000000_test/A00000000_test/audio/A00000000_test_chunk_000.wav",
        "outputs/A00000000_test/A00000000_test/audio/A00000000_test_chunk_001.wav",
        "experiments/experiment_data/efhkN7e8238/audio/efhkN7e8238_chunk_000.wav",
    ]
    
    if len(sys.argv) >= 2:
        # Test specific file from command line
        audio_file = sys.argv[1]
        success = test_google_transcription(audio_file)
        sys.exit(0 if success else 1)
    else:
        # Test all default files
        print("No audio file specified. Testing multiple files...\n")
        any_success = False
        
        for audio_file in default_test_files:
            if os.path.exists(audio_file):
                success = test_google_transcription(audio_file)
                any_success = any_success or success
                print("\n" + "="*70 + "\n")
            else:
                print(f"⏭️  Skipping (not found): {audio_file}\n")
        
        if any_success:
            print("✅ At least one file was successfully transcribed!")
            sys.exit(0)
        else:
            print("❌ All test files failed to transcribe")
            sys.exit(1)
