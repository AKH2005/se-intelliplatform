import httpx
import json

url = "http://127.0.0.1:8000/api/v1/projects/df084c2c-4fff-464f-84a3-9104f07f31c4/analysis/failure"
payload = {"force": True}

print(f"Calling {url} with {payload}...")
with httpx.Client(timeout=60.0) as client:
    res = client.post(url, json=payload)
    print("Status:", res.status_code)
    try:
        data = res.json()
        print("Diagnosis ID:", data.get("diagnosis_id"))
        print("Failure Type:", data.get("failure_type"))
        print("Title:", data.get("title"))
        print("Root Cause:", data.get("root_cause"))
        print("Affected Files:", data.get("affected_files"))
        print("Remediation Plan:", data.get("suggested_remediation"))
    except Exception as e:
        print("Raw text:", res.text)
