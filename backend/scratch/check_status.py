import urllib.request
import json

login_url = "http://127.0.0.1:8000/api/v1/auth/login"
payload = json.dumps({"email": "capstone.dev@example.com", "password": "Password123!"}).encode("utf-8")
req = urllib.request.Request(login_url, data=payload, headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as resp:
    token = json.loads(resp.read().decode("utf-8"))["access_token"]

proj_id = "15321fc5-1fbb-477c-95aa-bdf84efe51df"
st_url = f"http://127.0.0.1:8000/api/v1/projects/{proj_id}/runtime/status"
st_req = urllib.request.Request(st_url, headers={"Authorization": f"Bearer {token}"})
with urllib.request.urlopen(st_req) as resp:
    st_data = json.loads(resp.read().decode("utf-8"))
    print("Runtime Status Data:")
    print(json.dumps(st_data, indent=2))
    p_url = st_data.get("preview_url")
    print("p_url:", p_url)
    if p_url:
        full_p_url = f"http://127.0.0.1:8000{p_url}" if p_url.startswith("/") else p_url
        try:
            with urllib.request.urlopen(full_p_url) as p_resp:
                html = p_resp.read().decode("utf-8")
                print("HTML length:", len(html))
                print("HTML preview (first 300 chars):")
                print(html[:300])
        except Exception as e:
            print("Error fetching preview url:", e)

