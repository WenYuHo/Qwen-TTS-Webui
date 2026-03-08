import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from server import app
from backend.config import SHARED_ASSETS_DIR
from pathlib import Path

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_upload_asset_path_traversal(client):
    # Attempt to upload a file outside the shared assets directory
    # Using a nested path to test Path(file.filename).name
    filename = "../../traversal_test.txt"
    files = {"file": (filename, b"evil content")}

    # We expect this to succeed but with the sanitized name "traversal_test.txt"
    # because Path("../../traversal_test.txt").name is "traversal_test.txt"
    response = await client.post("/api/assets/upload", files=files)

    assert response.status_code == 200
    assert response.json()["message"] == "Asset traversal_test.txt uploaded successfully"

    # Check that it was NOT created in the parent directory
    traversal_file = SHARED_ASSETS_DIR.parent / "traversal_test.txt"
    assert not traversal_file.exists(), "Path traversal successful! File created outside SHARED_ASSETS_DIR"

    # Check that it WAS created in the shared assets directory with the safe name
    safe_file = SHARED_ASSETS_DIR / "traversal_test.txt"
    assert safe_file.exists(), "Sanitized file not found in SHARED_ASSETS_DIR"

    # Cleanup
    if safe_file.exists():
        safe_file.unlink()

@pytest.mark.asyncio
async def test_upload_asset_invalid_name(client):
    # Test a name that might still cause issues if not for .name
    # Though Path(".").name is "" which would fail our validation
    filename = "."
    files = {"file": (filename, b"content")}

    response = await client.post("/api/assets/upload", files=files)
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid filename"
