import pytest
import numpy as np
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path
import os

@pytest.mark.asyncio
async def test_root_serves_index(app_client):
    async with app_client as client:
        response = await client.get("/")
        assert response.status_code == 200
        assert "Qwen-TTS" in response.text


@pytest.mark.asyncio
async def test_health_endpoint(app_client, mock_engine):
    async with app_client as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert "device" in data
        assert "models_loaded" in data


@pytest.mark.asyncio
async def test_api_speakers(app_client):
    async with app_client as client:
        response = await client.get("/api/voice/speakers")
        assert response.status_code == 200
        data = response.json()
        assert "presets" in data
        speaker_ids = [s["id"] for s in data["presets"]]
        assert "ryan" in speaker_ids


@pytest.mark.asyncio
async def test_api_upload_invalid_type(app_client):
    async with app_client as client:
        files = {'file': ('test.txt', b'hello world', 'text/plain')}
        response = await client.post("/api/voice/upload", files=files)
        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]


@pytest.mark.asyncio
async def test_api_upload_valid_wav(app_client, tmp_path):
    async with app_client as client:
        import soundfile as sf
        wav_path = tmp_path / "test.wav"
        sf.write(str(wav_path), np.random.randn(1000), 24000)
        
        with open(wav_path, "rb") as f:
            files = {'file': ('test.wav', f, 'audio/wav')}
            response = await client.post("/api/voice/upload", files=files)
            assert response.status_code == 200
            assert "filename" in response.json()


@pytest.mark.asyncio
async def test_upload_size_limit(app_client):
    async with app_client as client:
        # 11MB file (limit is 10MB)
        big_data = b"0" * (11 * 1024 * 1024)
        files = {'file': ('big.wav', big_data, 'audio/wav')}
        response = await client.post("/api/voice/upload", files=files)
        assert response.status_code == 413


@pytest.mark.asyncio
async def test_podcast_100_segment_limit(app_client):
    async with app_client as client:
        # Limit is exactly 100, so 101 should fail
        script = [{"role": "Alice", "text": "Hi"}] * 101
        response = await client.post("/api/generate/podcast", json={
            "script": script,
            "profiles": {"Alice": {"type": "preset", "value": "Aiden"}}
        })
        assert response.status_code == 400
        assert "Script too long" in response.json()["detail"]


@pytest.mark.asyncio
async def test_segment_100_limit(app_client):
    async with app_client as client:
        script = [{"role": "Alice", "text": "Hi"}] * 101
        response = await client.post("/api/generate/segment", json={
            "script": script,
            "profiles": {"Alice": {"type": "preset", "value": "Aiden"}}
        })
        assert response.status_code == 400


@pytest.mark.asyncio
async def test_text_length_validation(app_client):
    async with app_client as client:
        # Limit is 5000, so 5001 should fail
        long_text = "a" * 5001
        script = [{"role": "Alice", "text": long_text}]
        response = await client.post("/api/generate/segment", json={
            "script": script,
            "profiles": {"Alice": {"type": "preset", "value": "Aiden"}}
        })
        assert response.status_code == 400
        assert "Text too long" in response.json()["detail"]


@pytest.mark.asyncio
async def test_podcast_empty_script(app_client):
    async with app_client as client:
        response = await client.post("/api/generate/podcast", json={
            "script": [],
            "profiles": {}
        })
        assert response.status_code == 400


@pytest.mark.asyncio
async def test_generate_segment_calls_engine(app_client, mock_engine):
    async with app_client as client:
        response = await client.post("/api/generate/segment", json={
            "profiles": {"alice": {"type": "preset", "value": "Aiden"}},
            "script": [{"role": "alice", "text": "Hello"}]
        })
        assert response.status_code == 200
        assert "task_id" in response.json()


@pytest.mark.asyncio
async def test_task_status_endpoint(app_client):
    async with app_client as client:
        # Create a task first
        res = await client.post("/api/generate/segment", json={
            "profiles": {"alice": {"type": "preset", "value": "Aiden"}},
            "script": [{"role": "alice", "text": "Hello"}]
        })
        task_id = res.json()["task_id"]
        
        response = await client.get(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        assert "status" in response.json()


@pytest.mark.asyncio
async def test_voice_preview_returns_streaming_response(app_client, mock_engine):
    async with app_client as client:
        # Setup mock_engine to return data for generate_segment
        mock_engine.generate_segment.return_value = (np.zeros(1000), 24000)
        
        response = await client.post("/api/voice/preview", json={
            "type": "preset",
            "value": "Aiden"
        })
        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/wav"


@pytest.mark.asyncio
async def test_voice_preview_with_custom_text(app_client, mock_engine):
    async with app_client as client:
        mock_engine.generate_segment.return_value = (np.zeros(1000), 24000)
        
        response = await client.post("/api/voice/preview", json={
            "type": "preset",
            "value": "Aiden",
            "preview_text": "Custom preview text"
        })
        assert response.status_code == 200
        # Verify engine was called with the custom text
        mock_engine.generate_segment.assert_called()
        args, kwargs = mock_engine.generate_segment.call_args
        assert kwargs["text"] == "Custom preview text"


@pytest.mark.asyncio
async def test_generate_podcast_with_temperature_preset(app_client, mock_engine):
    async with app_client as client:
        mock_engine.generate_podcast.return_value = {"waveform": np.zeros(1000), "sample_rate": 24000}
        
        response = await client.post("/api/generate/podcast", json={
            "script": [{"role": "Alice", "text": "Hi"}],
            "profiles": {"Alice": {"type": "preset", "value": "Aiden"}},
            "temperature": 0.5
        })
        assert response.status_code == 200
        mock_engine.generate_podcast.assert_called()
        args, kwargs = mock_engine.generate_podcast.call_args
        assert kwargs["temperature"] == 0.5


@pytest.mark.asyncio
async def test_security_headers(app_client):
    async with app_client as client:
        response = await client.get("/")
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"
