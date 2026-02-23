import pytest
import numpy as np
from pathlib import Path
from PIL import Image
from backend.video_engine import VideoEngine
from backend.api.schemas import ProjectData, ProjectBlock
from unittest.mock import MagicMock, patch

def test_create_text_image():
    engine = VideoEngine(MagicMock())
    img_arr = engine._create_text_image("Hello World", 1920, 1080)

    assert isinstance(img_arr, np.ndarray)
    assert img_arr.shape == (1080, 1920, 4)
    # Check if there is some non-zero data (the text)
    assert np.any(img_arr != 0)

def test_process_image():
    engine = VideoEngine(MagicMock())
    # Create a dummy image
    img = Image.new("RGB", (1000, 500), (255, 0, 0))
    img_path = Path("test_img.jpg")
    img.save(img_path)

    try:
        processed = engine._process_image(img_path, 1920, 1080)
        assert processed.size == (1920, 1080)
    finally:
        if img_path.exists():
            img_path.unlink()

def test_get_font_fallback():
    engine = VideoEngine(MagicMock())
    font = engine._get_font(20, "NonExistentFont.ttf")
    assert font is not None

def test_ken_burns_effect():
    engine = VideoEngine(MagicMock())
    from moviepy import ImageClip

    img = np.zeros((100, 100, 3), dtype=np.uint8)
    clip = ImageClip(img).with_duration(2)

    # We just want to make sure it doesn't crash and returns a clip
    zoomed = engine._apply_ken_burns(clip, 2)
    assert zoomed is not None

def test_generate_video_progress():
    mock_engine = MagicMock()
    mock_engine.generate_segment.return_value = (np.zeros(100), 16000)

    engine = VideoEngine(mock_engine)
    project = ProjectData(name="Test", blocks=[ProjectBlock(id="1", role="R", text="Hi", status="idle")])

    progress_values = []
    def callback(p): progress_values.append(p)

    # We mock write_videofile to avoid actual rendering
    with patch("moviepy.CompositeVideoClip.write_videofile"):
        engine.generate_video(project, progress_callback=callback)

    assert len(progress_values) > 0
    assert 90 in progress_values
