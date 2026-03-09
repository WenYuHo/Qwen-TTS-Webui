import pytest
import json
from unittest.mock import MagicMock, patch
from backend.utils.lip_sync import generate_viseme_timestamps, export_lip_sync_json

def test_lip_sync_generation():
    text = "Hello world"
    duration = 2.0
    timestamps = generate_viseme_timestamps(text, duration)
    
    assert len(timestamps) > 0
    assert timestamps[0]["start"] == 0
    assert timestamps[-1]["end"] == 2.0
    for t in timestamps:
        assert "value" in t
        assert t["value"] in "ABCDEFGHX"

def test_lip_sync_export():
    text = "Testing"
    duration = 1.5
    json_str = export_lip_sync_json(text, duration)
    data = json.loads(json_str)
    
    assert "metadata" in data
    assert "mouthCues" in data
    assert data["metadata"]["text"] == text
    assert len(data["mouthCues"]) > 0

def test_chinese_heuristic():
    text = "你好世界"
    duration = 1.0
    timestamps = generate_viseme_timestamps(text, duration, language="zh")
    assert len(timestamps) > 0
