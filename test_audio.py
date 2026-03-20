import librosa
import os
import sys

def test_load(path):
    print(f"Testing load for: {path}")
    try:
        # Try to suppress stderr locally if it's a common issue
        y, sr = librosa.load(path)
        print(f"Success! Loaded {len(y)} samples at {sr}Hz")
    except Exception as e:
        print(f"FAILED to load: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_load(sys.argv[1])
    else:
        print("Usage: python test_audio.py <path_to_mp3>")
