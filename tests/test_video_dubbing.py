import pytest
from unittest.mock import patch, MagicMock
import numpy as np
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from backend.podcast_engine import PodcastEngine

@pytest.fixture
def engine():
    with patch('backend.podcast_engine.Path.mkdir'):
        return PodcastEngine()

def test_transcribe_video_handling(engine):
    """Test that transcribe_audio detects video and calls extraction."""
    with patch.object(engine, '_resolve_paths') as mock_resolve,          patch('backend.podcast_engine.VideoEngine.is_video') as mock_is_video,          patch('backend.podcast_engine.VideoEngine.extract_audio') as mock_extract,          patch('whisper.load_model') as mock_whisper:

        mock_resolve.return_value = [Path("/app/uploads/test.mp4")]
        mock_is_video.return_value = True
        mock_extract.return_value = "/app/projects/videos/ext_audio.wav"

        mock_model = MagicMock()
        mock_model.transcribe.return_value = {"text": "Hello world"}
        mock_whisper.return_value = mock_model

        text = engine.transcribe_audio("test.mp4")

        assert text == "Hello world"
        mock_is_video.assert_called_once()
        mock_extract.assert_called_once_with("/app/uploads/test.mp4")
        mock_model.transcribe.assert_called_once_with("/app/projects/videos/ext_audio.wav")

def test_dub_video_handling(engine):
    """Test that dub_audio handles video files through the pipeline."""
    with patch.object(engine, 'transcribe_audio') as mock_transcribe,          patch.object(engine, 'generate_segment') as mock_gen,          patch('backend.podcast_engine.GoogleTranslator') as mock_translator:

        mock_transcribe.return_value = "Hello"
        mock_translator.return_value.translate.return_value = "Hola"
        mock_gen.return_value = (np.zeros(1000), 24000)

        result = engine.dub_audio("video.mp4", "es")

        assert result["text"] == "Hola"
        mock_transcribe.assert_called_once_with("video.mp4")
        mock_gen.assert_called_once()
        # Verify it passed the original video path for cloning
        args, kwargs = mock_gen.call_args
        assert kwargs["profile"]["type"] == "clone"
        assert kwargs["profile"]["value"] == "video.mp4"

if __name__ == "__main__":
    pytest.main([__file__])
