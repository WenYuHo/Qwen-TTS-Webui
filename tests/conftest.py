import sys
import os
from pathlib import Path

# Add src to PYTHONPATH
src_path = str(Path(__file__).resolve().parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Mock sox before anything else
try:
    import backend.sox_shim as sox_shim
    sox_shim.mock_sox()
except Exception:
    pass
