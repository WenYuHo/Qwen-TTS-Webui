import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import sys
from pathlib import Path
import os
import shutil

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from server import app
from backend.config import SHARED_ASSETS_DIR

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_assets_lifecycle(client):
    # Ensure clean start for test
    for f in SHARED_ASSETS_DIR.glob("*"):
        f.unlink()

    # 1. List assets (should be empty initially)
    resp = await client.get("/api/assets/")
    assert resp.status_code == 200
    assert len(resp.json()) == 0

    # 2. Upload a dummy asset
    test_file = Path("test_asset.txt")
    test_file.write_text("dummy asset content")

    try:
        with open(test_file, "rb") as f:
            resp = await client.post("/api/assets/upload", files={"file": ("test_asset.txt", f, "text/plain")})

        assert resp.status_code == 200
        assert "uploaded successfully" in resp.json()["message"]

        # 3. Verify it exists in list
        resp = await client.get("/api/assets/")
        assert len(resp.json()) == 1
        assert resp.json()[0]["name"] == "test_asset.txt"

        # 4. Download it
        resp = await client.get("/api/assets/download/test_asset.txt")
        assert resp.status_code == 200
        assert resp.text == "dummy asset content"

        # 5. Delete it
        resp = await client.delete("/api/assets/test_asset.txt")
        assert resp.status_code == 200
        assert "deleted" in resp.json()["message"]

        # 6. Verify it's gone
        resp = await client.get("/api/assets/")
        assert len(resp.json()) == 0
    finally:
        if test_file.exists():
            test_file.unlink()

@pytest.mark.asyncio
async def test_safe_path(client):
    resp = await client.delete("/api/assets/..%2F..%2Fetc%2Fpasswd")
    assert resp.status_code in [403, 404]
