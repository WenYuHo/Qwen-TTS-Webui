import pytest
import unittest
from unittest.mock import patch, MagicMock
import numpy as np
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from backend.podcast_engine import PodcastEngine

class TestE2ESynthesis(unittest.TestCase):

    def setUp(self):
        self.engine = PodcastEngine()

    @patch("backend.podcast_engine.get_model")
    @patch("backend.config.verify_system_paths")
    def test_end_to_end_synthesis_flow(self, mock_verify, mock_get_model):
        """Test the full synthesis flow with mocked model inference."""
        # 1. Setup mock model
        mock_model = MagicMock()
        dummy_wav = np.zeros(24000, dtype=np.float32)
        mock_model.generate_custom_voice.return_value = ([dummy_wav], 24000)
        mock_get_model.return_value = mock_model
        
        # 2. Setup script
        script = [
            {"role": "Ryan", "text": "Hello, this is a test of the stability track."}
        ]
        profiles = {"Ryan": {"type": "preset", "value": "ryan"}}
        
        # 3. Generate
        result = self.engine.generate_podcast(script, profiles=profiles)
        
        # 4. Verify
        self.assertIsNotNone(result)
        self.assertIn("waveform", result)
        self.assertIn("sample_rate", result)
        self.assertEqual(result["sample_rate"], 24000)
        self.assertIsInstance(result["waveform"], np.ndarray)

if __name__ == "__main__":
    unittest.main()
