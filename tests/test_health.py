import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

def test_enhanced_health_check():
    """Test that the health check returns detailed system status."""
    
    # Patch the global engine instance in server.py
    with patch("backend.server_state.engine") as mock_engine:
        from server import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
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
        
        response = client.get("/api/health")
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
