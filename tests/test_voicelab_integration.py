import sys
import io
from pathlib import Path
from unittest.mock import MagicMock, patch

# 1. Mock heavy dependencies before any imports
mock_modules = [
    "torch", "torch.nn", "torch.nn.functional", "torch.nn.utils", "torch.nn.utils.rnn",
    "torch.utils", "torch.utils.data", "torch.cuda",
    "torchaudio", "torchaudio.compliance", "torchaudio.compliance.kaldi", "torchaudio.transforms",
    "transformers", "transformers.configuration_utils", "transformers.modeling_utils",
    "transformers.processing_utils", "transformers.utils", "transformers.utils.logging",
    "transformers.utils.hub", "transformers.models", "transformers.generation",
    "scipy", "scipy.signal", "moviepy", "moviepy.editor",
    "moviepy.video", "moviepy.video.io", "moviepy.audio", "moviepy.audio.io",
    "cv2", "librosa", "librosa.filters", "pydub", "whisper", "einops", 
    "accelerate", "onnxruntime", "ltx_pipelines", "deep_translator", 
    "beautifulsoup4", "bs4", "psutil", "soundfile", "huggingface_hub"
]

for mod in mock_modules:
    sys.modules[mod] = MagicMock()

# 2. Add src to path
ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = str(ROOT_DIR / "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# 3. Create mock engine and setup app
mock_engine = MagicMock()
# Explicitly mock the import of PodcastEngine to avoid deep logic
sys.modules["backend.podcast_engine"] = MagicMock()
from backend import server_state
server_state.engine = mock_engine

# Now we can import the app
with patch("backend.api.generation.numpy_to_wav_bytes") as mock_wav_helper:
    mock_wav_helper.return_value = io.BytesIO(b"RIFF_WAVE_DATA")
    from server import app
from fastapi.testclient import TestClient
import numpy as np

client = TestClient(app)

def test_stream_synthesis_integration():
    """Verify that the /api/generate/stream endpoint returns a 200 and has correct headers."""
    def mock_generator(*args, **kwargs):
        yield np.zeros(1000, dtype=np.float32), 24000

    mock_engine.stream_synthesize.side_effect = mock_generator

    payload = {
        "text": "Streaming test",
        "profile": {"type": "design", "value": "A calm voice"},
        "language": "en"
    }
    
    # Use follow_redirects=False to avoid issues with streaming in TestClient
    response = client.post("/api/generate/stream", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    # Note: TestClient response.content for StreamingResponse might be empty 
    # depending on how it's handled, but we've verified headers and status.

def test_video_suggestion_integration():
    """Verify that the /api/video/suggest endpoint returns a cinematic prompt."""
    payload = {"text": "A rainy night in a cyberpunk city."}
    response = client.post("/api/video/suggest", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert "suggestion" in data
    assert "cyberpunk" in data["suggestion"].lower()

def test_phoneme_crud():
    """Verify the phoneme dictionary API (GET, POST, DELETE)."""
    # 1. Add override
    payload = {"word": "QwenTest", "phonetic": "Kwen"}
    response = client.post("/api/system/phonemes", json=payload)
    assert response.status_code == 200
    
    # 2. Get list
    response = client.get("/api/system/phonemes")
    assert response.status_code == 200
    assert "QwenTest" in response.json()["overrides"]
    
    # 3. Delete override
    response = client.delete("/api/system/phonemes/QwenTest")
    assert response.status_code == 200
    assert "QwenTest" not in response.json()["overrides"]

def test_system_settings_persistence():
    """Verify that system settings can be retrieved and updated."""
    response = client.get("/api/system/settings")
    assert response.status_code == 200
    
    payload = {"watermark_audio": False, "watermark_video": False}
    response = client.post("/api/system/settings", json=payload)
    assert response.status_code == 200
    assert response.json()["settings"]["watermark_audio"] is False
