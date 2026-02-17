import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

# Mock the engine BEFORE importing server to prevent model loading
mock_engine = MagicMock()
with patch("backend.podcast_engine.PodcastEngine", return_value=mock_engine):
    from server import app

client = TestClient(app)


def test_root_serves_index():
    response = client.get("/")
    assert response.status_code == 200
    assert "Qwen-TTS" in response.text


def test_health_endpoint():
    # Ensure mock returns the expected structure
    mock_engine.get_system_status.return_value = {
        "status": "ok",
        "models": {"models_dir_exists": True, "found_models": []},
        "device": {"type": "cpu", "cuda_available": False}
    }
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "models" in data
    assert "device" in data


def test_api_speakers():
    response = client.get("/api/speakers")
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
    """Verify that generate_segment delegates to the engine"""
    dummy_wav = np.zeros(24000, dtype=np.float32)
    mock_engine.generate_segment.return_value = (dummy_wav, 24000)

    payload = {
        "profiles": [{"role": "Ryan", "type": "preset", "value": "Ryan"}],
        "script": [{"role": "Ryan", "text": "Hello"}]
    }
    response = client.post("/api/generate/segment", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
