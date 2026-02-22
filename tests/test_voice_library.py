from fastapi.testclient import TestClient
import sys
from pathlib import Path
import os
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from server import app

client = TestClient(app)

def test_voice_library_persistence():
    # 1. Clear library
    lib_file = Path("projects/voices.json")
    if lib_file.exists():
        lib_file.unlink()

    # 2. Get empty library
    response = client.get("/api/voice/library")
    assert response.status_code == 200
    assert response.json()["voices"] == []

    # 3. Save a voice
    test_voices = [
        {"id": 1, "name": "Test Voice", "type": "design", "value": "A calm voice"}
    ]
    response = client.post("/api/voice/library", json={"voices": test_voices})
    assert response.status_code == 200

    # 4. Verify file exists
    assert lib_file.exists()

    # 5. Get library again
    response = client.get("/api/voice/library")
    assert response.status_code == 200
    assert len(response.json()["voices"]) == 1
    assert response.json()["voices"][0]["name"] == "Test Voice"

    # Cleanup
    if lib_file.exists():
        lib_file.unlink()
