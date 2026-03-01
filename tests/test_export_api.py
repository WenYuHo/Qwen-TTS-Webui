import pytest
from fastapi.testclient import TestClient
from src.server import app
import os
import shutil
from pathlib import Path
from src.backend.config import PROJECTS_DIR, VIDEO_DIR
import zipfile
import io

client = TestClient(app)

def test_project_export():
    # 1. Create a dummy project
    project_name = "test_export_proj"
    project_path = PROJECTS_DIR / f"{project_name}.json"
    project_data = {
        "name": project_name,
        "blocks": [{"id": "1", "role": "ryan", "text": "test", "status": "idle"}],
        "script_draft": "",
        "voices": []
    }
    with open(project_path, "w") as f:
        import json
        json.dump(project_data, f)

    # 2. Create a dummy video file
    video_path = VIDEO_DIR / f"{project_name}.mp4"
    video_path.write_text("dummy video")

    # 3. Request export
    resp = client.get(f"/api/projects/{project_name}/export")
    assert resp.status_code == 200
    assert resp.headers["Content-Type"] == "application/x-zip-compressed"

    # 4. Verify ZIP content
    with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
        filenames = z.namelist()
        assert f"{project_name}.json" in filenames
        assert f"{project_name}.mp4" in filenames

    # Cleanup
    if project_path.exists(): project_path.unlink()
    if video_path.exists(): video_path.unlink()
