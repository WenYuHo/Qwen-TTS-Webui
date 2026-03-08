import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

# Mock engine to avoid loading large models during tests
mock_engine = MagicMock()
with patch("backend.podcast_engine.PodcastEngine", return_value=mock_engine):
    from server import app

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_clear_cache_endpoint(client):
    """Verify that the cache clearing endpoint returns success and correct structure."""
    response = await client.post("/api/system/cache/clear")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "message" in data
    assert "pruned_count" in data
    assert "storage_stats" in data
    assert "last_cleanup" in data["storage_stats"]

@pytest.mark.asyncio
async def test_system_stats_endpoint(client):
    """Verify that system stats include storage info."""
    response = await client.get("/api/system/stats")
    assert response.status_code == 200
    data = response.json()
    assert "cpu_percent" in data
    assert "ram_percent" in data
    assert "storage" in data
    assert "total_pruned" in data["storage"]
