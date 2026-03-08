import sys
from pathlib import Path
import re
from datetime import datetime

def reserve_task():
    task_file = Path("agent/TASK_QUEUE.md")
    if not task_file.exists():
        print("❌ Error: agent/TASK_QUEUE.md not found.")
        return False

    content = task_file.read_text(encoding="utf-8")
    
    # Look for the first unreserved task block
    # Pattern: - [ ] **TASK_NAME** followed by Reserved: NONE
    task_pattern = r"(- \[ \] \*\*(.*?)\*\*\n(?:    - .*?\n)*?    - Reserved: )NONE"
    
    match = re.search(task_pattern, content)
    if not match:
        print("✅ No unreserved tasks found in backlog.")
        return False

    full_match = match.group(0)
    task_name = match.group(2)
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    reservation = f"IN_PROGRESS @ {timestamp}"
    
    new_content = content.replace(full_match, match.group(1) + reservation, 1)
    task_file.write_text(new_content, encoding="utf-8")
    
    print(f"🎯 RESERVED: **{task_name}**")
    print(f"⏰ TIMESTAMP: {timestamp}")
    print(f"📂 Status updated in agent/TASK_QUEUE.md")
    return True

if __name__ == "__main__":
    if reserve_task():
        sys.exit(0)
    else:
        sys.exit(1)
