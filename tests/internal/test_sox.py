import os
import subprocess
import pytest
from pathlib import Path
from backend.config import BIN_DIR

def test_sox_installation():
    """Verify that sox is installed and accessible."""
    print(f"BIN_DIR: {BIN_DIR}")
    assert BIN_DIR.exists(), f"BIN_DIR {BIN_DIR} does not exist"

    # Try running sox --version
    try:
        result = subprocess.run(["sox", "--version"], capture_output=True, text=True, check=True)
        assert "sox" in result.stdout.lower()
        print(f"Sox version: {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        pytest.fail(f"Failed to run sox: {e}")

def test_sox_python_import():
    """Verify that the sox python package is functional."""
    try:
        import sox
        assert hasattr(sox, 'Transformer'), "sox package missing Transformer class"
        tfm = sox.Transformer()
        assert tfm is not None
        print("Successfully created sox.Transformer")
    except Exception as e:
        pytest.fail(f"Sox python package error: {e}")
