import pytest
import time
import sys
from pathlib import Path

# Add src to path
src_path = str(Path(__file__).resolve().parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from backend.task_manager import TaskManager, TaskStatus

@pytest.fixture
def task_manager():
    """Provides a fresh TaskManager instance for each test."""
    return TaskManager()

def test_create_and_get_task(task_manager):
    tid = task_manager.create_task("test", {"meta": "data"})
    task = task_manager.get_task(tid)
    assert task is not None
    assert task["status"] == TaskStatus.PENDING
    assert task["metadata"]["meta"] == "data"

def test_update_task(task_manager):
    tid = task_manager.create_task("test")
    task_manager.update_task(tid, status=TaskStatus.PROCESSING, progress=50, message="Halfway")
    
    task = task_manager.get_task(tid)
    assert task["status"] == TaskStatus.PROCESSING
    assert task["progress"] == 50
    assert task["message"] == "Halfway"

def test_cleanup_tasks(task_manager):
    tid = task_manager.create_task("old")
    # Manually backdate the created_at for testing cleanup
    task_manager.tasks[tid]["created_at"] = time.time() - 5000
    
    task_manager.cleanup_old_tasks(max_age_seconds=3600)
    assert task_manager.get_task(tid) is None
