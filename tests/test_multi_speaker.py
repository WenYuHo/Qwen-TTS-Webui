import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from server import app

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

import pytest_asyncio

@pytest.mark.asyncio
async def test_diarization_endpoint(client):
    # Mock diarize_audio
    mock_segments = [
        {"start": 0.0, "end": 1.0, "speaker": "SPEAKER_00", "duration": 1.0},
        {"start": 1.5, "end": 2.5, "speaker": "SPEAKER_01", "duration": 1.0}
    ]
    
    with patch("backend.api.generation.diarize_audio", return_value=mock_segments), \
         patch("backend.podcast_engine.PodcastEngine._resolve_paths", return_value=[Path("dummy.wav")]):
        
        payload = {"source_audio": "dummy.wav"}
        response = await client.post("/api/generate/diarize", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_speakers"] == 2
        assert "SPEAKER_00" in data["speakers"]
        assert "SPEAKER_01" in data["speakers"]
        assert len(data["segments"]) == 2

@pytest.mark.asyncio
async def test_multi_speaker_dubbing_task(client):
    # Mock task creation and run_dub_task
    with patch("backend.api.generation.run_dub_task") as mock_run:
        payload = {
            "source_audio": "dummy.wav",
            "target_lang": "es",
            "speaker_assignment": {
                "SPEAKER_00": {"type": "preset", "value": "ryan"},
                "SPEAKER_01": {"type": "preset", "value": "aiden"}
            }
        }
        response = await client.post("/api/generate/dub", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        
        # Verify run_dub_task was called with speaker_assignment
        mock_run.assert_called_once()
        args = mock_run.call_args[0]
        assert args[4] == payload["speaker_assignment"]
