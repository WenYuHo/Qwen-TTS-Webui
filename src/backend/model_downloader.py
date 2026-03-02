import os
import threading
from pathlib import Path
from huggingface_hub import snapshot_download
from .config import MODELS_PATH, logger, MODELS, LTX_MODELS, find_model_path, find_ltx_model
from .task_manager import task_manager, TaskStatus

def download_qwen_model_task(task_id: str, repo_id: str):
    """
    Background task for downloading a model (Qwen or LTX).
    """
    try:
        task_manager.update_task(task_id, status=TaskStatus.PROCESSING, progress=10, message=f"Downloading {repo_id} from Hugging Face...")

        # Determine local dir. LTX models go into a subfolder.
        if "LTX" in repo_id:
            from .config import LTX_MODELS_PATH
            local_dir = LTX_MODELS_PATH
        else:
            local_dir = MODELS_PATH / repo_id

        # Note: snapshot_download handles the heavy lifting
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
    Check status of all models (Qwen + LTX).
    """
    inventory = []
    # Qwen Models
    for key, repo_id in MODELS.items():
        path = find_model_path(repo_id)
        inventory.append({
            "key": key,
            "type": "audio",
            "repo_id": repo_id,
            "status": "downloaded" if path else "missing",
            "path": str(path) if path else None
        })
    
    # LTX Models
    for key, repo_id in LTX_MODELS.items():
        # Map LTX keys to the internal checkpoint key used by find_ltx_model
        ltx_key = "ltxv_checkpoint" if "2B" in key else "checkpoint"
        path = find_ltx_model(ltx_key)
        inventory.append({
            "key": key,
            "type": "video",
            "repo_id": repo_id,
            "status": "downloaded" if path else "missing",
            "path": str(path) if path else None
        })
        
    return inventory
