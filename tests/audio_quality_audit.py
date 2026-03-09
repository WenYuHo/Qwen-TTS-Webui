import os
import sys
import asyncio
import httpx
import numpy as np
import soundfile as sf
from pathlib import Path

def analyze_audio(path, label):
    data, sr = sf.read(path)
    
    # ⚡ Bolt: Use pyloudnorm if available for rigorous measurement
    try:
        import pyloudnorm as pyln
        input_data = data if data.ndim == 2 else data[:, None]
        meter = pyln.Meter(sr)
        loudness = meter.integrated_loudness(input_data)
    except Exception:
        loudness = None

    if len(data.shape) > 1:
        data = data[:, 0] # Mono for simpler stats
        
    duration = len(data) / sr
    rms = np.sqrt(np.mean(data**2))
    peak = np.max(np.abs(data))
    
    print(f"\n--- Analysis: {label} ---")
    print(f"Duration: {duration:.2f}s")
    print(f"RMS Energy: {rms:.4f} (Ideal: 0.05 - 0.2)")
    if loudness is not None:
        print(f"Loudness: {loudness:.2f} LUFS (Target: -16.0)")
    print(f"Peak Level: {peak:.4f} (Target: < 0.9)")
    
    if rms < 0.01:
        print("❌ RESULT: Too quiet or silent.")
    elif loudness is not None and abs(loudness - (-16.0)) > 3.0:
        print(f"⚠️ RESULT: Loudness deviation too high ({abs(loudness - (-16.0)):.1f} LUFS)")
    elif peak > 0.95:
        print("❌ RESULT: Audio is clipping or too close to 0dB.")
    elif duration < 1.0:
        print("❌ RESULT: Audio too short, likely failed to generate.")
    else:
        print("✅ RESULT: Audio signature looks healthy.")

async def test_quality_via_api():
    base_url = "http://localhost:8080"
    tests = [
        {"name": "DEEP_MALE", "prompt": "A mature male voice with a deep, authoritative tone and clear articulation."},
        {"name": "BRIGHT_FEMALE", "prompt": "A youthful female voice, bright and energetic, with a friendly, helpful persona."}
    ]
    
    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        for t in tests:
            print(f"\nTesting Template via API: {t['name']}...")
            payload = {
                "profiles": [{"role": "preview", "type": "design", "value": t['prompt']}],
                "script": [{"role": "preview", "text": "This is a technical quality test to ensure the voice sounds natural and clear."}]
            }
            
            try:
                # Create task
                res = await client.post("/api/generate/segment", json=payload)
                task_id = res.json()["task_id"]
                print(f"Task created: {task_id}. Polling...")
                
                # Poll for completion
                while True:
                    task_res = await client.get(f"/api/tasks/{task_id}")
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
                    
                    await asyncio.sleep(2)
            except Exception as e:
                print(f"❌ API Request failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_quality_via_api())
