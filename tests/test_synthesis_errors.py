import pytest
import unittest
from unittest.mock import patch, MagicMock
import numpy as np
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from backend.podcast_engine import PodcastEngine

class TestSynthesisErrors(unittest.TestCase):

    def setUp(self):
        self.engine = PodcastEngine()

    @patch("backend.podcast_engine.get_model")
    @patch("backend.podcast_engine.logger")
    def test_generate_segment_handles_model_error(self, mock_logger, mock_get_model):
        """Test that generate_segment logs and raises RuntimeError on model failure."""
        # Setup mock: get_model returns a model whose generate_custom_voice fails
        mock_model = MagicMock()
        mock_model.generate_custom_voice.side_effect = Exception("Inference error")
        mock_get_model.return_value = mock_model
        
        # We expect a RuntimeError to be raised to the API layer, but with logging
        with self.assertRaises(RuntimeError) as cm:
            self.engine.generate_segment("Hello world", profile={"type": "preset", "value": "Ryan"})
        
        self.assertIn("Synthesis failed", str(cm.exception))
        mock_logger.error.assert_called()

    @patch("backend.podcast_engine.get_model")
    def test_generate_segment_invalid_type(self, mock_get_model):
        """Test that unknown speaker types raise RuntimeError (wrapped from ValueError)."""
        with self.assertRaises(RuntimeError) as cm:
            self.engine.generate_segment("Text", profile={"type": "unknown", "value": "val"})
        self.assertIn("Unknown speaker type", str(cm.exception))

if __name__ == "__main__":
    unittest.main()
