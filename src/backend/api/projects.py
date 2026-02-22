from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, field_validator
from typing import List, Optional, Any, Dict
from pathlib import Path
import logging

router = APIRouter(prefix="/api/projects", tags=["projects"])
logger = logging.getLogger("studio")

PROJECTS_DIR = Path("projects")
PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

class ProjectBlock(BaseModel):
    id: str
    role: str
    text: str
    status: str
    language: Optional[str] = "auto"
    pause_after: Optional[float] = 0.5

class ProjectData(BaseModel):
    name: str
    blocks: List[ProjectBlock]
    script_draft: Optional[str] = ""
    voices: Optional[List[Dict[str, Any]]] = []

    @field_validator('name')
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Project name cannot be empty')
        return v.strip()

@router.get("")
async def list_projects():
    return {"projects": [f.stem for f in PROJECTS_DIR.glob("*.json") if f.stem != "voices"]}

@router.post("/{name}")
async def save_project(name: str, data: ProjectData):
    safe_name = "".join([c for c in name if c.isalnum() or c in (' ', '-', '_')]).strip()
    if not safe_name:
        raise HTTPException(status_code=400, detail="Invalid project name")

    file_path = PROJECTS_DIR / f"{safe_name}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(data.model_dump_json())
    return {"status": "saved", "name": safe_name}

@router.get("/{name}")
async def load_project(name: str):
    # Security: check if name is safe
    safe_name = "".join([c for c in name if c.isalnum() or c in (' ', '-', '_')]).strip()
    file_path = PROJECTS_DIR / f"{safe_name}.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(file_path)
