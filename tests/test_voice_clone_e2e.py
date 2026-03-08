import pytest
import pytest_asyncio
import numpy as np
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from httpx import AsyncClient, ASGITransport
import io
import asyncio

# Add src to python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from server import app

@pytest_asyncio.fixture
async def api_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

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
    
    # Needs to return a valid prompt structure to avoid exceptions
    mock_prompt = MagicMock()
    mock_prompt.ref_code = np.zeros((1, 256))
    mock_prompt.ref_spk_embedding = np.zeros(256)
    model.create_voice_clone_prompt.return_value = [mock_prompt]
    
    return model

@pytest.fixture(scope="module", autouse=True)
def mock_global_engine():
    # Create a proper engine mock that returns (wav, sr)
    # This mock must be applied to server_state so background tasks pick it up
    mock_eng = MagicMock()
    mock_eng.upload_dir = Path("uploads").resolve()
    mock_eng.generate_segment.return_value = (np.zeros(24000, dtype=np.float32), 24000)
    
    with patch("backend.server_state.engine", mock_eng):
        yield mock_eng

async def wait_for_task(client, task_id, timeout=5):
    """Wait for a task to reach a terminal state."""
    start_time = asyncio.get_event_loop().time()
    while asyncio.get_event_loop().time() - start_time < timeout:
        resp = await client.get(f"/api/tasks/{task_id}")
        data = resp.json()
        if data["status"] in ["completed", "failed"]:
            return data
        await asyncio.sleep(0.1)
    raise TimeoutError(f"Task {task_id} timed out")

@pytest.mark.integration
@pytest.mark.asyncio
@patch("backend.engine_modules.synthesizer.VoiceSynthesizer._validate_ref_audio")
@patch("backend.engine_modules.synthesizer.get_model")
@patch("backend.config.verify_system_paths")
async def test_voice_clone_workflow_e2e(mock_verify, mock_get_model, mock_validate, mock_model, api_client, mock_global_engine):
    """
    Test E2E voice clone flow: Uploading a WAV reference then generating a clone via segment API.
    """
    mock_get_model.return_value = mock_model
    mock_validate.return_value = None  # Bypass validation
    
    # 1. Upload mock reference audio
    wav_header_bytes = b'RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80\x3e\x00\x00\x00\x7d\x00\x00\x02\x00\x10\x00data\x00\x00\x00\x00'
    files = {'file': ('test_clone_ref.wav', wav_header_bytes, 'audio/wav')}
    response = await api_client.post("/api/voice/upload", files=files)
    assert response.status_code == 200
    upload_data = response.json()
    assert "filename" in upload_data
    ref_file = upload_data["filename"]
    
    # 2. Start generation with clone profile via API
    payload = {
        "profiles": {
            "Speaker": {"type": "clone", "value": ref_file, "ref_text": "Sample reference text"}
        },
        "script": [
            {"role": "Speaker", "text": "This is a synthesized clone test."}
        ]
    }
    
    seg_response = await api_client.post("/api/generate/segment", json=payload)
    assert seg_response.status_code == 200
    seg_data = seg_response.json()
    assert "task_id" in seg_data
    task_id = seg_data["task_id"]
    
    # 3. Retrieve task status. 
    # With AsyncClient/ASGITransport, we poll until completed.
    task_data = await wait_for_task(api_client, task_id)
    assert task_data["status"] == "completed"
    assert task_data["has_result"] is True
    
    # 4. Verify binary result via the result endpoint
    result_response = await api_client.get(f"/api/tasks/{task_id}/result")
    assert result_response.status_code == 200
    assert len(result_response.content) > 0
    # Check for RIFF header in the WAV bytes
    assert result_response.content.startswith(b'RIFF')

@pytest.mark.integration
@pytest.mark.asyncio
@patch("backend.engine_modules.synthesizer.VoiceSynthesizer._validate_ref_audio")
@patch("backend.engine_modules.synthesizer.get_model")
@patch("backend.config.verify_system_paths")
async def test_voice_clone_workflow_no_ref_text(mock_verify, mock_get_model, mock_validate, mock_model, api_client, mock_global_engine):
    """
    Test voice clone flow without ref_text (embedding-only mode).
    """
    mock_get_model.return_value = mock_model
    mock_validate.return_value = None

    # 1. Upload mock reference audio
    wav_header_bytes = b'RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80\x3e\x00\x00\x00\x7d\x00\x00\x02\x00\x10\x00data\x00\x00\x00\x00'
    files = {'file': ('test_clone_ref_no_text.wav', wav_header_bytes, 'audio/wav')}
    response = await api_client.post("/api/voice/upload", files=files)
    assert response.status_code == 200
    ref_file = response.json()["filename"]

    # 2. Start generation WITHOUT ref_text
    payload = {
        "profiles": {
            "Speaker": {"type": "clone", "value": ref_file} # No ref_text
        },
        "script": [
            {"role": "Speaker", "text": "This is a synthesized clone test (no text)."}
        ]
    }

    seg_response = await api_client.post("/api/generate/segment", json=payload)
    assert seg_response.status_code == 200
    task_id = seg_response.json()["task_id"]

    # 3. Retrieve task status
    task_data = await wait_for_task(api_client, task_id)
    assert task_data["status"] == "completed"

@pytest.mark.integration
@pytest.mark.asyncio
@patch("backend.engine_modules.synthesizer.get_model")
@patch("backend.config.verify_system_paths")
async def test_voice_clone_workflow_error_nonexistent(mock_verify, mock_get_model, mock_model, api_client, mock_global_engine):
    """
    Test voice clone flow with a non-existent reference file.
    """
    # Mocking generate_segment to raise RuntimeError to simulate failure
    mock_global_engine.generate_segment.side_effect = RuntimeError("Synthesis failed: Cloning reference audio not found")

    mock_get_model.return_value = mock_model

    payload = {
        "profiles": {
            "Speaker": {"type": "clone", "value": "nonexistent_file.wav"}
        },
        "script": [
            {"role": "Speaker", "text": "This should fail."}
        ]
    }

    seg_response = await api_client.post("/api/generate/segment", json=payload)
    assert seg_response.status_code == 200
    task_id = seg_response.json()["task_id"]

    # 3. Retrieve task status. It should be FAILED.
    task_data = await wait_for_task(api_client, task_id)
    assert task_data["status"] == "failed"
    # Either my custom RuntimeError or a direct validation error
    error_msg = task_data["message"]
    assert "Cloning reference audio not found" in error_msg or \
           "Invalid audio file" in error_msg or \
           "not found" in error_msg.lower()

    # Reset side effect for other tests
    mock_global_engine.generate_segment.side_effect = None

@pytest.mark.integration
@pytest.mark.asyncio
@patch("backend.config.verify_system_paths")
async def test_task_list_api(mock_verify, api_client):
    """
    Test the task list API endpoint.
    """
    # 1. Create a dummy task via simple status endpoint check
    await api_client.get("/api/health")

    # Actually, call the segment endpoint with minimal valid payload
    payload = {
        "profiles": {"Speaker": {"type": "preset", "value": "Aiden"}},
        "script": [{"role": "Speaker", "text": "Hello"}]
    }
    await api_client.post("/api/generate/segment", json=payload)

    # 2. Check task list
    response = await api_client.get("/api/tasks/")
    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) > 0
    assert "id" in tasks[0]
    assert "status" in tasks[0]

