import uuid
import threading
import time
from typing import Dict, Any, Optional, List
from .config import logger

class TaskStatus:
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskManager:
    def __init__(self):
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.threads: Dict[str, threading.Thread] = {}
        self.stop_events: Dict[str, threading.Event] = {}
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
            self.stop_events[task_id] = threading.Event()
        logger.info(f"Task created: {task_id} ({task_type})")
        return task_id

    def register_thread(self, task_id: str, thread: threading.Thread):
        """Register the thread running the task."""
        with self.lock:
            self.threads[task_id] = thread

    def get_stop_event(self, task_id: str) -> Optional[threading.Event]:
        """Get the stop event for a task."""
        with self.lock:
            return self.stop_events.get(task_id)

    def is_cancelled(self, task_id: str) -> bool:
        """Check if a task has been cancelled."""
        event = self.get_stop_event(task_id)
        return event.is_set() if event else False

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task."""
        with self.lock:
            if task_id not in self.tasks:
                return False

            task = self.tasks[task_id]
            if task["status"] in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                return False

            task["status"] = TaskStatus.CANCELLED
            task["message"] = "Task cancelled by user"
            task["updated_at"] = time.time()

            if task_id in self.stop_events:
                self.stop_events[task_id].set()

            logger.info(f"Task cancelled: {task_id}")
            return True

    def update_task(self, task_id: str, status: Optional[str] = None, progress: Optional[int] = None, 
                    message: Optional[str] = None, result: Any = None, error: Optional[str] = None):
        """Update task status and metadata."""
        with self.lock:
            if task_id not in self.tasks:
                logger.error(f"Attempted to update non-existent task: {task_id}")
                return

            task = self.tasks[task_id]

            # Don't update if already cancelled
            if task["status"] == TaskStatus.CANCELLED:
                return

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

    def list_tasks(self) -> List[Dict[str, Any]]:
        """List all tasks."""
        with self.lock:
            return [ {k: v for k, v in t.items() if k != "result"} for t in self.tasks.values() ]

    def cleanup_old_tasks(self, max_age_seconds: int = 3600):
        """Remove tasks older than max_age_seconds."""
        now = time.time()
        with self.lock:
            to_delete = [tid for tid, t in self.tasks.items() if now - t["created_at"] > max_age_seconds]
            for tid in to_delete:
                del self.tasks[tid]
                self.threads.pop(tid, None)
                self.stop_events.pop(tid, None)
        if to_delete:
            logger.info(f"Cleaned up {len(to_delete)} old tasks")

# Global instance
task_manager = TaskManager()
