import sys
import ssl
import json
import urllib.request
import urllib.error

backend_dir = r"c:\Users\DELL\OneDrive\Documents\SE Intellplatform\backend"
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.security import create_access_token

USER_ID = "4efd163c-cd5d-483c-89c8-0d40e43ff3eb"  # madanuakhil07@gmail.com
AUTH_TOKEN = create_access_token({"sub": USER_ID})
LOCAL_CARROM_ID = "657e9d2a-4dd2-4fe9-9bb7-20717c43b588"
ctx = ssl.create_default_context()

print("=" * 70)
print("1. LOCAL BACKEND HEALTH & ENDPOINTS AUDIT")
print("=" * 70)

local_tests = [
    ("Health", "GET", "http://127.0.0.1:8000/api/v1/health", None, False),
    ("Root Health", "GET", "http://127.0.0.1:8000/health", None, False),
    ("Auth Me", "GET", "http://127.0.0.1:8000/api/v1/auth/me", None, True),
    ("Projects List", "GET", "http://127.0.0.1:8000/api/v1/projects", None, True),
    ("Active Version", "GET", f"http://127.0.0.1:8000/api/v1/projects/{LOCAL_CARROM_ID}/versions/active", None, True),
    ("Assistant Conversations", "GET", f"http://127.0.0.1:8000/api/v1/projects/{LOCAL_CARROM_ID}/assistant/conversations", None, True),
    ("Assistant Stream OPTIONS", "OPTIONS", f"http://127.0.0.1:8000/api/v1/projects/{LOCAL_CARROM_ID}/assistant/messages/stream", None, False),
]

for name, method, url, data, needs_auth in local_tests:
    headers = {"Origin": "http://127.0.0.1:5173"}
    if needs_auth:
        headers["Authorization"] = f"Bearer {AUTH_TOKEN}"
    if method == "OPTIONS":
        headers["Access-Control-Request-Method"] = "POST"
        headers["Access-Control-Request-Headers"] = "authorization,content-type,accept,x-correlation-id"
    req = urllib.request.Request(url, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            print(f"[LOCAL] {name} ({method} {url}) -> HTTP {resp.status}")
    except urllib.error.HTTPError as e:
        print(f"[LOCAL] {name} ({method} {url}) -> HTTP {e.code}: {e.read().decode('utf-8')[:100]}")
    except Exception as e:
        print(f"[LOCAL] {name} ({method} {url}) -> FAILED: {e}")

print("\n" + "=" * 70)
print("2. RENDER BACKEND HEALTH & ENDPOINTS AUDIT")
print("=" * 70)

render_tests = [
    ("Health", "GET", "https://se-intelliplatform-backend.onrender.com/api/v1/health", None, False),
    ("Root Health", "GET", "https://se-intelliplatform-backend.onrender.com/health", None, False),
    ("Auth Me (Local Token)", "GET", "https://se-intelliplatform-backend.onrender.com/api/v1/auth/me", None, True),
    ("Projects List", "GET", "https://se-intelliplatform-backend.onrender.com/api/v1/projects", None, True),
]

for name, method, url, data, needs_auth in render_tests:
    headers = {"Origin": "https://se-intelliplatform.vercel.app"}
    if needs_auth:
        headers["Authorization"] = f"Bearer {AUTH_TOKEN}"
    req = urllib.request.Request(url, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            body = resp.read().decode('utf-8')
            print(f"[RENDER] {name} ({method} {url}) -> HTTP {resp.status}: {body[:120]}")
    except urllib.error.HTTPError as e:
        print(f"[RENDER] {name} ({method} {url}) -> HTTP {e.code}: {e.read().decode('utf-8')[:120]}")
    except Exception as e:
        print(f"[RENDER] {name} ({method} {url}) -> FAILED: {e}")
