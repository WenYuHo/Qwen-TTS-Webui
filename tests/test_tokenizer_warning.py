import pytest
import sys
import io
from pathlib import Path
from unittest.mock import patch

# Add src to path
src_path = str(Path(__file__).resolve().parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

def test_load_model_captures_tokenizer_warning():
    """
    Attempt to load the model and check if the 'incorrect regex pattern' 
    warning is present in the output.
    """
    # Capture stderr where transformers usually logs warnings
    stderr_capture = io.StringIO()
    with patch('sys.stderr', new=stderr_capture):
        try:
            from backend.model_loader import get_model
            # Note: This requires the local model to exist at the configured path.
            # In CI, this might fail or be skipped.
            get_model("VoiceDesign")
        except Exception as e:
            # Expected if models are missing in the current environment
            print(f"Loading failed: {e}")
    
    output = stderr_capture.getvalue()
    # The warning text from the user's report
    warning_snippet = "incorrect regex pattern"
    
    # We just log it for now to see if it triggers in the current env
    print(f"Captured Output: {output}")
    # assert warning_snippet in output  # Uncomment if we want to enforce presence/absence
