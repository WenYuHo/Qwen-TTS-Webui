import sys
from unittest.mock import MagicMock

# Mock heavy dependencies and missing ones
mock_modules = [
    'torch', 'torch.nn', 'torch.optim', 'torchaudio', 'numpy',
    'soundfile', 'librosa', 'pydub', 'deep_translator', 'whisper',
    'dotenv', 'pydantic', 'fastapi'
]
for module in mock_modules:
    m = MagicMock()
    if module == 'torch':
        m.__version__ = '2.0.0'
        m.cuda.is_available.return_value = False
    sys.modules[module] = m

import pytest
from pathlib import Path
from backend.podcast_engine import PodcastEngine
from backend.utils import validate_safe_path

@pytest.fixture
def engine():
    # Instantiate without calling __init__ if possible, or ensure __init__ is safe
    return PodcastEngine()

def test_resolve_paths_partial_traversal_blocked(engine, tmp_path):
    # Setup directories
    uploads_dir = (tmp_path / "uploads").resolve()
    uploads_dir.mkdir()

    confidential_dir = (tmp_path / "uploads_confidential").resolve()
    confidential_dir.mkdir()

    secret_file = confidential_dir / "secret.wav"
    secret_file.touch()

    # Override engine's upload_dir
    engine.upload_dir = uploads_dir

    # Attempt to access confidential file via partial path match
    with pytest.raises(ValueError, match="Access denied"):
        engine._resolve_paths(str(secret_file))

def test_resolve_paths_standard_traversal_blocked(engine, tmp_path):
    uploads_dir = (tmp_path / "uploads").resolve()
    uploads_dir.mkdir()

    # File outside uploads
    outside_file = (tmp_path / "outside.wav").resolve()
    outside_file.touch()

    engine.upload_dir = uploads_dir

    with pytest.raises(ValueError, match="Access denied"):
        engine._resolve_paths("../outside.wav")

def test_resolve_paths_valid_file_allowed(engine, tmp_path):
    uploads_dir = (tmp_path / "uploads").resolve()
    uploads_dir.mkdir()

    valid_file = (uploads_dir / "test.wav").resolve()
    valid_file.touch()

    engine.upload_dir = uploads_dir

    resolved = engine._resolve_paths("test.wav")
    assert resolved[0] == valid_file

def test_validate_safe_path_partial_traversal_blocked(tmp_path):
    base_dir = (tmp_path / "base").resolve()
    base_dir.mkdir()

    confidential_dir = (tmp_path / "base_confidential").resolve()
    confidential_dir.mkdir()

    with pytest.raises(ValueError, match="path escapes base directory"):
        validate_safe_path(base_dir, "../base_confidential")
