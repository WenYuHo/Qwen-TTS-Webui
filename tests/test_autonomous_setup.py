import os
from pathlib import Path

def test_autonomous_files_exist():
    """Verify that all core files for the Autonomous Improvement System are present."""
    base_dir = Path(__file__).resolve().parent.parent
    
    # Required files
    required_files = [
        ".jules/improver.md",
        "agent/MEMORY.md",
        "agent/TASK_QUEUE.md",
        "agent/IMPROVEMENT_LOG.md",
        ".github/workflows/autonomous-improvement.yml"
    ]
    
    for rel_path in required_files:
        full_path = base_dir / rel_path
        assert full_path.exists(), f"Missing required autonomous file: {rel_path}"

def test_task_queue_structure():
    """Verify that the TASK_QUEUE.md has the expected structure."""
    base_dir = Path(__file__).resolve().parent.parent
    tq_path = base_dir / "agent/TASK_QUEUE.md"
    
    if not tq_path.exists():
        return # Handled by test_autonomous_files_exist
        
    content = tq_path.read_text(encoding="utf-8")
    assert "# TASK QUEUE" in content
    assert "## PRIORITIZED BACKLOG" in content
    assert "## COMPLETED" in content
