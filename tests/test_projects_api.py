from fastapi.testclient import TestClient
import sys
import os
from pathlib import Path
import shutil
import pytest

# Add src to path
current_dir = Path(__file__).resolve().parent
src_dir = current_dir.parent / "src"
sys.path.insert(0, str(src_dir))

from server import app, PROJECTS_DIR

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_projects():
    # Setup: Create dir
    if not PROJECTS_DIR.exists():
        PROJECTS_DIR.mkdir(parents=True)
    
    # Save existing
    existing = list(PROJECTS_DIR.glob("*.json"))
    
    yield
    
    # Teardown: Remove test files
    for f in PROJECTS_DIR.glob("test_*.json"):
        f.unlink()

def test_save_and_load_project():
    project_data = {
        "name": "test_project_1",
        "blocks": [
            {"id": "b1", "role": "Narrator", "text": "Hello world", "status": "idle"}
        ],
        "script_draft": "Narrator: Hello world"
    }
    
    # 1. Save
    response = client.post("/api/projects/test_project_1", json=project_data)
    assert response.status_code == 200
    assert response.json()["status"] == "saved"
    
    # 2. List
    response = client.get("/api/projects")
    assert response.status_code == 200
    projects = response.json()["projects"]
    assert "test_project_1" in projects
    
    # 3. Load
    response = client.get("/api/projects/test_project_1")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "test_project_1"
    assert len(data["blocks"]) == 1
    assert data["blocks"][0]["text"] == "Hello world"

def test_invalid_project_name():
    response = client.post("/api/projects/   ", json={"name": " ", "blocks": []})
    assert response.status_code == 400

def test_load_nonexistent():
    response = client.get("/api/projects/nonexistent_project_xyz")
    assert response.status_code == 404
