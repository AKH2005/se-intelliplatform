import httpx
import json
import time

url = "http://127.0.0.1:8000/api/v1/projects/df084c2c-4fff-464f-84a3-9104f07f31c4/browser-journeys"
payload = {
    "execute_browser_tests": True,
    "max_journeys": 3,
}

print(f"Sending POST to {url} with {payload}...")
start = time.time()
try:
    with httpx.Client(timeout=120.0) as client:
        resp = client.post(url, json=payload)
        print(f"Response status: {resp.status_code}")
        data = resp.json()
        print(json.dumps(data, indent=2))
except Exception as e:
    print(f"Exception: {e}")
print(f"Time taken: {time.time() - start:.2f}s")
