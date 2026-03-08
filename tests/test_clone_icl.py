import pytest
import numpy as np
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from backend.podcast_engine import PodcastEngine

@pytest.fixture
def engine():
    with patch("backend.podcast_engine.get_model"):
        e = PodcastEngine()
        return e

def test_clone_without_ref_text_uses_xvector_only(engine):
    """Clone without ref_text should set x_vector_only_mode=True."""
    with patch.object(engine, '_resolve_paths', return_value=[Path('/fake/audio.wav')]):
        mock_model = MagicMock()
        mock_model.create_voice_clone_prompt.return_value = [MagicMock()]
        mock_model.generate_voice_clone.return_value = ([np.zeros(24000)], 24000)
        
        # We need to mock _validate_ref_audio to avoid actual file system checks
        with patch.object(engine, '_validate_ref_audio'):
            engine.generate_segment("Hello", {"type": "clone", "value": "test.wav"}, model=mock_model)
            
            mock_model.create_voice_clone_prompt.assert_called_once()
            call_kwargs = mock_model.create_voice_clone_prompt.call_args.kwargs
            assert call_kwargs.get("x_vector_only_mode") is True

def test_clone_with_ref_text_uses_icl(engine):
    """Clone with ref_text should set x_vector_only_mode=False (ICL mode)."""
    with patch.object(engine, '_resolve_paths', return_value=[Path('/fake/audio.wav')]):
        mock_model = MagicMock()
        mock_model.create_voice_clone_prompt.return_value = [MagicMock()]
        mock_model.generate_voice_clone.return_value = ([np.zeros(24000)], 24000)
        
        # Mock _validate_ref_audio AND sf.read/write for padding logic
        with patch.object(engine, '_validate_ref_audio'), \
             patch("soundfile.read", return_value=(np.zeros(24000), 24000)), \
             patch("soundfile.write"):
            engine.generate_segment("Hello", {"type": "clone", "value": "test.wav", "ref_text": "Test transcript"}, model=mock_model)
            
            call_kwargs = mock_model.create_voice_clone_prompt.call_args.kwargs
            assert call_kwargs.get("x_vector_only_mode") is False
            assert call_kwargs.get("ref_text") == "Test transcript"
