import pytest
import numpy as np
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path
from httpx import AsyncClient, ASGITransport
import pytest_asyncio

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from backend import server_state
from server import app

@pytest_asyncio.fixture
async def client():
    # Patch the engine in server_state
    mock_engine = MagicMock()
    with patch.object(server_state, "engine", mock_engine):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            ac.mock_engine = mock_engine
            yield ac

@pytest.mark.asyncio
async def test_s2s_streaming_endpoint(client):
    """Verify that the /api/generate/s2s endpoint supports streaming."""
    # 1. Mock the stream_voice_changer generator
    def mock_generator(*args, **kwargs):
        # Yield two chunks
        yield np.zeros(1000, dtype=np.float32), 24000
        yield np.zeros(1000, dtype=np.float32), 24000

    client.mock_engine.stream_voice_changer.side_effect = mock_generator

    # 2. Call the endpoint with stream=True
    payload = {
        "source_audio": "test.wav",
        "target_voice": {"type": "preset", "value": "ryan"},
        "stream": True
    }
    
    response = await client.post("/api/generate/s2s", json=payload)
    
    # 3. Assertions
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    
    # Check that we got data
    content = await response.aread()
    assert len(content) > 0
    
    # Verify engine was called
    client.mock_engine.stream_voice_changer.assert_called_once_with(
        source_audio="test.wav",
        target_profile={"type": "preset", "value": "ryan"},
        preserve_prosody=True,
        instruct=None
    )

@pytest.mark.asyncio
async def test_s2s_non_streaming_still_works(client):
    """Verify that the /api/generate/s2s endpoint still works for background tasks."""
    # 1. Setup
    client.mock_engine.generate_voice_changer.return_value = {"waveform": np.zeros(1000), "sample_rate": 24000}
    
    # 2. Call endpoint with stream=False (default)
    payload = {
        "source_audio": "test.wav",
        "target_voice": {"type": "preset", "value": "ryan"},
        "stream": False
    }
    
    response = await client.post("/api/generate/s2s", json=payload)
    
    # 3. Assertions
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert data["status"] == "pending"
