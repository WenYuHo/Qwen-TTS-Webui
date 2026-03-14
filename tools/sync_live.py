import sys
import os
import re
from pathlib import Path
from datetime import datetime

def update_live_board(agent_name, status, task="Waiting...", progress="0%"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    live_file = Path("agent/SYMPHONY_LIVE.md")
    if not live_file.exists():
        # Initialize with skeleton if missing
        pass # Handle below if needed

    content = live_file.read_text(encoding="utf-8")

    # Update Status Section with Heartbeat
    status_pattern = rf"- \*\*{agent_name}:\*\* (.*)"
    new_status_line = f"- **{agent_name}:** {status} (HB: {timestamp})"
    
    if re.search(status_pattern, content):
        content = re.sub(status_pattern, new_status_line, content)
    else:
        # If the agent isn't in the list yet, we'd need to add it, 
        # but for simplicity assume the file is pre-populated as per current design.
        pass

    # Update Dispatch Table for Workers
    if "Worker" in agent_name:
        table_pattern = rf"\| {agent_name} \| (.*?) \| (.*?) \|"
        new_table_row = f"| {agent_name} | {task} | {progress} |"
        content = re.sub(table_pattern, new_table_row, content)

    live_file.write_text(content, encoding="utf-8")
    print(f"📊 Updated SYMPHONY_LIVE.md: {agent_name} -> {status} (HB: {timestamp})")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python tools/sync_live.py <agent_name> <status> [task] [progress]")
        sys.exit(1)

    name = sys.argv[1]
    stat = sys.argv[2]
    tsk = sys.argv[3] if len(sys.argv) > 3 else "Waiting..."
    prog = sys.argv[4] if len(sys.argv) > 4 else "0%"

    update_live_board(name, stat, tsk, prog)
