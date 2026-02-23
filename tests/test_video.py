import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import sys
from pathlib import Path
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

# Mock before importing app
mock_engine = MagicMock()
mock_video_engine = MagicMock()

with patch("backend.podcast_engine.PodcastEngine", return_value=mock_engine), \
     patch("backend.video_engine.VideoEngine", return_value=mock_video_engine):
    from server import app

client = TestClient(app)

def test_upload_image_invalid_type():
    files = {'file': ('test.txt', b'hello', 'text/plain')}
    response = client.post("/api/voice/image/upload", files=files)
    assert response.status_code == 400
    assert "Invalid image type" in response.json()["detail"]

def test_upload_image_valid():
    # Mocking VOICE_IMAGES_DIR and upload
    with patch("backend.api.voices.VOICE_IMAGES_DIR", Path("/tmp")):
        files = {'file': ('test.png', b'\x89PNG\r\n\x1a\n', 'image/png')}
        response = client.post("/api/voice/image/upload", files=files)
        assert response.status_code == 200
        assert "url" in response.json()
        assert "/api/voice/image/" in response.json()["url"]

def test_generate_video_api():
    # Mock project file existence
    from backend.api import generation

    payload = {
        "project_name": "TestProject",
        "aspect_ratio": "16:9",
        "include_subtitles": True
    }

    with patch("backend.api.generation.PROJECTS_DIR") as mock_projects_dir:
        mock_file = MagicMock()
        mock_file.exists.return_value = True
        mock_projects_dir.__truediv__.return_value = mock_file

        # Mock ProjectData validation
        from backend.api.schemas import ProjectData
        mock_data = ProjectData(name="TestProject", blocks=[])
        with patch.object(ProjectData, "model_validate_json", return_value=mock_data):
            response = client.post("/api/generate/video", json=payload)
            assert response.status_code == 200
            assert "task_id" in response.json()
            assert response.json()["status"] == "pending"

def test_video_request_schema():
    from backend.api.schemas import VideoRequest
    v = VideoRequest(project_name="Test")
    assert v.aspect_ratio == "16:9"
    assert v.include_subtitles is True
    assert v.font_size == 40
