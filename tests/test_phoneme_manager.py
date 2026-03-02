import pytest
from pathlib import Path
import sys
import json

# Add src to path
ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = str(ROOT_DIR / "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from backend.utils import PhonemeManager

def test_phoneme_manager_replacement(tmp_path):
    # Mock projects dir
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir()

    # Patch PROJECTS_DIR in utils or just use the manager with a custom path
    from backend import utils
    original_projects_dir = utils.PROJECTS_DIR
    utils.PROJECTS_DIR = projects_dir

    try:
        pm = PhonemeManager()
        pm.file_path = projects_dir / "phonemes.json"

        overrides = {
            "Apple": "A-P-P-L-E",
            "Banana": "B-A-N-A-N-A"
        }
        pm.save(overrides)

        text = "I like Apple and Banana."
        result = pm.apply(text)

        assert result == "I like A-P-P-L-E and B-A-N-A-N-A."

        # Test case insensitivity
        text_lower = "i like apple and banana."
        result_lower = pm.apply(text_lower)
        assert result_lower == "i like A-P-P-L-E and B-A-N-A-N-A."

        # Test word boundaries
        text_boundary = "Apples are not Apple."
        result_boundary = pm.apply(text_boundary)
        assert result_boundary == "Apples are not A-P-P-L-E."

    finally:
        utils.PROJECTS_DIR = original_projects_dir

def test_phoneme_manager_empty():
    pm = PhonemeManager()
    pm.overrides = {}
    pm.compiled_patterns = {}

    text = "Hello world"
    assert pm.apply(text) == text
