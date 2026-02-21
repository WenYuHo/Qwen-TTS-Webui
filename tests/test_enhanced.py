import pytest
from fastapi.testclient import TestClient
from src.server import app
from src.backend.task_manager import task_manager, TaskStatus
import json
import os
import numpy as np
from pathlib import Path
from unittest.mock import MagicMock, patch

client = TestClient(app)

@pytest.fixture
def mock_engine():
    with patch('src.server.engine') as mock:
        mock.upload_dir = Path("uploads")
        if not mock.upload_dir.exists():
            mock.upload_dir.mkdir(parents=True)

        dummy_wav = np.zeros(1000, dtype=np.float32)
        mock.generate_segment.return_value = (dummy_wav, 24000)
        mock.generate_podcast.return_value = {"waveform": dummy_wav, "sample_rate": 24000}
        mock.dub_audio.return_value = {"waveform": dummy_wav, "sample_rate": 24000, "text": "Spanish text"}
        mock.transcribe_audio.return_value = "Transcribed text"

        yield mock

def test_health_check(mock_engine):
    mock_engine.get_system_status.return_value = {"status": "ok"}
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_upload_voice(mock_engine):
    # Create a dummy wav file
    dummy_wav_file = Path("test_upload.wav")
    dummy_wav_file.write_bytes(b"dummy audio content")

    try:
        with open(dummy_wav_file, "rb") as f:
            response = client.post("/api/voice/upload", files={"file": ("test.wav", f, "audio/wav")})

        assert response.status_code == 200
        assert "filename" in response.json()

        filename = response.json()["filename"]
        uploaded_file = mock_engine.upload_dir / filename
        assert uploaded_file.exists()
    finally:
        if dummy_wav_file.exists():
            dummy_wav_file.unlink()

def test_generate_segment(mock_engine):
    data = {
        "profiles": [{"role": "Alice", "type": "preset", "value": "Ryan"}],
        "script": [{"role": "Alice", "text": "Hello"}]
    }
    response = client.post("/api/generate/segment", json=data)
    assert response.status_code == 200
    assert "task_id" in response.json()
    task_id = response.json()["task_id"]

    # In tests, the background task might not have run yet or might fail if not mocked properly
    # But the endpoint should return a task_id
    assert task_id is not None

def test_s2s_endpoint(mock_engine):
    data = {
        "source_audio": "test.wav",
        "target_voice": {"role": "Bob", "type": "preset", "value": "Eric"}
    }
    response = client.post("/api/generate/s2s", json=data)
    assert response.status_code == 200
    assert "task_id" in response.json()

def test_dub_endpoint(mock_engine):
    data = {
        "source_audio": "test.wav",
        "target_lang": "Spanish"
    }
    response = client.post("/api/generate/dub", json=data)
    assert response.status_code == 200
    assert "task_id" in response.json()

def test_project_endpoints():
    project_name = "test_project"
    data = {
        "name": project_name,
        "blocks": [{"id": "1", "role": "Alice", "text": "Hi", "status": "ready"}],
        "script_draft": "Alice: Hi"
    }

    # Save
    response = client.post(f"/api/projects/{project_name}", json=data)
    assert response.status_code == 200

    # List
    response = client.get("/api/projects")
    assert project_name in response.json()["projects"]

    # Load
    response = client.get(f"/api/projects/{project_name}")
    assert response.status_code == 200
    assert response.json()["name"] == project_name

    # Cleanup
    project_file = Path("projects") / f"{project_name}.json"
    if project_file.exists():
        project_file.unlink()
