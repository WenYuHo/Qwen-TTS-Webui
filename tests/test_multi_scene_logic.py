import pytest
from unittest.mock import MagicMock, patch
import numpy as np
import sys
from pathlib import Path

from backend.api.video import run_narrated_video_task
from backend.api.schemas import NarratedVideoRequest, VideoScene

@pytest.fixture
def mock_server_state():
    with patch("backend.api.video.server_state") as mock:
        from backend.task_manager import TaskStatus
        mock.TaskStatus = TaskStatus
        yield mock

@pytest.fixture
def mock_video_engine():
    with patch("backend.api.video._get_video_engine") as mock_get:
        engine = MagicMock()
        mock_get.return_value = engine
        yield engine

@patch("backend.api.video._concat_scenes")
@patch("backend.api.video.VIDEO_OUTPUT_DIR")
@patch("backend.utils.subtitles.burn_subtitles")
@patch("backend.utils.subtitles.generate_srt")
def test_multi_scene_logic_flow(mock_gen_srt, mock_burn, mock_output_dir, mock_concat, mock_video_engine, mock_server_state):
    # Setup
    mock_concat.return_value = "final_output.mp4"
    mock_burn.return_value = "final_output_subtitled.mp4"
    mock_gen_srt.return_value = "1\n00:00:00,000 --> 00:00:01,000\nTest\n"
    
    # Mocking Path objects is tricky, let's just mock the __truediv__ to return another mock
    mock_path = MagicMock()
    mock_output_dir.__truediv__.return_value = mock_path
    
    tts_engine = MagicMock()
    # Mock TTS to return 1 second of audio (24k samples at 24k SR)
    tts_engine.generate_segment.return_value = (np.zeros(24000), 24000) 
    mock_server_state.engine = tts_engine
    
    # Mock video generation to return a path
    mock_video_engine.generate_narrated_video.return_value = {"video_path": "scene_clip.mp4"}
    
    request = NarratedVideoRequest(
        scenes=[
            VideoScene(video_prompt="Prompt 1", narration_text="Text 1"),
            VideoScene(video_prompt="Prompt 2", narration_text="Text 2", transition="fade")
        ],
        subtitle_enabled=True
    )
    
    # Run
    # We need to mock 'open' to avoid writing actual files
    with patch("builtins.open", MagicMock()):
        run_narrated_video_task("task-123", request)
    
    # Verify calls
    assert tts_engine.generate_segment.call_count == 2
    assert mock_video_engine.generate_narrated_video.call_count == 2
    assert mock_concat.call_count == 1
    assert mock_burn.call_count == 1
    
    # Verify Task Manager updates
    # The last call should be COMPLETED
    last_call = mock_server_state.task_manager.update_task.call_args_list[-1]
    args, kwargs = last_call
    assert args[0] == "task-123"
    assert kwargs["status"] == mock_server_state.TaskStatus.COMPLETED
    assert kwargs["result"]["video_path"] == "final_output_subtitled.mp4"
    assert kwargs["result"]["scenes"] == 2
    assert "srt_path" in kwargs["result"]

def test_legacy_single_scene_compat(mock_video_engine, mock_server_state):
    # Setup
    tts_engine = MagicMock()
    tts_engine.generate_segment.return_value = (np.zeros(24000), 24000) 
    mock_server_state.engine = tts_engine
    mock_video_engine.generate_narrated_video.return_value = {"video_path": "legacy.mp4"}
    
    request = NarratedVideoRequest(
        prompt="Legacy Prompt",
        narration_text="Legacy Text"
    )
    
    # Run
    with patch("builtins.open", MagicMock()):
        run_narrated_video_task("task-legacy", request)
    
    # Verify
    assert tts_engine.generate_segment.call_count == 1
    assert mock_video_engine.generate_narrated_video.call_count == 1
    
    last_call = mock_server_state.task_manager.update_task.call_args_list[-1]
    args, kwargs = last_call
    assert kwargs["result"]["video_path"] == "legacy.mp4"
