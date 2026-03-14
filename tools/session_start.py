import os
import sys
import subprocess
from pathlib import Path
import re

# Fix Windows cp1252 encoding for emoji output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def get_git_status():
    try:
        res = subprocess.run(["git", "status", "--short"], capture_output=True, text=True)
        return res.stdout.strip() or "Clean"
    except:
        return "Unknown"

def get_last_lessons(n=3):
    """Show last N lessons from LESSONS.md so agents learn from recent mistakes."""
    lessons_file = Path("agent/LESSONS.md")
    if not lessons_file.exists():
        return "No lessons logged yet."
    
    content = lessons_file.read_text(encoding="utf-8")
    # Match table rows: | date | lesson |
    rows = re.findall(r"\| (\d{4}-\d{2}-\d{2}) \| (.+?) \|", content)
    if not rows:
        return "No lessons logged yet."
    
    summary = []
    for date, lesson in rows[-n:]:
        summary.append(f"  - [{date}] {lesson.strip()}")
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

def get_context_layer_sizes():
    """Show context layer files with sizes to help agents budget."""
    layers = [
        ("L0: Identity", "agent/MEMORY.md"),
        ("L1: Task", "agent/TASK_QUEUE.md"),
        ("L2: Skills", "skills/"),
        ("L3: Tracks", "conductor/"),
        ("L4: History", "agent/DECISIONS.md"),
    ]
    lines = []
    for label, path in layers:
        p = Path(path)
        if p.is_file():
            size = p.stat().st_size
            lines.append(f"  {label:20s} {path:30s} ({size:,} bytes)")
        elif p.is_dir():
            total = sum(f.stat().st_size for f in p.rglob("*.md"))
            lines.append(f"  {label:20s} {path:30s} ({total:,} bytes total)")
        else:
            lines.append(f"  {label:20s} {path:30s} (not found)")
    return "\n".join(lines)

def main():
    print("🧬 SESSION RE-HYDRATION SNAPSHOT")
    print("-" * 40)
    
    # 1. Verify Environment
    print("🛠️  Verifying Environment...")
    try:
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        subprocess.run(["python", "verify_setup.py"], check=True, env=env)
        print("✅ Environment Healthy")
    except subprocess.CalledProcessError:
        print("❌ Environment Verification Failed! Fix before proceeding.")
        return

    print("-" * 40)
    print(f"📍 BRANCH: {subprocess.run(['git', 'branch', '--show-current'], capture_output=True, text=True).stdout.strip()}")
    print(f"📝 GIT STATUS: {get_git_status()}")
    print(f"🎯 ACTIVE TASK: {get_active_task()}")
    
    print("\n🧠 CONTEXT LAYERS (load on-demand only):")
    print(get_context_layer_sizes())
    
    print("\n📚 RECENT LESSONS:")
    print(get_last_lessons())
    
    print("-" * 40)
    print("⚡ TOKEN RULE: L0 is pre-loaded. Load L1-L4 on-demand only.")
    print("🚀 Ready to proceed. Read agent/MEMORY.md (L0), then reserve a task.")

if __name__ == "__main__":
    main()
