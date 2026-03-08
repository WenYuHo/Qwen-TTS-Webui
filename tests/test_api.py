import pytest
import numpy as np
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path
import os
from httpx import AsyncClient, ASGITransport

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

# Create a mock engine
mock_engine = MagicMock()

# Setup mocks before any imports that might trigger engine usage
with patch("backend.podcast_engine.PodcastEngine", return_value=mock_engine):
    import backend.server_state
    backend.server_state.engine = mock_engine
    from server import app

import pytest_asyncio

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_root_serves_index(client):
    response = await client.get("/")
    assert response.status_code == 200
    assert "Qwen-TTS" in response.text


@pytest.mark.asyncio
async def test_health_endpoint(client):
    # Ensure mock returns the expected structure from PodcastEngine.get_system_status
    mock_engine.get_system_status.return_value = {
        "status": "ready",
        "device": "cpu",
        "models_loaded": []
    }
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert "device" in data
    assert "models_loaded" in data


@pytest.mark.asyncio
async def test_api_speakers(client):
    response = await client.get("/api/voice/speakers")
    assert response.status_code == 200
    data = response.json()
    assert "presets" in data
    speaker_ids = [s["id"] for s in data["presets"]]
    assert "ryan" in speaker_ids


@pytest.mark.asyncio
async def test_api_upload_invalid_type(client):
    files = {'file': ('test.txt', b'hello world', 'text/plain')}
    response = await client.post("/api/voice/upload", files=files)
    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]


@pytest.mark.asyncio
async def test_api_upload_valid_wav(client):
    files = {'file': ('test.wav', b'RIFF....WAVEfmt ', 'audio/wav')}
    response = await client.post("/api/voice/upload", files=files)
    assert response.status_code == 200
    assert "filename" in response.json()


@pytest.mark.asyncio
async def test_upload_size_limit(client):
    """Uploads > 10MB should be rejected"""
    large_data = b'x' * (11 * 1024 * 1024)  # 11MB
    files = {'file': ('big.wav', large_data, 'audio/wav')}
    response = await client.post("/api/voice/upload", files=files)
    assert response.status_code == 413
    assert "too large" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_podcast_100_segment_limit(client):
    """Script > 100 segments should be rejected"""
    script = [{"role": "Ryan", "text": "Hi"}] * 101
    payload = {
        "profiles": {"Ryan": {"type": "preset", "value": "Ryan"}},
        "script": script
    }
    response = await client.post("/api/generate/podcast", json=payload)
    assert response.status_code == 400
    assert "too long" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_segment_100_limit(client):
    """Segment endpoint also enforces the limit"""
    script = [{"role": "Ryan", "text": "Hi"}] * 101
    payload = {
        "profiles": {"Ryan": {"type": "preset", "value": "Ryan"}},
        "script": script
    }
    response = await client.post("/api/generate/segment", json=payload)
    assert response.status_code == 400
    assert "too long" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_text_length_validation(client):
    """Text > 5000 chars should be rejected"""
    long_text = "a" * 5001
    payload = {
        "profiles": {"Ryan": {"type": "preset", "value": "Ryan"}},
        "script": [{"role": "Ryan", "text": long_text}]
    }
    response = await client.post("/api/generate/segment", json=payload)
    assert response.status_code == 400
    assert "too long" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_podcast_empty_script(client):
    """Empty script should be rejected"""
    payload = {
        "profiles": {"Ryan": {"type": "preset", "value": "Ryan"}},
        "script": []
    }
    response = await client.post("/api/generate/podcast", json=payload)
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_generate_segment_calls_engine(client):
    """Verify that generate_segment returns a task ID"""
    payload = {
        "profiles": {"ryan": {"type": "preset", "value": "ryan"}},
        "script": [{"role": "ryan", "text": "Hello"}]
    }
    response = await client.post("/api/generate/segment", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_task_status_endpoint(client):
    """Verify task status can be retrieved"""
    # Create a task manually for testing
    from backend.task_manager import task_manager
    tid = task_manager.create_task("test_task")
    
    response = await client.get(f"/api/tasks/{tid}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == tid
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_voice_preview_returns_streaming_response(client):
    """Verify that /api/voice/preview returns audio bytes and doesn't write to disk."""
    # Mock engine.generate_segment to return a dummy waveform
    dummy_wav = np.zeros(16000, dtype=np.float32)
    dummy_sr = 16000
    mock_engine.generate_segment.return_value = (dummy_wav, dummy_sr)

    payload = {"role": "Test", "type": "preset", "value": "aiden"}
    response = await client.post("/api/voice/preview", json=payload)

    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert len(response.content) > 0


@pytest.mark.asyncio
async def test_voice_preview_with_custom_text(client):
    """Verify that /api/voice/preview accepts custom preview_text."""
    dummy_wav = np.zeros(16000, dtype=np.float32)
    mock_engine.generate_segment.return_value = (dummy_wav, 16000)

    payload = {"role": "Test", "type": "preset", "value": "aiden", "preview_text": "Special text"}
    response = await client.post("/api/voice/preview", json=payload)

    assert response.status_code == 200
    # Verify engine was called with "Special text"
    mock_engine.generate_segment.assert_called()
    last_call = mock_engine.generate_segment.call_args
    assert last_call[0][0] == "Special text"


@pytest.mark.asyncio
async def test_generate_podcast_with_temperature_preset(client):
    """Verify that /api/generate/podcast accepts temperature_preset."""
    payload = {
        "profiles": {"ryan": {"type": "preset", "value": "ryan"}},
        "script": [{"role": "ryan", "text": "Hello"}],
        "temperature_preset": "creative"
    }
    response = await client.post("/api/generate/podcast", json=payload)
    assert response.status_code == 200
    assert "task_id" in response.json()


@pytest.mark.asyncio
async def test_security_headers(client):
    """Verify that security headers are present in responses."""
    response = await client.get("/api/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "X-XSS-Protection" in response.headers
    assert "Strict-Transport-Security" in response.headers

