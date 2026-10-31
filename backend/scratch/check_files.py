import urllib.request
import json

login_url = "http://127.0.0.1:8000/api/v1/auth/login"
payload = json.dumps({"email": "capstone.dev@example.com", "password": "Password123!"}).encode("utf-8")
req = urllib.request.Request(login_url, data=payload, headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as resp:
    token = json.loads(resp.read().decode("utf-8"))["access_token"]

proj_id = "15321fc5-1fbb-477c-95aa-bdf84efe51df"
tree_url = f"http://127.0.0.1:8000/api/v1/projects/{proj_id}/files"
req_tree = urllib.request.Request(tree_url, headers={"Authorization": f"Bearer {token}"})
with urllib.request.urlopen(req_tree) as resp:
    tree_data = json.loads(resp.read().decode("utf-8"))
    print("Total files:", tree_data.get("total_files"))
    print("Root children names:")
    for child in tree_data.get("root", {}).get("children", []):
        print(" -", child.get("name"), child.get("type"), child.get("path"))

# Let's also fetch frontend/src/styles/App.css
css_url = f"http://127.0.0.1:8000/api/v1/projects/{proj_id}/files/frontend/src/styles/App.css"
req_css = urllib.request.Request(css_url, headers={"Authorization": f"Bearer {token}"})
try:
    with urllib.request.urlopen(req_css) as resp:
        css_data = json.loads(resp.read().decode("utf-8"))
        print("\nfrontend/src/styles/App.css content (first 200 chars):")
        print(css_data.get("content", "")[:200])
except Exception as e:
    print("Error getting App.css:", e)

# Let's also fetch frontend/src/App.tsx
tsx_url = f"http://127.0.0.1:8000/api/v1/projects/{proj_id}/files/frontend/src/App.tsx"
req_tsx = urllib.request.Request(tsx_url, headers={"Authorization": f"Bearer {token}"})
try:
    with urllib.request.urlopen(req_tsx) as resp:
        tsx_data = json.loads(resp.read().decode("utf-8"))
        print("\nfrontend/src/App.tsx content (first 200 chars):")
        print(tsx_data.get("content", "")[:200])
except Exception as e:
    print("Error getting App.tsx:", e)

