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

def launch_agent(name, mission, color="0A"):
    # We add a specific instruction about the GPU Lock to the prompt
    gpu_instruction = (
        "\\n\\n**GPU SAFETY**: Your 2070 Super has 8GB VRAM. "
        "Before running ANY ML models or tests, check if 'agent/GPU.lock' exists. "
        "If yes, WAIT. If no, create it with your name, run your task, then DELETE it immediately."
    )
    
    full_mission = mission + gpu_instruction
    
    cmd = f'start cmd /k "title SYMPHONY-{name} && color {color} && cd {name} && gemini \\"/ralph:loop \\"{full_mission}\\" --max-iterations 20 --completion-promise MISSION_COMPLETE\\""'
    subprocess.run(cmd, shell=True)

if __name__ == "__main__":
    print("--- 🎼 SYMPHONY v2 (8GB VRAM OPTIMIZED) ---")
    
    # 1. Clean up stale locks
    if os.path.exists("agent/GPU.lock"):
        os.remove("agent/GPU.lock")
        print("🔓 Cleared stale GPU lock.")

    # 2. Setup Worktrees & Junctions
    setup_worktree("worker-1")
    setup_worktree("worker-2")
    
    # 3. Launch Manager (Orchestrator)
    # Manager doesn't use the GPU, so it can run freely
    print("🚀 Launching Manager (Blue)...")
    launch_agent(".", "Manager Mode: You are the TPM. Assign tasks from agent/TASK_QUEUE.md to worker-1 or worker-2 by editing the file. Monitor their progress. Merge branches when done. Keep agent/SYMPHONY_LIVE.md updated with status.", "0B")
    
    time.sleep(3)
    
    # 4. Launch Workers
    print("🚀 Launching Worker 1 (Green)...")
    launch_agent("worker-1", "Worker-1: Look for tasks assigned to you in agent/TASK_QUEUE.md. Execute them one by one. Use the GPU Token protocol.", "0A")
    
    time.sleep(3)
    
    print("🚀 Launching Worker 2 (Yellow)...")
    launch_agent("worker-2", "Worker-2: Look for tasks assigned to you in agent/TASK_QUEUE.md. Execute them one by one. Use the GPU Token protocol.", "0E")

    print("\n✅ Symphony is running. Check 'agent/SYMPHONY_LIVE.md' for the dashboard.")
