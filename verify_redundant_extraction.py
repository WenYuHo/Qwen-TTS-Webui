import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from backend.podcast_engine import PodcastEngine
from backend.video_engine import VideoEngine

def test_dubbing_redundancy():
    engine = PodcastEngine()

    # Mocking necessary components to avoid actual ML/IO
    with patch('backend.podcast_engine.VideoEngine.is_video', return_value=True),          patch('backend.podcast_engine.VideoEngine.extract_audio') as mock_extract,          patch('backend.podcast_engine.Path.exists', return_value=True),          patch.object(engine, '_whisper_model') as mock_whisper,          patch('backend.podcast_engine.GoogleTranslator') as mock_translator,          patch('backend.podcast_engine.get_model') as mock_get_model,          patch('backend.podcast_engine.sf.read') as mock_sf_read:

        # Mocking whisper transcription
        mock_whisper.transcribe.return_value = {"text": "Hello world"}

        # Mocking translator
        mock_translator.return_value.translate.return_value = "Hola mundo"

        # Mocking Qwen Model
        mock_model = MagicMock()
        mock_model.generate_voice_clone.return_value = ([np.zeros(24000)], 24000)
        mock_model.create_voice_clone_prompt.return_value = [MagicMock(ref_spk_embedding=np.zeros(128))]
        mock_get_model.return_value = mock_model

        # Mocking audio extraction return value to avoid file not found
        mock_extract.return_value = "dummy_audio.wav"

        print("Starting Dubbing Task...")
        start_time = time.time()
        engine.dub_audio("test_video.mp4", "es")
        end_time = time.time()

        print(f"Dubbing took {end_time - start_time:.4f} seconds (Mocked)")
        print(f"VideoEngine.extract_audio called {mock_extract.call_count} times")

        if mock_extract.call_count > 1:
            print("❌ REDUNDANCY DETECTED")
        else:
            print("✅ NO REDUNDANCY")

if __name__ == "__main__":
    test_dubbing_redundancy()
