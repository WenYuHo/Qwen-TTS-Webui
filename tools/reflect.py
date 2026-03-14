import os
import sys
from pathlib import Path
from datetime import datetime

def reflect():
    """
    Automated reflection tool.
    In this 2026 DNA v3 version, the agent (me) runs this to consolidate 
    the current session's findings into the long-term memory.
    """
    lessons_file = Path("agent/LESSONS.md")
    task_file = Path("agent/TASK_QUEUE.md")
    
    if not lessons_file.exists():
        lessons_file.write_text("# Agent Lessons Learned\n\n| Date | Lesson |\n|:---|:---|\n", encoding="utf-8")

    # In a real autonomy loop, this would call an LLM to summarize. 
    # For now, we provide a CLI interface for the agent to log a lesson quickly.
    if len(sys.argv) > 1:
        lesson = " ".join(sys.argv[1:])
    else:
        # Fallback: try to guess from the last completed task
        lesson = "Completed recent task. (Automated reflection pending LLM summary)"

    timestamp = datetime.utcnow().strftime("%Y-%m-%d")
    with open(lessons_file, "a", encoding="utf-8") as f:
        f.write(f"| {timestamp} | {lesson} |\n")
    
    print(f"🧠 Reflection logged: {lesson}")

if __name__ == "__main__":
    reflect()
