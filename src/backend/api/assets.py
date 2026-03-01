from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import os
import shutil
from pathlib import Path
from ..config import SHARED_ASSETS_DIR, logger
from ..utils import validate_safe_path

router = APIRouter(prefix="/api/assets", tags=["assets"])

@router.get("/")
async def list_assets():
    """List all shared assets."""
    assets = []
    for f in SHARED_ASSETS_DIR.glob("*"):
        if f.is_file():
            assets.append({
                "name": f.name,
                "size": f.stat().st_size,
                "updated_at": f.stat().st_mtime
            })
    return sorted(assets, key=lambda x: x["updated_at"], reverse=True)

@router.post("/upload")
async def upload_asset(file: UploadFile = File(...)):
    """Upload a new shared asset."""
    file_path = SHARED_ASSETS_DIR / file.filename
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"Asset uploaded: {file.filename}")
        return {"message": f"Asset {file.filename} uploaded successfully"}
    except Exception as e:
        logger.error(f"Failed to upload asset {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{filename}")
async def delete_asset(filename: str):
    """Delete a shared asset."""
    file_path = SHARED_ASSETS_DIR / filename
    if not validate_safe_path(file_path, SHARED_ASSETS_DIR):
        raise HTTPException(status_code=403, detail="Unauthorized path")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Asset not found")

    try:
        file_path.unlink()
        logger.info(f"Asset deleted: {filename}")
        return {"message": f"Asset {filename} deleted"}
    except Exception as e:
        logger.error(f"Failed to delete asset {filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{filename}")
async def download_asset(filename: str):
    """Download a shared asset."""
    file_path = SHARED_ASSETS_DIR / filename
    if not validate_safe_path(file_path, SHARED_ASSETS_DIR):
        raise HTTPException(status_code=403, detail="Unauthorized path")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Asset not found")

    return FileResponse(file_path)
