import os
import subprocess
import time
import sys

def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)

def setup_junction(target_dir, folder_name):
    """Creates a Windows Junction to share the environment."""
    root_folder = os.path.join(os.getcwd(), folder_name)
    target_folder = os.path.join(target_dir, folder_name)
    
    if os.path.exists(root_folder) and not os.path.exists(target_folder):
        print(f"Linking {folder_name} to {target_dir}...")
        subprocess.run(['cmd', '/c', 'mklink', '/J', target_folder, root_folder])

def setup_worktree(name):
    if not os.path.exists(name):
        print(f"Creating worktree: {name}...")
        subprocess.run(['git', 'worktree', 'add', name, '-b', f"symphony-{name}"])
    
    setup_junction(name, ".venv")
    setup_junction(name, "node_modules")
    setup_junction(name, "models")

def launch_agent(name, mission, color="0A", target_dir="."):
    if name.lower() == "manager":
        readable_name = "SYMPHONY MANAGER (Lead Orchestrator)"
        warning_msg = "DO NOT CLOSE UNLESS STOPPING ENTIRE SWARM"
    else:
        readable_name = f"SYMPHONY {name.upper()} (Task Executor)"
        warning_msg = "SAFE TO CLOSE IF NOT NEEDED"

    skill_mandate = (
        "\\n\\n**SKILL ACTIVATION**: You are AUTHORIZED and ENCOURAGED to use the project's internal skills. "
        "Read `skills/skills.md` at the start of every task. "
        "- For testing/TDD: Use `skills/tester/SKILL.md`. "
        "- For architectural changes: Use `skills/architect/SKILL.md`. "
        "- For context pruning/memory cleanup: Use `skills/dna-evolution/SKILL.md`. "
        "Loading skills on-demand is MANDATORY to prevent context overloading."
    )
    
    meta_mandate = (
        "\\n\\n**META-REFLECTION**: You are part of an evolving swarm. "
        "1. If you (the Manager) see Workers struggling, you MUST rewrite your own 'Manager Mode' instructions in `symphony_start.py` to be clearer. "
        "2. If you (the Worker) are confused, write `[?] CLARIFICATION_NEEDED` in TASK_QUEUE.md immediately."
    )
    
    gpu_instruction = (
        "\\n\\n**GPU SAFETY**: Your 2070 Super has 8GB VRAM. Use the GPU Token protocol in 'agent/GPU.lock'."
    )

    live_board_protocol = (
        "\\n\\n**LIVE BOARD PROTOCOL**: You MUST update your status in `agent/SYMPHONY_LIVE.md` at the start and end of every task phase using: "
        f"`python tools/sync_live.py \"{name}\" \"[STATUS]\" \"[TASK_NAME]\" \"[PROGRESS%]\"`."
    )
    
    full_mission = mission + skill_mandate + meta_mandate + gpu_instruction + live_board_protocol
    
    title = f"{readable_name} -- [{warning_msg}]"
    header_cmd = f"echo ===================================================== && echo {title} && echo ====================================================="
    
    mission_file = os.path.join(target_dir, "agent", f"{name}_mission.txt")
    os.makedirs(os.path.dirname(mission_file), exist_ok=True)
    with open(mission_file, "w", encoding="utf-8") as f:
        f.write(full_mission)
        
    launcher_path = "symphony_launcher.py" if target_dir == "." else f"..\\symphony_launcher.py"
    cmd_list = [
        'cmd', '/c', 'start', title, 'cmd', '/k',
        f"{header_cmd} && title {title} && color {color} && cd {target_dir} && python {launcher_path} {name}"
    ]
    subprocess.run(cmd_list)

if __name__ == "__main__":
    print("--- SYMPHONY v5 (LIVE-BOARD & SKILL-BASED) ---")
    
    if os.path.exists("agent/GPU.lock"):
        os.remove("agent/GPU.lock")
        print("Cleared stale GPU lock.")

    setup_worktree("worker-1")
    setup_worktree("worker-2")
    
    print("Launching Manager (Blue)...")
    manager_mission = (
        "Manager Mode: Lead Orchestrator & TPM. "
        "1. Monitor `agent/TASK_QUEUE.md`. "
        "2. **CRITICAL**: Check `agent/SYMPHONY_LIVE.md` for Heartbeat (HB) timestamps. "
        "If a Worker's HB is >15 mins old, they are likely STUCK. NOTIFY THE USER immediately. "
        "3. Use `dna-evolution` skill to prune `MEMORY.md` if it exceeds 40 lines. "
        "4. **REVIEW GATE**: Before approving ANY Worker task, `git diff` their branch and check against "
        "`agent/MEMORY.md` coding standards and negative constraints. Reject with specific feedback if violations found. "
        "5. After each task cycle, append a 1-line lesson to `agent/LESSONS.md`."
    )
    launch_agent("Manager", manager_mission, "0B", ".")
    
    time.sleep(3)
    
    worker_mission = (
        "Worker Mode: Execute tasks from `agent/TASK_QUEUE.md`. "
        "1. Load the relevant SKILL.md before starting each task phase. "
        "2. Follow `agent/MEMORY.md` coding standards and negative constraints strictly. "
        "3. **CONTEXT COMPACTION**: If context feels >50%% full, write a SCRATCHPAD.md summary and drop raw files. "
        "4. After each task, append a 1-line lesson to `agent/LESSONS.md`. "
        "5. Focus on TDD and clean architecture."
    )
    
    print("Launching Worker 1 (Green)...")
    launch_agent("Worker-1", f"Worker-1: {worker_mission}", "0A", "worker-1")
    
    time.sleep(3)
    
    print("Launching Worker 2 (Yellow)...")
    launch_agent("Worker-2", f"Worker-2: {worker_mission}", "0E", "worker-2")

    print("\nSymphony is running. Agents are now using modular skills to save tokens.")
