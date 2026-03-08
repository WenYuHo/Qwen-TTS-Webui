import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import numpy as np
import json
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from server import app
from backend.task_manager import task_manager, TaskStatus

@pytest_asyncio.fixture
async def client():
    # Patch the engine in server_state where all routers get it from
    with patch('backend.server_state.engine') as mock:
        mock.upload_dir = Path("uploads")
        if not mock.upload_dir.exists():
            mock.upload_dir.mkdir(parents=True)

        dummy_wav = np.zeros(1000, dtype=np.float32)
        mock.generate_segment.return_value = (dummy_wav, 24000)
        mock.generate_podcast.return_value = {"waveform": dummy_wav, "sample_rate": 24000}
        mock.dub_audio.return_value = {"waveform": dummy_wav, "sample_rate": 24000, "text": "Spanish text"}
        mock.transcribe_audio.return_value = "Transcribed text"
        mock.get_system_status.return_value = {"status": "ok"}

        app.state.mock_engine = mock
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            yield ac

@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

@pytest.mark.asyncio
async def test_upload_voice(client):
    # client fixture setup app.state.mock_engine
    mock_engine = app.state.mock_engine
    
    # Create a dummy wav file
    dummy_wav_file = Path("test_upload.wav")
    dummy_wav_file.write_bytes(b"dummy audio content")

    try:
        with open(dummy_wav_file, "rb") as f:
            response = await client.post("/api/voice/upload", files={"file": ("test.wav", f, "audio/wav")})

        assert response.status_code == 200
        assert "filename" in response.json()

        filename = response.json()["filename"]
        uploaded_file = mock_engine.upload_dir / filename
        assert uploaded_file.exists()
        # Cleanup uploaded file
        if uploaded_file.exists():
            uploaded_file.unlink()
    finally:
        if dummy_wav_file.exists():
            dummy_wav_file.unlink()

@pytest.mark.asyncio
async def test_generate_segment(client):
    data = {
        "profiles": {"Alice": {"type": "preset", "value": "Ryan"}},
        "script": [{"role": "Alice", "text": "Hello"}]
    }
    response = await client.post("/api/generate/segment", json=data)
    assert response.status_code == 200
    assert "task_id" in response.json()

@pytest.mark.asyncio
async def test_s2s_endpoint(client):
    data = {
        "source_audio": "test.wav",
        "target_voice": {"role": "Bob", "type": "preset", "value": "Eric"}
    }
    response = await client.post("/api/generate/s2s", json=data)
    assert response.status_code == 200
    assert "task_id" in response.json()

@pytest.mark.asyncio
async def test_dub_endpoint(client):
    data = {
        "source_audio": "test.wav",
        "target_lang": "Spanish"
    }
    response = await client.post("/api/generate/dub", json=data)
    assert response.status_code == 200
    assert "task_id" in response.json()

@pytest.mark.asyncio
async def test_project_endpoints(client):
    project_name = "test_project"
    data = {
        "name": project_name,
        "blocks": [{"id": "1", "role": "Alice", "text": "Hi", "status": "ready"}],
        "script_draft": "Alice: Hi"
    }

    # Save
    response = await client.post(f"/api/projects/{project_name}", json=data)
    assert response.status_code == 200

    # List
    response = await client.get("/api/projects")
    assert project_name in response.json()["projects"]

    # Load
    response = await client.get(f"/api/projects/{project_name}")
    assert response.status_code == 200
    assert response.json()["name"] == project_name

    # Cleanup
    project_file = Path("projects") / f"{project_name}.json"
    if project_file.exists():
        project_file.unlink()
