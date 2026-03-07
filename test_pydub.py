import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from backend.config import BIN_DIR
from pydub import AudioSegment

print(f"BIN_DIR: {BIN_DIR}")
print(f"PATH updated: {'bin' in os.environ.get('PATH')}")

try:
    # This might trigger the warning if ffmpeg/sox not found
    seg = AudioSegment.silent(duration=1000)
    print("Created AudioSegment")
    # Try exporting (requires ffmpeg)
    seg.export("test_pydub.wav", format="wav")
    print("Exported test_pydub.wav")
    os.remove("test_pydub.wav")
except Exception as e:
    print(f"Pydub error: {e}")
