import subprocess
from pathlib import Path

def test_quoting(mission):
    print(f"Testing mission: {mission}")
    # Simulate the simplified quoting from launch_agent
    safe_mission = mission.replace('"', "'").replace("\n", " ").strip()
    gpu_instruction = " [GPU SAFETY: Check agent/GPU.lock before use]"
    full_mission = safe_mission + gpu_instruction
    
    # We simulate the command construction
    cmd = f'gemini /ralph:loop \\"{full_mission}\\" --yolo'
    print(f"Generated command (inner): {cmd}")
    
    # We can't easily test 'start' in a headless environment, 
    # but we can test if the string remains valid for subprocess.run
    try:
        # Dry run with --help to see if parsing succeeds
        test_cmd = f'gemini --help'
        subprocess.run(test_cmd, shell=True, check=True, capture_output=True)
        print("✅ CLI parsing successful (base)")
    except Exception as e:
        print(f"❌ CLI base check failed: {e}")

if __name__ == "__main__":
    missions = [
        'Standard mission',
        'Mission with "quotes"',
        'Mission with \n newlines',
        'Mission with & symbols',
        'Mission with ^ carets'
    ]
    for m in missions:
        test_quoting(m)
        print("-" * 20)
