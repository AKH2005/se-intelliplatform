import urllib.request
import urllib.error
import ssl
import json
import sys

backend_dir = r"c:\Users\DELL\OneDrive\Documents\SE Intellplatform\backend"
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.security import create_access_token

USER_ID = "4efd163c-cd5d-483c-89c8-0d40e43ff3eb"  # madanuakhil07@gmail.com
AUTH_TOKEN = create_access_token({"sub": USER_ID})

ctx = ssl.create_default_context()

# Test 1: POST to Carrom Master on Render with LOCAL ID (657e9d2a-4dd2-4fe9-9bb7-20717c43b588)
local_id = "657e9d2a-4dd2-4fe9-9bb7-20717c43b588"
url_local = f"https://se-intelliplatform-backend.onrender.com/api/v1/projects/{local_id}/assistant/messages/stream"
req1 = urllib.request.Request(
    url_local,
    headers={
        "Origin": "https://se-intelliplatform.vercel.app",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
        "Authorization": f"Bearer {AUTH_TOKEN}",
    },
    data=json.dumps({"content": "Add a login page."}).encode("utf-8"),
    method="POST"
)
try:
    with urllib.request.urlopen(req1, context=ctx) as resp:
        print("Test 1 (Local ID on Render) -> Status:", resp.status)
except urllib.error.HTTPError as e:
    body = e.read().decode("utf-8")
    print(f"Test 1 (Local ID on Render) -> HTTP {e.code}: {body}")
    print("Test 1 Response Headers:")
    for k, v in e.headers.items():
        if "access-control" in k.lower():
            print(f"  {k}: {v}")
except Exception as e:
    print("Test 1 Error:", e)

# Test 2: POST to Carrom Master on Render with RENDER ID (40a7e827-dbc7-4c28-b33c-53a91ea7c727)
render_id = "40a7e827-dbc7-4c28-b33c-53a91ea7c727"
url_render = f"https://se-intelliplatform-backend.onrender.com/api/v1/projects/{render_id}/assistant/messages/stream"
req2 = urllib.request.Request(
    url_render,
    headers={
        "Origin": "https://se-intelliplatform.vercel.app",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
        "Authorization": f"Bearer {AUTH_TOKEN}",
    },
    data=json.dumps({"content": "Add a login page."}).encode("utf-8"),
    method="POST"
)
try:
    with urllib.request.urlopen(req2, context=ctx) as resp:
        print("Test 2 (Render ID on Render) -> Status:", resp.status)
        first_chunk = resp.read(200).decode("utf-8")
        print("Test 2 First chunk:", first_chunk)
except urllib.error.HTTPError as e:
    body = e.read().decode("utf-8")
    print(f"Test 2 (Render ID on Render) -> HTTP {e.code}: {body}")
    print("Test 2 Response Headers:")
    for k, v in e.headers.items():
        if "access-control" in k.lower():
            print(f"  {k}: {v}")
except Exception as e:
    print("Test 2 Error:", e)
