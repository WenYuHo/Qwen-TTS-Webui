import uuid
import threading
import time
from typing import Dict, Any, Optional
from .config import logger

class TaskStatus:
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskManager:
    def __init__(self):
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()

    def create_task(self, task_type: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create a new task and return its ID."""
        task_id = str(uuid.uuid4())
        with self.lock:
            self.tasks[task_id] = {
                "id": task_id,
                "type": task_type,
                "status": TaskStatus.PENDING,
                "progress": 0,
                "message": "Task queued",
                "result": None,
                "error": None,
                "created_at": time.time(),
                "updated_at": time.time(),
                "metadata": metadata or {}
            }
        logger.info(f"Task created: {task_id} ({task_type})")
        return task_id

    def update_task(self, task_id: str, status: Optional[str] = None, progress: Optional[int] = None, 
                    message: Optional[str] = None, result: Any = None, error: Optional[str] = None):
        """Update task status and metadata."""
        with self.lock:
            if task_id not in self.tasks:
                logger.error(f"Attempted to update non-existent task: {task_id}")
                return

            task = self.tasks[task_id]
            if status:
                task["status"] = status
            if progress is not None:
                task["progress"] = progress
            if message:
                task["message"] = message
            if result is not None:
                task["result"] = result
            if error:
                task["error"] = error
            
            task["updated_at"] = time.time()
        
        logger.debug(f"Task updated: {task_id} - {status} ({progress}%)")

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve task information."""
        with self.lock:
            return self.tasks.get(task_id)

    def cleanup_old_tasks(self, max_age_seconds: int = 3600):
        """Remove tasks older than max_age_seconds."""
        now = time.time()
        with self.lock:
            to_delete = [tid for tid, t in self.tasks.items() if now - t["created_at"] > max_age_seconds]
            for tid in to_delete:
                del self.tasks[tid]
        if to_delete:
            logger.info(f"Cleaned up {len(to_delete)} old tasks")

# Global instance
task_manager = TaskManager()
