import urllib.request
import ssl

ctx = ssl.create_default_context()

for origin in [
    "https://se-intelliplatform.vercel.app",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://se-intelliplatform-frontend.vercel.app"
]:
    req = urllib.request.Request(
        "https://se-intelliplatform-backend.onrender.com/api/v1/projects/40a7e827-dbc7-4c28-b33c-53a91ea7c727/assistant/messages/stream",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type,accept,x-correlation-id",
        },
        method="OPTIONS"
    )
    try:
        with urllib.request.urlopen(req, context=ctx) as resp:
            print(f"Origin {origin} -> Status: {resp.status}")
            for k, v in resp.headers.items():
                if "access-control" in k.lower():
                    print(f"  {k}: {v}")
    except Exception as e:
        print(f"Origin {origin} -> ERROR: {e}")
