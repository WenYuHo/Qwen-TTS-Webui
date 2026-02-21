import sys
import os
from pathlib import Path
import soundfile as sf
import traceback
import importlib

# Setup path
sys.path.insert(0, str(Path("src").resolve()))
sys.path.insert(0, str(Path("src/backend").resolve()))

# Mock sox if needed
try:
    import sox
except ImportError:
    from backend.sox_shim import mock_sox
    mock_sox()

from backend.podcast_engine import PodcastEngine
import backend.podcast_engine

# Force reload to ensure valid speakers
importlib.reload(backend.podcast_engine)
PRESET_SPEAKERS = backend.podcast_engine.PRESET_SPEAKERS

def generate_all_previews():
    engine = PodcastEngine()
    preview_dir = Path("src/static/previews")
    preview_dir.mkdir(parents=True, exist_ok=True)
    
    # Clean old ones to be sure? No, keep valid ones.
    # Actually, Ryan.wav might be bad if case sensitivity matters
    
    print(f"Generating previews for: {PRESET_SPEAKERS}")
    
    for speaker in PRESET_SPEAKERS:
        safe_name = "".join([c for c in speaker if c.isalnum() or c in (' ', '.', '_', '-')]).strip()
        filename = preview_dir / f"{safe_name}.wav"
        
        if filename.exists():
            print(f"Skipping {speaker} (already exists at {filename})")
            continue
            
        print(f"Generating preview for {speaker}...")
        try:
            # Configure engine for this speaker
            engine.set_speaker_profile(speaker, {"type": "preset", "value": speaker})
            
            # Generate
            text = "Hello! This is a preview of my voice."
            wav, sr = engine.generate_segment(speaker, text)
            
            # Save
            sf.write(str(filename), wav, sr, format='WAV')
            print(f"Saved {filename}")
            
        except Exception as e:
            print(f"Failed to generate {speaker}: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    generate_all_previews()
