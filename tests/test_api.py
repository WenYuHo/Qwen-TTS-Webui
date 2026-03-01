import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import sys
from pathlib import Path
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

# Create a mock engine
mock_engine = MagicMock()

# Setup mocks before any imports that might trigger engine usage
with patch("backend.podcast_engine.PodcastEngine", return_value=mock_engine):
    import backend.server_state
    backend.server_state.engine = mock_engine
    from server import app

client = TestClient(app)


def test_root_serves_index():
    response = client.get("/")
    assert response.status_code == 200
    assert "Qwen-TTS" in response.text


def test_health_endpoint():
    # Ensure mock returns the expected structure
    mock_engine.get_system_status.return_value = {
        "status": "ready",
        "models": {"models_dir_exists": True, "found_models": []},
        "device": {"type": "cpu", "cuda_available": False}
    }
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert "models" in data
    assert "device" in data


def test_api_speakers():
    response = client.get("/api/voice/speakers")
    assert response.status_code == 200
    data = response.json()
    assert "presets" in data
    assert "ryan" in data["presets"]


def test_api_upload_invalid_type():
    files = {'file': ('test.txt', b'hello world', 'text/plain')}
    response = client.post("/api/voice/upload", files=files)
    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]


def test_api_upload_valid_wav():
    files = {'file': ('test.wav', b'RIFF....WAVEfmt ', 'audio/wav')}
    response = client.post("/api/voice/upload", files=files)
    assert response.status_code == 200
    assert "filename" in response.json()


def test_upload_size_limit():
    """Uploads > 10MB should be rejected"""
    large_data = b'x' * (11 * 1024 * 1024)  # 11MB
    files = {'file': ('big.wav', large_data, 'audio/wav')}
    response = client.post("/api/voice/upload", files=files)
    assert response.status_code == 413
    assert "too large" in response.json()["detail"].lower()


def test_podcast_100_segment_limit():
    """Script > 100 segments should be rejected"""
    script = [{"role": "Ryan", "text": "Hi"}] * 101
    payload = {
        "profiles": [{"role": "Ryan", "type": "preset", "value": "Ryan"}],
        "script": script
    }
    response = client.post("/api/generate/podcast", json=payload)
    assert response.status_code == 400
    assert "too long" in response.json()["detail"].lower()


def test_segment_100_limit():
    """Segment endpoint also enforces the limit"""
    script = [{"role": "Ryan", "text": "Hi"}] * 101
    payload = {
        "profiles": [{"role": "Ryan", "type": "preset", "value": "Ryan"}],
        "script": script
    }
    response = client.post("/api/generate/segment", json=payload)
    assert response.status_code == 400
    assert "too long" in response.json()["detail"].lower()


def test_text_length_validation():
    """Text > 5000 chars should be rejected"""
    long_text = "a" * 5001
    payload = {
        "profiles": [{"role": "Ryan", "type": "preset", "value": "Ryan"}],
        "script": [{"role": "Ryan", "text": long_text}]
    }
    response = client.post("/api/generate/segment", json=payload)
    assert response.status_code == 400
    assert "too long" in response.json()["detail"].lower()


def test_podcast_empty_script():
    """Empty script should be rejected"""
    payload = {
        "profiles": [{"role": "Ryan", "type": "preset", "value": "Ryan"}],
        "script": []
    }
    response = client.post("/api/generate/podcast", json=payload)
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_generate_segment_calls_engine():
    """Verify that generate_segment returns a task ID"""
    payload = {
        "profiles": [{"role": "ryan", "type": "preset", "value": "ryan"}],
        "script": [{"role": "ryan", "text": "Hello"}]
    }
    response = client.post("/api/generate/segment", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert data["status"] == "pending"

def test_task_status_endpoint():
    """Verify task status can be retrieved"""
    # Create a task manually for testing
    from backend.task_manager import task_manager
    tid = task_manager.create_task("test_task")
    
    response = client.get(f"/api/tasks/{tid}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == tid
    assert data["status"] == "pending"

def test_voice_preview_returns_streaming_response():
    """Verify that /api/voice/preview returns audio bytes and doesn't write to disk."""
    # Mock engine.generate_segment to return a dummy waveform
    dummy_wav = np.zeros(16000, dtype=np.float32)
    dummy_sr = 16000
    mock_engine.generate_segment.return_value = (dummy_wav, dummy_sr)

    payload = {"role": "Test", "type": "preset", "value": "aiden"}
    response = client.post("/api/voice/preview", json=payload)

    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert len(response.content) > 0

def test_security_headers():
    """Verify that security headers are present in responses."""
    response = client.get("/api/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "X-XSS-Protection" in response.headers
    assert "Strict-Transport-Security" in response.headers
