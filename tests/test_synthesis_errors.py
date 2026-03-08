import pytest
from unittest.mock import patch, MagicMock
import numpy as np
import sys
from pathlib import Path

# Add src to path
src_path = str(Path(__file__).resolve().parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from backend.podcast_engine import PodcastEngine

@pytest.fixture
def engine():
    """Provides a fresh PodcastEngine instance for each test."""
    return PodcastEngine()

@patch("backend.engine_modules.synthesizer.get_model")
@patch("backend.engine_modules.synthesizer.logger")
def test_generate_segment_handles_model_error(mock_logger, mock_get_model, engine):
    """Test that generate_segment logs and raises RuntimeError on model failure."""
    # Setup mock: get_model returns a model whose generate_custom_voice fails
    mock_model = MagicMock()
    mock_model.generate_custom_voice.side_effect = Exception("Inference error")
    mock_get_model.return_value = mock_model
    
    # We expect a RuntimeError to be raised to the API layer, but with logging
    with pytest.raises(RuntimeError) as excinfo:
        engine.generate_segment("Hello world", profile={"type": "preset", "value": "Ryan"})
    
    assert "Synthesis failed" in str(excinfo.value)
    mock_logger.error.assert_called()

@patch("backend.engine_modules.synthesizer.get_model")
def test_generate_segment_invalid_type(mock_get_model, engine):
    """Test that unknown speaker types raise RuntimeError (wrapped from ValueError)."""
    with pytest.raises(RuntimeError) as excinfo:
        engine.generate_segment("Text", profile={"type": "unknown", "value": "val"})
    assert "Unknown speaker type" in str(excinfo.value)
