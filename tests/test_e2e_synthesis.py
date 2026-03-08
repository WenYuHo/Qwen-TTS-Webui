import pytest
import pytest_asyncio
import numpy as np
from unittest.mock import patch, MagicMock
from httpx import AsyncClient, ASGITransport
import sys
from pathlib import Path
import asyncio

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

# Create a mock engine
mock_engine = MagicMock()

# Setup mocks before any imports that might trigger engine usage
with patch("backend.podcast_engine.PodcastEngine", return_value=mock_engine):
    import backend.server_state
    backend.server_state.engine = mock_engine
    from server import app

@pytest_asyncio.fixture
async def api_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

async def wait_for_task(client, task_id, timeout=5):
    """Wait for a task to reach a terminal state."""
    start_time = asyncio.get_event_loop().time()
    while asyncio.get_event_loop().time() - start_time < timeout:
        resp = await client.get(f"/api/tasks/{task_id}")
        data = resp.json()
        if data["status"] in ["completed", "failed"]:
            return data
        await asyncio.sleep(0.1)
    raise TimeoutError(f"Task {task_id} timed out")

@pytest.mark.integration
@pytest.mark.asyncio
@patch("backend.config.verify_system_paths")
async def test_end_to_end_synthesis_flow_api(mock_verify, api_client):
    """
    Test the full synthesis flow end-to-end via the REST API layer,
    verifying background task processing and result generation.
    """
    # Mock engine.generate_podcast to return a dummy result
    dummy_wav = np.zeros(24000, dtype=np.float32)
    mock_engine.generate_podcast.return_value = {"waveform": dummy_wav, "sample_rate": 24000}
    
    # 1. Start generation via API
    script = [
        {"role": "Ryan", "text": "Hello, this is a test of the REST E2E pipeline."}
    ]
    profiles = {"Ryan": {"type": "preset", "value": "ryan"}}
    
    payload = {
        "profiles": profiles,
        "script": script,
        "eq_preset": "flat"
    }
    
    response = await api_client.post("/api/generate/podcast", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "task_id" in data
    task_id = data["task_id"]
    
    # 2. Wait for background task to complete.
    task_data = await wait_for_task(api_client, task_id)
    
    assert task_data["status"] == "completed"
    assert task_data["has_result"] is True
    
    # 3. Verify binary result via the result endpoint
    result_response = await api_client.get(f"/api/tasks/{task_id}/result")
    assert result_response.status_code == 200
    assert len(result_response.content) > 0
    # Check for RIFF header in the WAV bytes
    assert result_response.content.startswith(b'RIFF')
