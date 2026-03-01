from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import zipfile
import io
import os
import json
from pathlib import Path
from .schemas import ProjectData
from ..config import PROJECTS_DIR, VIDEO_DIR, SHARED_ASSETS_DIR, logger

router = APIRouter(prefix="/api/projects", tags=["projects"])

@router.get("")
async def list_projects():
    return {"projects": [f.stem for f in PROJECTS_DIR.glob("*.json") if f.stem != "voices"]}

@router.post("/{name}")
async def save_project(name: str, data: ProjectData):
    safe_name = "".join([c for c in name if c.isalnum() or c in (' ', '-', '_')]).strip()
    # Security: Prevent overwriting the system voices library
    if not safe_name or safe_name.lower() == "voices":
        raise HTTPException(status_code=400, detail="Invalid project name")

    file_path = PROJECTS_DIR / f"{safe_name}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(data.model_dump_json())
    return {"status": "saved", "name": safe_name}

@router.get("/{name}")
async def load_project(name: str):
    # Security: check if name is safe
    safe_name = "".join([c for c in name if c.isalnum() or c in (' ', '-', '_')]).strip()
    # Security: Prevent loading the system voices library through project API
    if not safe_name or safe_name.lower() == "voices":
        raise HTTPException(status_code=400, detail="Invalid project name")

    file_path = PROJECTS_DIR / f"{safe_name}.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(file_path)

@router.get("/{name}/export")
async def export_project(name: str):
    """Export project as a ZIP bundle containing JSON, audio, and video."""
    safe_name = "".join([c for c in name if c.isalnum() or c in (' ', '-', '_')]).strip()
    if not safe_name or safe_name.lower() == "voices":
        raise HTTPException(status_code=400, detail="Invalid project name")

    project_file = PROJECTS_DIR / f"{safe_name}.json"
    if not project_file.exists():
        raise HTTPException(status_code=404, detail="Project not found")

    # Create ZIP in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        # 1. Add project JSON
        zip_file.write(project_file, f"{safe_name}.json")

        # 2. Try to find and add generated video
        video_file = VIDEO_DIR / f"{safe_name}.mp4"
        if video_file.exists():
            zip_file.write(video_file, f"{safe_name}.mp4")

    zip_buffer.seek(0)

    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        zip_buffer,
        media_type="application/x-zip-compressed",
        headers={"Content-Disposition": f"attachment; filename={safe_name}_bundle.zip"}
    )
