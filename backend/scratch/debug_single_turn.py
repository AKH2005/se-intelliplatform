import asyncio
import json
import httpx
from app.core.security import create_access_token

BASE_URL = "http://127.0.0.1:8000"
PROJECT_ID = "68289eab-12f4-4602-a4b7-143f29c52c58"
USER_ID = "4efd163c-cd5d-483c-89c8-0d40e43ff3eb"

async def debug_one():
    token = create_access_token(data={"sub": USER_ID, "role": "ADMIN"})
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        conv_res = await client.post(
            f"{BASE_URL}/api/v1/projects/{PROJECT_ID}/assistant/conversations",
            json={"title": "Debug Run"},
            headers=headers,
        )
        conversation_id = conv_res.json()["conversation_id"]
        print("Conv:", conversation_id)

        stream_url = f"{BASE_URL}/api/v1/projects/{PROJECT_ID}/assistant/messages/stream"
        payload = {
            "content": "Add a login page to my application.",
            "conversation_id": conversation_id,
        }

        async with client.stream("POST", stream_url, json=payload, headers=headers, timeout=60.0) as resp:
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    d = json.loads(line[6:])
                    if "status" in d:
                        print("STATUS:", d["status"])
                    elif "role" in d and d.get("role") == "assistant":
                        print("DONE EVENT action_result:")
                        print(json.dumps(d.get("action_result"), indent=2))

if __name__ == "__main__":
    asyncio.run(debug_one())
