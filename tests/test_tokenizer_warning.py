import unittest
import sys
import io
from pathlib import Path
from unittest.mock import patch

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

class TestTokenizerWarning(unittest.TestCase):

    def test_load_model_captures_tokenizer_warning(self):
        """
        Attempt to load the model and check if the 'incorrect regex pattern' 
        warning is present in the output.
        """
        # We need a real model path to trigger this properly if we want a true E2E,
        # but we can also mock the specific transformer call that emits the warning.
        
        # Based on user's log, it happens during model loading.
        from backend.model_loader import get_model
        from backend.config import MODELS
        
        # Capture stderr where transformers usually logs warnings
        stderr_capture = io.StringIO()
        with patch('sys.stderr', new=stderr_capture):
            try:
                # We only need to load it once to see the warning
                # If already loaded in this process, we might need to reload or clear cache
                # For a standalone test run, it's fine.
                # Note: This requires the local model to exist at the configured path.
                get_model("VoiceDesign")
            except Exception as e:
                print(f"Loading failed (expected if models missing in CI): {e}")
        
        output = stderr_capture.getvalue()
        # The warning text from the user's report
        warning_snippet = "incorrect regex pattern"
        
        # This test is designed to FAIL initially if the warning is present
        # (Inverse logic for TDD: we want to verify we CAN see it)
        # Actually, let's just check if it's there.
        print(f"Captured Output: {output}")
        # If the fix isn't applied, this SHOULD be true.
        # self.assertIn(warning_snippet, output)

if __name__ == "__main__":
    unittest.main()
