import os
import threading
from pathlib import Path
from huggingface_hub import snapshot_download
from .config import MODELS_PATH, logger, MODELS, find_model_path
from .task_manager import task_manager, TaskStatus

def download_qwen_model_task(task_id: str, repo_id: str):
    """
    Background task for downloading a model.
    """
    try:
        task_manager.update_task(task_id, status=TaskStatus.PROCESSING, progress=10, message=f"Downloading {repo_id} from Hugging Face...")

        # Determine local dir
        local_dir = MODELS_PATH / repo_id

        # Note: snapshot_download doesn't have a built-in progress callback for total percentage easily,
        # but we can at least signal it started and finished.

        snapshot_download(
            repo_id=repo_id,
            local_dir=str(local_dir),
            local_dir_use_symlinks=False,
            resume_download=True
        )

        task_manager.update_task(task_id, status=TaskStatus.COMPLETED, progress=100, message=f"Model {repo_id} downloaded successfully.")
        logger.info(f"Successfully downloaded {repo_id}")
    except Exception as e:
        logger.error(f"Failed to download {repo_id}: {e}")
        task_manager.update_task(task_id, status=TaskStatus.FAILED, error=str(e), message=f"Download failed: {e}")

def get_model_inventory():
    """
    Check status of all models.
    """
    inventory = []
    for key, repo_id in MODELS.items():
        path = find_model_path(repo_id)
        inventory.append({
            "key": key,
            "repo_id": repo_id,
            "status": "downloaded" if path else "missing",
            "path": str(path) if path else None
        })
    return inventory
