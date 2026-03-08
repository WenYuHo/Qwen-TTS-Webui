import httpx
import asyncio
import sys
import os

async def run_smoke_test():
    print("Starting Smoke Test...")
    base_url = "http://localhost:8080"

    async with httpx.AsyncClient(base_url=base_url) as client:
        # 1. Health check
        try:
            r = await client.get("/api/health")
            r.raise_for_status()
            print("✅ Health Check passed")
        except Exception as e:
            print(f"❌ Health Check failed: {e}")
            return False

        # 2. Model Inventory
        try:
            r = await client.get("/api/models/inventory")
            r.raise_for_status()
            print(f"✅ Model Inventory passed: {len(r.json()['models'])} models found")
        except Exception as e:
            print(f"❌ Model Inventory failed: {e}")
            return False

        # 3. Voice Library
        try:
            test_voice = {"voices": [{"id": 999, "name": "Smoke Test Voice", "type": "preset", "value": "aiden"}]}
            (await client.post("/api/voice/library", json=test_voice)).raise_for_status()
            r = await client.get("/api/voice/library")
            r.raise_for_status()
            if r.json()["voices"][0]["name"] == "Smoke Test Voice":
                print("✅ Voice Library persistence passed")
            else:
                print("❌ Voice Library data mismatch")
                return False
        except Exception as e:
            print(f"❌ Voice Library failed: {e}")
            return False

    print("\n--- Smoke Test Completed Successfully! ---")
    return True

if __name__ == "__main__":
    if asyncio.run(run_smoke_test()):
        sys.exit(0)
    else:
        sys.exit(1)
