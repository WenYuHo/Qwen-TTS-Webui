import pytest
import time
from src.backend.task_manager import TaskManager, TaskStatus

def test_task_creation_and_listing():
    tm = TaskManager()
    tid = tm.create_task("test_task", {"meta": "data"})

    task = tm.get_task(tid)
    assert task["id"] == tid
    assert task["type"] == "test_task"
    assert task["status"] == TaskStatus.PENDING

    tasks = tm.list_tasks()
    assert len(tasks) == 1
    assert tasks[0]["id"] == tid

def test_task_cancellation():
    tm = TaskManager()
    tid = tm.create_task("cancellable_task")

    tm.update_task(tid, status=TaskStatus.PROCESSING, progress=50)
    assert tm.get_task(tid)["status"] == TaskStatus.PROCESSING

    success = tm.cancel_task(tid)
    assert success is True
    assert tm.get_task(tid)["status"] == TaskStatus.CANCELLED
    assert tm.is_cancelled(tid) is True

    # Subsequent updates should be ignored
    tm.update_task(tid, status=TaskStatus.COMPLETED)
    assert tm.get_task(tid)["status"] == TaskStatus.CANCELLED

def test_cleanup():
    tm = TaskManager()
    tid = tm.create_task("old_task")
    tm.tasks[tid]["created_at"] = time.time() - 4000

    tm.cleanup_old_tasks(max_age_seconds=3600)
    assert tm.get_task(tid) is None
    assert len(tm.list_tasks()) == 0
