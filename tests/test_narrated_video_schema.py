import pytest
from pydantic import ValidationError
from backend.api.schemas import NarratedVideoRequest, VideoScene

def test_narrated_video_request_backward_compat():
    # Test legacy single-scene format
    data = {
        "prompt": "A sunset over the mountains",
        "narration_text": "The sun is setting slowly.",
        "voice_profile": {"type": "preset", "value": "Aiden"}
    }
    req = NarratedVideoRequest(**data)
    assert req.prompt == "A sunset over the mountains"
    assert req.narration_text == "The sun is setting slowly."
    assert req.scenes is None

def test_narrated_video_request_multi_scene():
    # Test new multi-scene format
    data = {
        "scenes": [
            {
                "video_prompt": "Scene 1: Space station",
                "narration_text": "Welcome to the station."
            },
            {
                "video_prompt": "Scene 2: Control room",
                "narration_text": "All systems are nominal.",
                "transition": "fade"
            }
        ],
        "subtitle_enabled": True
    }
    req = NarratedVideoRequest(**data)
    assert len(req.scenes) == 2
    assert req.scenes[1].transition == "fade"
    assert req.subtitle_enabled is True

def test_video_scene_defaults():
    scene = VideoScene(video_prompt="test", narration_text="hello")
    assert scene.transition == "cut"
    assert scene.duration_seconds is None
