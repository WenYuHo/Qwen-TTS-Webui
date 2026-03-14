import sys
import os
import time
import subprocess
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add src to PYTHONPATH
src_path = str(Path(__file__).resolve().parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Mock sox before anything else
try:
    import backend.sox_shim as sox_shim
    sox_shim.mock_sox()
except Exception:
    pass


@pytest.fixture
def mock_model():
    """Mock Qwen3-TTS model that returns deterministic audio."""
    model = MagicMock()
    # generate_custom_voice returns (waveform_list, sample_rate)
    model.generate_custom_voice.return_value = (
        [np.random.randn(24000).astype(np.float32)], 24000
    )
    model.generate_voice_design.return_value = (
        [np.random.randn(24000).astype(np.float32)], 24000
    )
    model.generate_voice_clone.return_value = (
        [np.random.randn(24000).astype(np.float32)], 24000
    )
    model.get_supported_languages.return_value = ["zh","en","ja","ko","de","fr","ru","pt","es","it"]
    model.create_voice_clone_prompt.return_value = [MagicMock(
        ref_code=np.zeros((1, 256)),
        ref_spk_embedding=np.zeros(256)
    )]
    return model


@pytest.fixture
def mock_engine(mock_model, tmp_path):
    """Mock PodcastEngine with mocked model."""
    # Patch get_model in podcast_engine to return our mock_model
    with patch("backend.podcast_engine.get_model", return_value=mock_model):
        from backend.podcast_engine import PodcastEngine
        # ⚡ Bolt: Use test_mode to disable background threads/Bolt precomputations during tests
        engine = PodcastEngine(test_mode=True)
        # Explicitly mock methods to avoid 'method object has no attribute return_value'
        engine.generate_segment = MagicMock(return_value=(np.zeros(1000), 24000))
        engine.generate_podcast = MagicMock(return_value={"waveform": np.zeros(1000), "sample_rate": 24000})
        engine.stream_synthesize = MagicMock()
        
        # Mock get_system_status to avoid real hardware checks
        engine.get_system_status = MagicMock(return_value={
            "status": "ready",
            "device": "cpu",
            "models_loaded": []
        })
        # Add a temp upload_dir
        upload_dir = tmp_path / "uploads"
        upload_dir.mkdir()
        engine.upload_dir = upload_dir
        yield engine


@pytest.fixture
def test_audio():
    """Generate a 3-second test audio at 24kHz."""
    sr = 24000
    duration = 3.0
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    # 440 Hz sine wave
    wav = (0.5 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
    return wav, sr


@pytest.fixture
def test_audio_file(test_audio, tmp_path):
    """Save test audio to a temp WAV file."""
    import soundfile as sf
    wav, sr = test_audio
    path = tmp_path / "test_input.wav"
    sf.write(str(path), wav, sr)
    return str(path)


@pytest.fixture
def sample_profiles():
    """Sample voice profiles for testing."""
    return {
        "Alice": {"type": "preset", "value": "Aiden"},
        "Bob": {"type": "design", "value": "A deep male voice with warm tones"},
    }


@pytest.fixture
def sample_script():
    """Sample podcast script for testing."""
    return [
        {"role": "Alice", "text": "Hello and welcome to the show.", "language": "en"},
        {"role": "Bob", "text": "Thanks for having me.", "language": "en"},
        {"role": "Alice", "text": "Let's get started.", "language": "en"},
    ]


@pytest.fixture
def app_client(mock_engine):
    """Async test client for FastAPI app with mocked engine."""
    from httpx import AsyncClient, ASGITransport
    from server import app
    import backend.server_state
    
    # Inject mock engine into server state
    backend.server_state.engine = mock_engine
    
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.fixture(scope="session")
def start_server():
    """Start the uvicorn server in a subprocess for E2E tests."""
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "server:app", "--host", "127.0.0.1", "--port", "8080"],
        cwd=str(Path(__file__).parent.parent / "src"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server to be ready
    import httpx
    for _ in range(30):
        try:
            response = httpx.get("http://127.0.0.1:8080/api/health", timeout=2)
            if response.status_code == 200:
                break
        except (httpx.ConnectError, httpx.TimeoutException):
            pass
        time.sleep(1)
    else:
        # Check stderr for errors
        stdout, stderr = process.communicate()
        print(f"Server STDOUT: {stdout.decode()}")
        print(f"Server STDERR: {stderr.decode()}")
        process.terminate()
        raise RuntimeError("Server failed to start")

    yield process
    process.terminate()
    process.wait()
