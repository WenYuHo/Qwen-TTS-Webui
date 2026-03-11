import os
import subprocess
from pathlib import Path
import re
import sys

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

def get_git_status():
    try:
        res = subprocess.run(["git", "status", "--short"], capture_output=True, text=True)
        return res.stdout.strip() or "Clean"
    except:
        return "Unknown"

def get_last_decisions(n=3):
    decision_file = Path("agent/DECISIONS_LOG.md")
    if not decision_file.exists():
        return "No decisions logged."
    
    content = decision_file.read_text(encoding="utf-8")
    # Matches markdown headers like "### 2026-03-08: ..."
    entries = re.findall(r"### (.*?)\n(.*?)(?=\n### |\Z)", content, re.DOTALL)
    
    summary = []
    for date, body in entries[-n:]:
        first_line = body.strip().split('\n')[0]
        summary.append(f"- {date}: {first_line}")
    return "\n".join(summary)

def get_active_task():
    task_file = Path("agent/TASK_QUEUE.md")
    if not task_file.exists():
        return "No task queue found."
    
    content = task_file.read_text(encoding="utf-8")
    # Find the first pending task
    match = re.search(r"- \[ \] \*\*(.*?)\*\*(.*)", content)
    if match:
        return f"{match.group(1).strip()}: {match.group(2).strip(' —')}"
    return "No active tasks."

def main():
    print("🧬 SESSION RE-HYDRATION SNAPSHOT")
    print("-" * 30)
    
    # 1. Verify Environment
    print("🛠️  Verifying Environment...")
    try:
        subprocess.run(["python", "verify_setup.py"], check=True)
        print("✅ Environment Healthy")
    except subprocess.CalledProcessError:
        print("❌ Environment Verification Failed! Fix before proceeding.")
        return

    print("-" * 30)
    print(f"📍 BRANCH: {subprocess.run(['git', 'branch', '--show-current'], capture_output=True, text=True).stdout.strip()}")
    print(f"📝 GIT STATUS: {get_git_status()}")
    print(f"🎯 ACTIVE TASK: {get_active_task()}")
    print("\n🧠 RECENT DECISIONS:")
    print(get_last_decisions())
    print("-" * 30)
    print("🚀 Ready to proceed. Follow agent/MEMORY.md.")

if __name__ == "__main__":
    main()
