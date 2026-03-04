import os
import sys
import time
import requests
import numpy as np
import soundfile as sf
from pathlib import Path

def analyze_audio(path, label):
    data, sr = sf.read(path)
    if len(data.shape) > 1:
        data = data[:, 0] # Mono
        
    duration = len(data) / sr
    rms = np.sqrt(np.mean(data**2))
    peak = np.max(np.abs(data))
    
    print(f"\n--- Analysis: {label} ---")
    print(f"Duration: {duration:.2f}s")
    print(f"RMS Energy: {rms:.4f} (Ideal: 0.05 - 0.2)")
    print(f"Peak Level: {peak:.4f} (Ideal: < 1.0)")
    
    if rms < 0.01:
        print("❌ RESULT: Too quiet or silent.")
    elif duration < 1.0:
        print("❌ RESULT: Audio too short, likely failed to generate.")
    else:
        print("✅ RESULT: Audio signature looks healthy.")

def test_quality_via_api():
    base_url = "http://localhost:8080"
    tests = [
        {"name": "DEEP_MALE", "prompt": "A mature male voice with a deep, authoritative tone and clear articulation."},
        {"name": "BRIGHT_FEMALE", "prompt": "A youthful female voice, bright and energetic, with a friendly, helpful persona."}
    ]
    
    for t in tests:
        print(f"\nTesting Template via API: {t['name']}...")
        payload = {
            "profiles": [{"role": "preview", "type": "design", "value": t['prompt']}],
            "script": [{"role": "preview", "text": "This is a technical quality test to ensure the voice sounds natural and clear."}]
        }
        
        try:
            # Create task
            res = requests.post(f"{base_url}/api/generate/segment", json=payload)
            task_id = res.json()["task_id"]
            print(f"Task created: {task_id}. Polling...")
            
            # Poll for completion
            while True:
                task_res = requests.get(f"{base_url}/api/tasks/{task_id}")
                task_data = task_res.json()
                status = task_data["status"]
                
                if status == "completed":
                    print("Task completed!")
                    # Task manager in this project stores result as bytes
                    # result field is expected to be present in completed task
                    audio_bytes = bytes(task_data["result"])
                    path = f"test_{t['name']}.wav"
                    with open(path, "wb") as f:
                        f.write(audio_bytes)
                    analyze_audio(path, t['name'])
                    break
                elif status == "failed":
                    print(f"❌ Task failed: {task_data.get('error')}")
                    break
                
                time.sleep(2)
        except Exception as e:
            print(f"❌ API Request failed: {e}")

if __name__ == "__main__":
    test_quality_via_api()
