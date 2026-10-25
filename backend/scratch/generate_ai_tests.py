import urllib.request
import json
import sys

def main():
    project_id = "df084c2c-4fff-464f-84a3-9104f07f31c4"
    url = f"http://127.0.0.1:8000/api/v1/projects/{project_id}/tests/ai/generate"
    payload = json.dumps({"workflow_execution_id": "21f79f09-a714-4fa0-9905-09eb0970ac16"}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        print("Sending request to generate AI tests...")
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read().decode())
            print(f"HTTP {resp.status} Success!")
            suite_id = data.get("suite_id")
            print(f"Generated Suite ID: {suite_id}")
            tests = data.get("test_cases", [])
            print(f"Total Test Cases: {len(tests)}")
            for t in tests:
                print(f"  • [{t.get('category')}] {t.get('test_name')} - {t.get('target_function')}")
            
            # Save suite_id for next step
            with open("scratch/latest_suite.json", "w") as f:
                json.dump({"suite_id": suite_id, "project_id": project_id}, f)
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.read().decode()}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
