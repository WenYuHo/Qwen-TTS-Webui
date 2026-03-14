import os
import sys
import subprocess
from pathlib import Path
import re
from datetime import datetime

def finish_task():
    print("🚀 FINISHING TASK...")
    print("-" * 40)

    # 1. RUN PRE-COMMIT
    print("📦 1/3: Running pre-commit checks...")
    try:
        subprocess.run(["python", "tools/pre_commit.py"], check=True)
        print("✅ Pre-commit checks passed!")
    except subprocess.CalledProcessError:
        print("❌ FAILED: Pre-commit checks failed. Fix and try again.")
        return False

    # 2. UPDATE TASK QUEUE
    task_name = "Unknown"
    print("📂 2/3: Updating TASK_QUEUE.md...")
    task_file = Path("agent/TASK_QUEUE.md")
    if task_file.exists():
        content = task_file.read_text(encoding="utf-8")
        
        # Find the first in-progress task
        match = re.search(r"(- \[ \] \*\*(.*?)\*\*\n(?:    - .*?\n)*?    - Reserved: )IN_PROGRESS @ .*?\n", content)
        if match:
            full_match = match.group(0)
            task_name = match.group(2)
            timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            
            # Replace [ ] with [x] and update Reserved/Updated fields
            new_block = f"- [x] **{task_name}**\n    - Task: (Completed)\n    - Updated: {timestamp}\n"
            new_content = content.replace(full_match, new_block, 1)
            
            # Append to COMPLETED section
            new_content += f"- [x] **{task_name}** ({timestamp[:10]})\n"
            
            task_file.write_text(new_content, encoding="utf-8")
            print(f"✅ Marked **{task_name}** as complete.")
        else:
            print("⚠️  Warning: No task was found with 'IN_PROGRESS' status.")

    # 3. UPDATE EVOLUTION LOG
    print("🧠 3/3: Updating agent/EVOLUTION.md...")
    evo_file = Path("agent/EVOLUTION.md")
    if evo_file.exists():
        timestamp = datetime.utcnow().strftime("%Y-%m-%d")
        evo_content = evo_file.read_text(encoding="utf-8")
        evo_file.write_text(
            evo_content + f"| {timestamp} | {task_name} | — | COMPLETED | Finished via `tools/finish.py`. |\n",
            encoding="utf-8"
        )
        print("✅ EVOLUTION.md updated.")

    # 4. AUTOMATED REFLECTION
    print("\n🧐 4/5: Running Automated Reflection...")
    subprocess.run(["python", "tools/reflect.py", f"Successfully completed {task_name} and verified system health."])

    # 5. AUTOMATED SYNC
    print("\n☁️  5/5: Synchronizing to Repository...")
    subprocess.run(["python", "tools/git_ops.py", task_name.lower().replace(" ", "-"), "commit", f"Task Completed: {task_name}"], check=False)

    print("-" * 40)
    print("🎉 TASK FINISHED & SYNCED!")
    print()
    print("🔄 SELF-IMPROVE (L0 DNA):")
    return True

if __name__ == "__main__":
    if finish_task():
        sys.exit(0)
    else:
        sys.exit(1)
