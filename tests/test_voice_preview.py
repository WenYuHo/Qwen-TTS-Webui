import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from backend.api.voices import PREVIEW_TEXTS

def test_preview_pool_has_diverse_sentences():
    assert len(PREVIEW_TEXTS) >= 8, "Pool should have at least 8 sentences"
    # Check variety: questions, exclamations, quotes
    has_question = any("?" in t for t in PREVIEW_TEXTS)
    has_exclamation = any("!" in t for t in PREVIEW_TEXTS)
    has_quote = any("'" in t or '"' in t for t in PREVIEW_TEXTS)
    assert has_question and has_exclamation and has_quote

@pytest.mark.asyncio
async def test_preview_uses_custom_text():
    """POST /api/voice/preview with preview_text should use that text."""
    from httpx import AsyncClient, ASGITransport
    # backend.server import needs to happen AFTER sys.path modification
    from server import app
    from backend.api.schemas import SpeakerProfile
    
    # We patch server_state.engine.generate_segment globally within the module it's used
    # But since backend.api.voices imports server_state, we patch server_state.engine
    
    with patch("backend.server_state.engine") as mock_engine:
        # Mock return value: (waveform, sample_rate)
        mock_engine.generate_segment.return_value = (np.zeros(24000), 24000)
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/voice/preview", json={
                "type": "preset", 
                "value": "ryan", 
                "preview_text": "Custom test text"
            })
            
        assert resp.status_code == 200
        
        # Verify generate_segment was called with "Custom test text"
        mock_engine.generate_segment.assert_called_once()
        # call_args[0] are positional args, [1] are keyword args
        # signature: generate_segment(text, profile, ...)
        call_args = mock_engine.generate_segment.call_args
        # The first positional argument should be the text
        assert call_args[0][0] == "Custom test text"
