import sys
import io
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import numpy as np

# 2. Add src to path
ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = str(ROOT_DIR / "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# 3. Create mock engine and setup app
from unittest.mock import MagicMock, patch
mock_engine = MagicMock()

# Patch PodcastEngine to avoid initialization
with patch("backend.podcast_engine.PodcastEngine", return_value=mock_engine):
    from backend import server_state
    server_state.engine = mock_engine

    # Now we can import the app
    with patch("backend.api.generation.numpy_to_wav_bytes", return_value=io.BytesIO(b"RIFF_WAVE_DATA")):
        from server import app

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_stream_synthesis_integration(client):
    """Verify that the /api/generate/stream endpoint returns a 200 and has correct headers."""
    def mock_generator(*args, **kwargs):
        yield np.zeros(1000, dtype=np.float32), 24000

    mock_engine.stream_synthesize.side_effect = mock_generator

    payload = {
        "text": "Streaming test",
        "profile": {"type": "design", "value": "A calm voice"},
        "language": "en"
    }
    
    response = await client.post("/api/generate/stream", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"

@pytest.mark.asyncio
async def test_video_suggestion_integration(client):
    """Verify that the /api/video/suggest endpoint returns a cinematic prompt."""
    payload = {"text": "A rainy night in a cyberpunk city."}
    response = await client.post("/api/video/suggest", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert "suggestion" in data
    assert "cyberpunk" in data["suggestion"].lower()

@pytest.mark.asyncio
async def test_phoneme_crud(client):
    """Verify the phoneme dictionary API (GET, POST, DELETE)."""
    # 1. Add override
    payload = {"word": "QwenTest", "phonetic": "Kwen"}
    response = await client.post("/api/system/phonemes", json=payload)
    assert response.status_code == 200
    
    # 2. Get list
    response = await client.get("/api/system/phonemes")
    assert response.status_code == 200
    assert "QwenTest" in response.json()["overrides"]
    
    # 3. Delete override
    response = await client.delete("/api/system/phonemes/QwenTest")
    assert response.status_code == 200
    assert "QwenTest" not in response.json()["overrides"]

@pytest.mark.asyncio
async def test_system_settings_persistence(client):
    """Verify that system settings can be retrieved and updated."""
    response = await client.get("/api/system/settings")
    assert response.status_code == 200
    
    payload = {"watermark_audio": False, "watermark_video": False}
    response = await client.post("/api/system/settings", json=payload)
    assert response.status_code == 200
    assert response.json()["settings"]["watermark_audio"] is False

@pytest.mark.asyncio
async def test_clone_preview_with_ref_text(client):
    """Verify the full clone workflow: upload -> preview with ref_text."""
    # 1. Simulate upload
    mock_file = io.BytesIO(b"FAKE_AUDIO_CONTENT")
    # We need to mock the actual file writing in upload_voice
    with patch("backend.api.voices.open", create=True) as mock_open:
        response = await client.post("/api/voice/upload", files={"file": ("test.wav", mock_file, "audio/wav")})
    
    assert response.status_code == 200
    filename = response.json()["filename"]
    assert filename.endswith(".wav")

    # 2. Simulate preview with ref_text (ICL mode)
    dummy_wav = np.zeros(1000, dtype=np.float32)
    mock_engine.generate_segment.return_value = (dummy_wav, 24000)

    payload = {
        "type": "clone",
        "value": filename,
        "ref_text": "This is the reference transcript for ICL."
    }
    
    response = await client.post("/api/voice/preview", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    
    # Verify engine was called with ref_text
    mock_engine.generate_segment.assert_called()
    last_call = mock_engine.generate_segment.call_args
    # signature: generate_segment(text, profile, ...)
    # profile should have ref_text
    profile_arg = last_call.kwargs.get("profile") or last_call[0][1]
    assert profile_arg["ref_text"] == "This is the reference transcript for ICL."

