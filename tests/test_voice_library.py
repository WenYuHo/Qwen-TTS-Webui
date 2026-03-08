import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import sys
from pathlib import Path
import os
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from server import app

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_voice_library_persistence(client):
    # 1. Clear library
    lib_file = Path("projects/voices.json")
    if lib_file.exists():
        lib_file.unlink()

    # 2. Get empty library
    response = await client.get("/api/voice/library")
    assert response.status_code == 200
    assert response.json()["voices"] == []

    # 3. Save a voice
    test_voices = [
        {"id": 1, "name": "Test Voice", "type": "design", "value": "A calm voice"}
    ]
    response = await client.post("/api/voice/library", json={"voices": test_voices})
    assert response.status_code == 200

    # 4. Verify file exists
    assert lib_file.exists()

    # 5. Get library again
    response = await client.get("/api/voice/library")
    assert response.status_code == 200
    assert len(response.json()["voices"]) == 1
    assert response.json()["voices"][0]["name"] == "Test Voice"

    # Cleanup
    if lib_file.exists():
        lib_file.unlink()
