import uuid
import threading
import time
from typing import Dict, Any, Optional, List
from .config import logger

class TaskStatus:
    """Constants representing the lifecycle states of an asynchronous task."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskManager:
    """
    A thread-safe manager for tracking and controlling asynchronous background tasks.
    
    This class maintains a registry of tasks, their progress, and associated execution threads.
    It provides mechanisms for task creation, status updates, cancellation via threading events,
    and automatic cleanup of stale task data.
    """
    def __init__(self):
        """Initialize the TaskManager with empty registries and a thread lock."""
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.threads: Dict[str, threading.Thread] = {}
        self.stop_events: Dict[str, threading.Event] = {}
        self.lock = threading.Lock()

    def create_task(self, task_type: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Initialize a new task record in the registry.

        Args:
            task_type: A string identifier for the category of task (e.g., 'synthesis', 'download').
            metadata: Optional dictionary of context-specific data for the task.

        Returns:
            A unique UUID string identifying the created task.
        """
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
        """
        Associate a task ID with the OS thread executing the workload.

        Args:
            task_id: The ID of the task to register.
            thread: The threading.Thread instance running the task.
        """
        with self.lock:
            self.threads[task_id] = thread

    def get_stop_event(self, task_id: str) -> Optional[threading.Event]:
        """
        Retrieve the cancellation event associated with a specific task.

        Tasks should periodically check this event (e.g., `event.is_set()`) to support 
        graceful termination.
        """
        with self.lock:
            return self.stop_events.get(task_id)

    def is_cancelled(self, task_id: str) -> bool:
        """
        Check if the specified task has been marked for cancellation.

        Returns:
            True if the task exists and its stop event is set, False otherwise.
        """
        event = self.get_stop_event(task_id)
        return event.is_set() if event else False

    def cancel_task(self, task_id: str) -> bool:
        """
        Signals a task to stop and marks its status as CANCELLED.

        This method sets the internal stop event. It is up to the task's execution 
        logic to observe this signal and exit.

        Args:
            task_id: The ID of the task to cancel.

        Returns:
            True if the task was successfully cancelled, False if it was already 
            finished or not found.
        """
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
        """
        Atomically update the state and metadata of a registered task.

        Args:
            task_id: The ID of the task to update.
            status: New lifecycle state from TaskStatus.
            progress: Integer percentage (0-100).
            message: Human-readable description of current progress.
            result: The final output data (only set on completion).
            error: Descriptive error message if the task fails.
        """
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
        """
        Return a list of all tasks in the registry.
        
        Note: The 'result' field is excluded from this list to keep responses lightweight.
        """
        with self.lock:
            return [ {k: v for k, v in t.items() if k != "result"} for t in self.tasks.values() ]

    def cleanup_old_tasks(self, max_age_seconds: int = 3600):
        """
        Prune task records, threads, and events that exceed the maximum age.

        Args:
            max_age_seconds: Maximum age in seconds since task creation.
        """
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
