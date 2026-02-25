from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from .schemas import ProjectData
from ..config import PROJECTS_DIR, logger

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
