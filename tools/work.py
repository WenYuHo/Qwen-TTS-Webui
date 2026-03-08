import os
import subprocess
import re
from pathlib import Path

def get_next_task():
    task_file = Path("agent/TASK_QUEUE.md")
    if not task_file.exists():
        return None
    
    content = task_file.read_text(encoding="utf-8")
    # Find the first line that looks like "- [ ] **Task Name** — Description"
    match = re.search(r"- \[ \] \*\*(.*?)\*\*(.*)", content)
    if match:
        task_name = match.group(1).strip()
        description = match.group(2).strip(" —")
        return f"{task_name}: {description}"
    return None

def main():
    task = get_next_task()
    if not task:
        print("✅ No pending tasks found in agent/TASK_QUEUE.md!")
        return

    print(f"🚀 Found next task: {task}")
    
    # Find gemini command in PATH
    import shutil
    gemini_cmd = shutil.which("gemini") or shutil.which("gemini.cmd")
    
    if not gemini_cmd:
        print("❌ ERROR: 'gemini' command not found in PATH.")
        print("Please ensure @google/gemini-cli is installed (npm install -g @google/gemini-cli)")
        return

    # Construct the Ralph command with hybrid-agent instructions
    # Security: Use a list of arguments instead of a shell string
    command = [
        gemini_cmd, "-y", 
        f"/ralph:loop \"{task}. Protocol: 1. Create unique feature branch. 2. Code/Test locally. 3. Push and open PR. 4. Poll PR status until merged. Use TASK_DONE as the promise only when the PR is merged into main. Follow agent/MEMORY.md.\" --completion-promise \"TASK_DONE\""
    ]
    
    print(f"🛠️  Launching Ralph Loop...")
    print(f"📝 Command: {' '.join(command)}")
    
    try:
        # Security: shell=False is default and safer
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Loop failed with exit code {e.returncode}")
    except KeyboardInterrupt:
        print("\n🛑 Loop interrupted by user.")

if __name__ == "__main__":
    main()
