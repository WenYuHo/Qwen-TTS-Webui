import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

@pytest_asyncio.fixture
async def client():
    # Patch the global engine instance in server_state/server before importing app
    with patch("backend.server_state.engine") as mock_engine:
        from server import app
        # Store mock_engine on the app instance for the test to access
        app.state.mock_engine = mock_engine
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            yield ac

@pytest.mark.asyncio
async def test_enhanced_health_check(client):
    """Test that the health check returns detailed system status."""
    
    # client fixture yields AsyncClient, and we need to access the mock
    # Wait, the fixture setup above imports app. We can access app.state.mock_engine.
    from server import app
    mock_engine = app.state.mock_engine
    
    # Setup mock return value for the instance
    mock_engine.get_system_status.return_value = {
        "status": "ok",
        "models": {
            "models_dir_exists": True,
            "found_models": ["1.7B_VoiceDesign", "1.7B_Base"]
        },
        "device": {
            "type": "cuda",
            "cuda_available": True
        },
        "performance": {
            "cpu_percent": 10.5,
            "memory_percent": 45.2
        }
    }
    
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "models" in data
    assert data["models"]["models_dir_exists"] is True
    assert "device" in data
    assert data["device"]["type"] == "cuda"
    assert "performance" in data
    assert data["performance"]["cpu_percent"] == 10.5

if __name__ == "__main__":
    pytest.main([__file__])
