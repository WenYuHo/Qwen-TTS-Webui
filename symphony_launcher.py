import sys
import os
import subprocess

def launch_agent():
    if len(sys.argv) < 2:
        print("Usage: python symphony_launcher.py <AgentName>")
        sys.exit(1)
        
    agent_name = sys.argv[1]
    mission_file = f"agent/{agent_name}_mission.txt"
    
    # Read the mission file written by symphony_start.py
    if not os.path.exists(mission_file):
        print(f"Error: Mission file {mission_file} not found.")
        sys.exit(1)
        
    with open(mission_file, "r", encoding="utf-8") as f:
        mission_text = f.read()

    # The prompt consists of the ralph loop invocation wrapping the mission payload
    prompt = f"/ralph:loop \"{mission_text}\" --max-iterations 20 --completion-promise MISSION_COMPLETE"
    
    print(f"[{agent_name}] Launcher initialized. Spawning gemini swarm node...")
    
    # Execute gemini CLI directly via subprocess list.
    # --yolo is required to ensure agents do not block on 'y/n' execution confirmation prompts 
    cmd = ["gemini", "--yolo", prompt]
    
    # Passing the list prevents Windows CMD entirely from trying to parse quotes and operators.
    subprocess.run(cmd)

if __name__ == "__main__":
    launch_agent()
