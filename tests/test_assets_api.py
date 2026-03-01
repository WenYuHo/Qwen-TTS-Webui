import pytest
from fastapi.testclient import TestClient
from src.server import app
import os
import shutil
from pathlib import Path
from src.backend.config import SHARED_ASSETS_DIR

client = TestClient(app)

def test_assets_lifecycle():
    # Ensure clean start for test
    for f in SHARED_ASSETS_DIR.glob("*"):
        f.unlink()

    # 1. List assets (should be empty initially)
    resp = client.get("/api/assets/")
    assert resp.status_code == 200
    assert len(resp.json()) == 0

    # 2. Upload a dummy asset
    test_file = Path("test_asset.txt")
    test_file.write_text("dummy asset content")

    with open(test_file, "rb") as f:
        resp = client.post("/api/assets/upload", files={"file": ("test_asset.txt", f, "text/plain")})

    assert resp.status_code == 200
    assert "uploaded successfully" in resp.json()["message"]

    # 3. Verify it exists in list
    resp = client.get("/api/assets/")
    assert len(resp.json()) == 1
    assert resp.json()[0]["name"] == "test_asset.txt"

    # 4. Download it
    resp = client.get("/api/assets/download/test_asset.txt")
    assert resp.status_code == 200
    assert resp.text == "dummy asset content"

    # 5. Delete it
    resp = client.delete("/api/assets/test_asset.txt")
    assert resp.status_code == 200
    assert "deleted" in resp.json()["message"]

    # 6. Verify it's gone
    resp = client.get("/api/assets/")
    assert len(resp.json()) == 0

    if test_file.exists():
        test_file.unlink()

def test_safe_path():
    resp = client.delete("/api/assets/..%2F..%2Fetc%2Fpasswd")
    assert resp.status_code in [403, 404]
