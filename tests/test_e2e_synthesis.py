import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

# We will import app but mock the get_model inside the engine
from server import app
from backend import server_state
import backend.podcast_engine

@pytest.fixture(scope="module")
def api_client():
    return TestClient(app)

@pytest.fixture
def mock_model():
    model = MagicMock()
    # Dummy waveform (e.g. 1 second at 24kHz)
    dummy_wav = np.zeros(24000, dtype=np.float32)
    
    # Return valid outputs for all generation tasks
    model.generate_custom_voice.return_value = ([dummy_wav], 24000)
    model.generate_voice_design.return_value = ([dummy_wav], 24000)
    model.generate_voice_clone.return_value = ([dummy_wav], 24000)
    model.get_supported_languages.return_value = ["zh","en","ja","ko","de","fr","ru"]
    
    mock_prompt = MagicMock()
    mock_prompt.ref_code = np.zeros((1, 256))
    mock_prompt.ref_spk_embedding = np.zeros(256)
    model.create_voice_clone_prompt.return_value = [mock_prompt]
    
    return model

@pytest.mark.integration
@patch("backend.engine_modules.synthesizer.get_model")
@patch("backend.config.verify_system_paths")
def test_end_to_end_synthesis_flow_api(mock_verify, mock_get_model, mock_model, api_client):
    """
    Test the full synthesis flow end-to-end via the REST API layer,
    verifying background task processing and result generation.
    """
    mock_get_model.return_value = mock_model
    
    # 1. Start generation via API
    script = [
        {"role": "Ryan", "text": "Hello, this is a test of the REST E2E pipeline."}
    ]
    profiles = {"Ryan": {"type": "preset", "value": "ryan"}}
    
    payload = {
        "profiles": profiles,
        "script": script,
        "eq_preset": "flat"
    }
    
    response = api_client.post("/api/generate/podcast", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "task_id" in data
    task_id = data["task_id"]
    
    # 2. Since TestClient runs BackgroundTasks synchronously before returning the response,
    # the task should already be in COMPLETED status in the task manager.
    status_response = api_client.get(f"/api/tasks/{task_id}")
    assert status_response.status_code == 200
    task_data = status_response.json()
    
    assert task_data["status"] == "completed"
    assert "result" in task_data
    
    # The result should be the HTTP-ready bytes array of the WAV file
    # Verify it has standard WAV headers or at least content
    assert task_data["result"] is not None
