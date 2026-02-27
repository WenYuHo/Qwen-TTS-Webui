import pytest
from fastapi import HTTPException
from unittest.mock import MagicMock, patch
import numpy as np
import io

@pytest.mark.asyncio
async def test_voice_preview_security_and_resource():
    with patch("backend.server_state.engine") as mock_engine:
        from backend.api.voices import voice_preview
        from backend.api.schemas import SpeakerProfile

        # Mock engine synthesis
        mock_wav = np.zeros(1000, dtype=np.float32)
        mock_sr = 24000
        mock_engine.generate_segment.return_value = (mock_wav, mock_sr)

        request = SpeakerProfile(role="test", type="preset", value="ryan")

        # 1. Test success returns StreamingResponse
        from fastapi.responses import StreamingResponse
        response = await voice_preview(request)
        assert isinstance(response, StreamingResponse)
        assert response.media_type == "audio/wav"

        # 2. Test error hides details
        mock_engine.generate_segment.side_effect = Exception("Sensitive internal path: /secret/keys")

        with pytest.raises(HTTPException) as excinfo:
            await voice_preview(request)

        assert excinfo.value.status_code == 500
        assert "Sensitive" not in str(excinfo.value.detail)
        assert excinfo.value.detail == "Preview generation failed"

@pytest.mark.asyncio
async def test_voice_mix_error_hiding():
    with patch("backend.server_state.engine") as mock_engine:
        from backend.api.voices import voice_mix
        from backend.api.schemas import MixRequest

        mock_engine.get_speaker_embedding.side_effect = Exception("Database connection string: postgres://user:pass@host")

        request = MixRequest(name="test", voices=[{"profile": {"type": "preset", "value": "ryan"}}])

        with pytest.raises(HTTPException) as excinfo:
            await voice_mix(request)

        assert excinfo.value.status_code == 500
        assert "Database" not in str(excinfo.value.detail)
        assert excinfo.value.detail == "Voice mix validation failed"

def test_task_error_sanitization():
    from backend.api.generation import run_synthesis_task
    from backend.api.schemas import PodcastRequest, ScriptLine
    from backend import server_state

    with patch("backend.server_state.task_manager") as mock_tm, \
         patch("backend.server_state.engine") as mock_engine:

        mock_engine.generate_segment.side_effect = Exception("CUDA Error: Device /dev/nvidia0 failed")

        request = PodcastRequest(profiles=[], script=[ScriptLine(role="A", text="hi")])

        # This runs synchronously in our test
        run_synthesis_task("task_123", False, request)

        # Check that update_task was called with sanitized error
        calls = mock_tm.update_task.call_args_list
        # The last call should be the FAILED status
        failed_call = next(c for c in calls if c.kwargs.get('status') == server_state.TaskStatus.FAILED)

        assert "nvidia0" not in failed_call.kwargs['error']
        assert failed_call.kwargs['error'] == "Synthesis error"
        assert "check your inputs or logs" in failed_call.kwargs['message']
