import unittest
import time
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from backend.task_manager import TaskManager, TaskStatus

class TestTaskManager(unittest.TestCase):
    def setUp(self):
        self.tm = TaskManager()

    def test_create_and_get_task(self):
        tid = self.tm.create_task("test", {"meta": "data"})
        task = self.tm.get_task(tid)
        self.assertIsNotNone(task)
        self.assertEqual(task["status"], TaskStatus.PENDING)
        self.assertEqual(task["metadata"]["meta"], "data")

    def test_update_task(self):
        tid = self.tm.create_task("test")
        self.tm.update_task(tid, status=TaskStatus.PROCESSING, progress=50, message="Halfway")
        
        task = self.tm.get_task(tid)
        self.assertEqual(task["status"], TaskStatus.PROCESSING)
        self.assertEqual(task["progress"], 50)
        self.assertEqual(task["message"], "Halfway")

    def test_cleanup_tasks(self):
        tid = self.tm.create_task("old")
        # Manually backdate the created_at for testing cleanup
        self.tm.tasks[tid]["created_at"] = time.time() - 5000
        
        self.tm.cleanup_old_tasks(max_age_seconds=3600)
        self.assertIsNone(self.tm.get_task(tid))

if __name__ == "__main__":
    unittest.main()
