import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

# Mocking the engine for API test
mock_engine = MagicMock()

with patch("backend.podcast_engine.PodcastEngine", return_value=mock_engine):
    from server import app

client = TestClient(app)

def test_enhanced_health_check():
    """Test that the health check returns detailed system status."""
    # Setup mock return value
    mock_engine.get_system_status.return_value = {
        "status": "ok",
        "models": {
            "models_dir_exists": True,
            "found_models": ["1.7B_VoiceDesign", "1.7B_Base"]
        },
        "device": {
            "type": "cuda",
            "cuda_available": True
        }
    }
    
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "models" in data
    assert data["models"]["models_dir_exists"] is True
    assert "device" in data
    assert data["device"]["type"] == "cuda"

if __name__ == "__main__":
    pytest.main([__file__])
