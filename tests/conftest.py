import sys
import os
import time
import subprocess
import pytest
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

@pytest.fixture(scope="session")
def start_server():
    """Start the uvicorn server in a subprocess for E2E tests."""
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "server:app", "--host", "127.0.0.1", "--port", "8080"],
        cwd=str(Path(__file__).parent.parent / "src"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server to be ready
    import httpx
    for _ in range(30):
        try:
            response = httpx.get("http://127.0.0.1:8080/api/health", timeout=2)
            if response.status_code == 200:
                break
        except (httpx.ConnectError, httpx.TimeoutException):
            pass
        time.sleep(1)
    else:
        # Check stderr for errors
        stdout, stderr = process.communicate()
        print(f"Server STDOUT: {stdout.decode()}")
        print(f"Server STDERR: {stderr.decode()}")
        process.terminate()
        raise RuntimeError("Server failed to start")

    yield process
    process.terminate()
    process.wait()
