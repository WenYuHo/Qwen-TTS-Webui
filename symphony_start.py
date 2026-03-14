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
        print(f"🔗 Linking {folder_name} to {target_dir}...")
        # /J creates a directory junction on Windows
        subprocess.run(f'mklink /J "{target_folder}" "{root_folder}"', shell=True)

def setup_worktree(name):
    if not os.path.exists(name):
        print(f"📂 Creating worktree: {name}...")
        subprocess.run(f"git worktree add {name} -b symphony-{name}", shell=True)
    
    # Share the environments to save RAM/Disk
    setup_junction(name, ".venv")
    setup_junction(name, "node_modules")
    setup_junction(name, "models") # Crucial for 2070 Super: share the heavy model files

def launch_agent(name, mission, color="0A", headless=False):
    # Avoid quotes and newlines in the mission string
    safe_mission = mission.replace('"', "'").replace("\n", " ").strip()
    gpu_instruction = " [GPU SAFETY: Check agent/GPU.lock before use]"
    full_mission = safe_mission + gpu_instruction
    
    # We use -p (non-interactive) in headless mode to force the CLI to run the command and exit
    if headless:
        print(f"🕵️  Launching {name} in background (headless)...")
        # CREATE_NO_WINDOW = 0x08000000
        cmd = f'gemini --prompt "/ralph:loop \\"{full_mission}\\"" --yolo'
        subprocess.Popen(cmd, shell=True, cwd=name, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=0x08000000)
    else:
        # Standard mode: Open interactive windows
        # Note: We must ensure the command is executed, so we prefix with /c if using cmd
        cmd = f'start "SYMPHONY-{name}" cmd /k "color {color} && cd {name} && gemini --prompt \\"/ralph:loop \\"{full_mission}\\"\\" --yolo"'
        subprocess.run(cmd, shell=True)

if __name__ == "__main__":
    print("--- 🎼 SYMPHONY v2 (8GB VRAM OPTIMIZED) ---")
    headless = "--headless" in sys.argv
    
    # 0. Automate Session Re-hydration (Fast Boot)
    print("🧬 Re-hydrating context...")
    subprocess.run(["python", "tools/session_start.py", "--skip-verify"], check=False)
    
    # 1. Clean up stale locks
    if os.path.exists("agent/GPU.lock"):
        os.remove("agent/GPU.lock")
        print("🔓 Cleared stale GPU lock.")

    # 2. Setup Worktrees & Junctions
    setup_worktree("worker-1")
    setup_worktree("worker-2")
    
    # 3. Launch Manager (Orchestrator)
    print(f"🚀 Launching Manager {'(Headless)' if headless else '(Blue)'}...")
    launch_agent(".", "Manager Mode: You are the TPM. Assign tasks from agent/TASK_QUEUE.md to worker-1 or worker-2 by editing the file. Monitor their progress. Merge branches when done. Keep agent/SYMPHONY_LIVE.md updated with status.", "0B", headless=headless)
    
    time.sleep(3)
    
    # 4. Launch Workers
    print(f"🚀 Launching Worker 1 {'(Headless)' if headless else '(Green)'}...")
    launch_agent("worker-1", "Worker-1: Look for tasks assigned to you in agent/TASK_QUEUE.md. Execute them one by one. Use the GPU Token protocol.", "0A", headless=headless)
    
    time.sleep(3)
    
    print(f"🚀 Launching Worker 2 {'(Headless)' if headless else '(Yellow)'}...")
    launch_agent("worker-2", "Worker-2: Look for tasks assigned to you in agent/TASK_QUEUE.md. Execute them one by one. Use the GPU Token protocol.", "0E", headless=headless)

    print(f"\n✅ Symphony is running {'in headless mode' if headless else ''}. Check 'agent/SYMPHONY_LIVE.md' for the dashboard.")
