# Google Speech Recognition Fix - Docker FLAC Wrapper

## Problem
Google Speech Recognition was failing inside Docker with `UnknownValueError` for all audio files, while the same files worked perfectly on the host machine.

## Root Cause
The FLAC wrapper script in Docker did not handle **stdin input** correctly. The SpeechRecognition library pipes WAV data to stdin and reads FLAC data from stdout, but our wrapper only handled file-based input.

### How SpeechRecognition Uses FLAC
```bash
# SpeechRecognition library calls:
cat audio.wav | flac - --stdout --totally-silent --best
```

The `-` means "read from stdin", but our wrapper was ignoring it and returning empty data.

## Solution
Updated the FLAC wrapper in `/usr/local/bin/flac` to properly handle stdin/stdout:

### Key Changes
```bash
# OLD (broken):
elif [ -n "$INPUT_FILE" ]; then
    # Output to stdout
    ffmpeg -i "$INPUT_FILE" -f flac - 2>/dev/null
fi

# NEW (working):
if [ "$INPUT_FILE" = "-" ] || [ -z "$INPUT_FILE" ]; then
    # Read from stdin, write to stdout (most common case for SpeechRecognition)
    ffmpeg -f wav -i pipe:0 -f flac pipe:1 2>/dev/null
elif [ -n "$INPUT_FILE" ] && [ -n "$OUTPUT_FILE" ]; then
    # Read from file, write to file
    ...
elif [ -n "$INPUT_FILE" ]; then
    # Read from file, write to stdout
    ffmpeg -i "$INPUT_FILE" -f flac pipe:1 2>/dev/null
fi
```

## Testing
### Before Fix
```bash
$ docker exec bengali-pipeline python3 test_google_transcription.py audio.wav
❌ UnknownValueError - Google could not understand the audio
```

### After Fix
```bash
$ docker exec bengali-pipeline python3 test_google_transcription.py audio.wav
✅ SUCCESS: মেহেবুব আলম আসল নাম আসলে দীপ্ত জিজ্ঞেস করেছে...
```

## Verification
Test with stdin piping:
```bash
# This should output FLAC data (not 0 bytes):
docker exec bengali-pipeline bash -c 'cat audio.wav | /usr/local/bin/flac - --stdout --totally-silent | wc -c'
# Output: 55865 bytes ✅
```

## Files Updated
1. `/usr/local/bin/flac` (in Docker container) - Fixed immediately
2. `Dockerfile` (lines 75-90) - Fixed for future builds
3. `flac_wrapper_fixed.sh` - Standalone script for reference

## Full Pipeline Test Results
After the fix:
- **Success Rate**: 100% (5/5 videos)
- **Transcription Speed**: 0.4-0.6 chunks/second
- **File Sizes**: All transcript files now contain Bengali text (not empty)

### Example Transcriptions
- `chunk_000.txt`: 429 bytes - "মেহেবুব আলম আসল নাম..."
- `chunk_001.txt`: 83 bytes - "বাড়ি কোথায় এটা হলো..."
- `chunk_002.txt`: 137 bytes - (Bengali text)
- `chunk_003.txt`: 610 bytes - (Bengali text)
- `chunk_004.txt`: 756 bytes - (Bengali text)

## Impact
- ✅ Google Speech Recognition now works inside Docker
- ✅ No need to run transcription on host machine
- ✅ Complete pipeline can run end-to-end in Docker
- ✅ Results accessible via volume mounts

## Future Docker Builds
The fix is now permanent in the Dockerfile. Next time you rebuild:
```bash
./build_docker.sh
```

The FLAC wrapper will be created correctly with stdin support.

---

**Fixed**: October 24, 2025  
**Root Cause**: FLAC wrapper didn't handle stdin (`-`) input  
**Solution**: Added stdin/stdout piping support using ffmpeg `pipe:0` and `pipe:1`
