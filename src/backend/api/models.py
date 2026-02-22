from fastapi import APIRouter, BackgroundTasks
from .schemas import DownloadRequest
from ..server_state import engine, task_manager
from ..model_downloader import get_model_inventory, download_qwen_model_task
from ..task_manager import TaskStatus

router = APIRouter(prefix="/api/models", tags=["models"])

@router.get("/inventory")
async def get_inventory():
    return {"models": get_model_inventory()}

@router.post("/download")
async def trigger_download(request: DownloadRequest, background_tasks: BackgroundTasks):
    task_id = task_manager.create_task("model_download", {"repo_id": request.repo_id})
    background_tasks.add_task(download_qwen_model_task, task_id, request.repo_id)
    return {"task_id": task_id, "status": TaskStatus.PENDING}

@router.get("/health")
async def health_check():
    return engine.get_system_status()
