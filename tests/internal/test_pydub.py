import os
import pytest
from pathlib import Path
from pydub import AudioSegment
from backend.config import BIN_DIR

def test_pydub_basic_ops():
    """Verify basic pydub operations and bin paths."""
    print(f"BIN_DIR: {BIN_DIR}")
    assert BIN_DIR.exists(), f"BIN_DIR {BIN_DIR} does not exist"

    try:
        # This might trigger warning if ffmpeg/sox not found
        seg = AudioSegment.silent(duration=100)
        assert seg.duration_seconds == pytest.approx(0.1, rel=1e-2)
        
        # Try exporting
        test_file = "test_pydub_tmp.wav"
        seg.export(test_file, format="wav")
        assert os.path.exists(test_file)
        os.remove(test_file)
    except Exception as e:
        pytest.fail(f"Pydub error: {e}")
