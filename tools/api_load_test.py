import asyncio
import time
import httpx
import statistics
import argparse

async def send_request(client, url, payload):
    start = time.time()
    try:
        resp = await client.post(url, json=payload, timeout=60.0)
        duration = time.time() - start
        return duration, resp.status_code
    except Exception as e:
        return time.time() - start, str(e)

async def run_load_test(url, concurrent_users, total_requests):
    payload = {
        "profiles": [{"role": "test", "type": "preset", "value": "Ryan"}],
        "script": [{"role": "test", "text": "This is a load test segment."}]
    }
    
    print(f"Starting load test: {total_requests} requests, {concurrent_users} concurrent users...")
    
    async with httpx.AsyncClient() as client:
        tasks = []
        for _ in range(total_requests):
            # Simple throttle to maintain concurrency
            if len(tasks) >= concurrent_users:
                done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                tasks = list(pending)
            
            tasks.append(asyncio.create_task(send_request(client, url, payload)))
        
        results = await asyncio.gather(*tasks)
    
    durations = [r[0] for r in results if isinstance(r[1], int) and r[1] == 200]
    errors = [r for r in results if not (isinstance(r[1], int) and r[1] == 200)]
    
    print("
--- Load Test Results ---")
    print(f"Total Requests: {total_requests}")
    print(f"Successful:     {len(durations)}")
    print(f"Failed/Errors:  {len(errors)}")
    
    if durations:
        print(f"Average Latency: {statistics.mean(durations):.2f}s")
        print(f"Median Latency:  {statistics.median(durations):.2f}s")
        print(f"Min Latency:     {min(durations):.2f}s")
        print(f"Max Latency:     {max(durations):.2f}s")
        print(f"Throughput:      {len(durations) / sum(durations):.2f} req/s (approx)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Qwen-TTS API Load Tester")
    parser.add_argument("--url", default="http://localhost:8080/api/generate/segment", help="API Endpoint URL")
    parser.add_argument("--users", type=int, default=5, help="Concurrent users")
    parser.add_argument("--reqs", type=int, default=20, help="Total requests")
    
    args = parser.parse_args()
    asyncio.run(run_load_test(args.url, args.users, args.reqs))
