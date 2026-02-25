import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

# We mock the heavy dependencies only when needed or via patch
def test_partial_path_traversal_logic():
    # Test the logic in PodcastEngine._resolve_paths
    with patch("backend.podcast_engine.get_model"), \
         patch("backend.podcast_engine.AudioSegment"):
        from backend.podcast_engine import PodcastEngine
        engine = PodcastEngine()

        uploads_dir = Path("/tmp/uploads").resolve()
        confidential_dir = Path("/tmp/uploads_confidential").resolve()

        engine.upload_dir = uploads_dir

        # is_relative_to should block this
        assert not confidential_dir.is_relative_to(uploads_dir)

        with pytest.raises(ValueError, match="Access denied"):
            engine._resolve_paths(str(confidential_dir / "secret.wav"))

def test_project_api_voices_protection():
    with patch("backend.api.projects.PROJECTS_DIR", Path("/tmp/projects")):
        from backend.api.projects import save_project, load_project
        from backend.api.schemas import ProjectData

        # Test saving "voices" project is blocked
        with pytest.raises(Exception) as excinfo:
            import asyncio
            asyncio.run(save_project("voices", ProjectData(name="voices", blocks=[])))
        # FastAPI raises HTTPException which we can check if we run it properly,
        # but here we just check if it was raised.
        # Since we're calling it directly, it will raise HTTPException.
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as excinfo:
            asyncio.run(save_project("voices", ProjectData(name="voices", blocks=[])))
        assert excinfo.value.status_code == 400

        with pytest.raises(HTTPException) as excinfo:
            asyncio.run(load_project("voices"))
        assert excinfo.value.status_code == 400

def test_validate_safe_path_robustness():
    from backend.utils import validate_safe_path
    base = Path("/tmp/base").resolve()

    # Partial match bypass attempt
    with pytest.raises(ValueError, match="path escapes base directory"):
        validate_safe_path(base, "../base_extra/file.txt")

    # Standard traversal
    with pytest.raises(ValueError, match="path escapes base directory"):
        validate_safe_path(base, "../../etc/passwd")
