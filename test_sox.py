import os
import subprocess
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from backend.config import BIN_DIR

print(f"BIN_DIR: {BIN_DIR}")
print(f"BIN_DIR exists: {BIN_DIR.exists()}")
print(f"First 100 chars of PATH: {os.environ.get('PATH')[:100]}")

try:
    # Try running sox.exe directly
    result = subprocess.run(["sox", "--version"], capture_output=True, text=True)
    print(f"Sox version: {result.stdout.strip()}")
except Exception as e:
    print(f"Failed to run sox: {e}")

try:
    import sox
    print(f"Imported sox: {sox}")
    print(f"sox.Transformer exists: {hasattr(sox, 'Transformer')}")
    tfm = sox.Transformer()
    print("Created sox.Transformer")
except Exception as e:
    print(f"Sox python package error: {e}")
