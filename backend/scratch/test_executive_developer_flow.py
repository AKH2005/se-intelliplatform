import asyncio
import json
import httpx
import uuid
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.core.security import create_access_token

BASE_URL = "http://127.0.0.1:8000"
PREVIEW_URL = "http://127.0.0.1:8001"
PROJECT_ID = "d8dc8495-6b8a-4fe3-940a-2b436d475454"
USER_ID = "4efd163c-cd5d-483c-89c8-0d40e43ff3eb"

async def main():
    token = create_access_token(data={"sub": USER_ID, "role": "ADMIN"})
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Check project
        p_res = await client.get(f"{BASE_URL}/api/v1/projects/{PROJECT_ID}", headers=headers)
        print("Project Status:", p_res.status_code, p_res.json()["name"])
        settings_before = p_res.json().get("settings") or {}
        print("Active Version before:", settings_before.get("active_version_id"))

        # Create new conversation
        conv_res = await client.post(
            f"{BASE_URL}/api/v1/projects/{PROJECT_ID}/assistant/conversations",
            json={"title": "Autonomous Bug Repair Acceptance"},
            headers=headers,
        )
        conv_id = conv_res.json()["conversation_id"]
        print("Created conversation:", conv_id)

        turns = [
            ("The modal still doesn't appear.", "REPAIR_MODAL"),
            ("The export CSV button isn't working", "REPAIR_CSV"),
            ("Add an analytics filter endpoint for date ranges", "ADD_ENDPOINT"),
        ]

        for query, label in turns:
            print(f"\n=======================================================")
            print(f"SENDING PROMPT: '{query}' ({label})")
            print(f"=======================================================")

            stream_url = f"{BASE_URL}/api/v1/projects/{PROJECT_ID}/assistant/messages/stream"
            payload = {"content": query, "conversation_id": conv_id}

            statuses = []
            full_reply = ""
            current_event = None

            async with client.stream("POST", stream_url, json=payload, headers=headers, timeout=90.0) as resp:
                print(f"Stream status code: {resp.status_code}")
                async for line in resp.aiter_lines():
                    if line.startswith("event: "):
                        current_event = line.replace("event: ", "").strip()
                    elif line.startswith("data: ") and current_event:
                        data_str = line.replace("data: ", "").strip()
                        try:
                            data = json.loads(data_str)
                            if current_event == "status":
                                statuses.append(data.get("status"))
                                print(f"  [STATUS] {data.get('status')}")
                            elif current_event == "content":
                                full_reply += data.get("chunk", "")
                        except Exception:
                            pass

            print("\n--- FINAL ASSISTANT REPLY ---")
            print(full_reply)
            print("-----------------------------\n")

            # Check project active version after
            p_after = await client.get(f"{BASE_URL}/api/v1/projects/{PROJECT_ID}", headers=headers)
            settings_after = p_after.json().get("settings") or {}
            print("Active Version after:", settings_after.get("active_version_id"))

            # Check preview content
            prev_res = await client.get(f"{PREVIEW_URL}/preview?project_id={PROJECT_ID}")
            print(f"Live Preview response: {prev_res.status_code}, length={len(prev_res.text)}")
            print("Contains btn-open-login:", "btn-open-login" in prev_res.text)
            print("Contains auth-modal-overlay:", "auth-modal-overlay" in prev_res.text)
            print("Contains btn-export-csv:", "btn-export-csv" in prev_res.text)

if __name__ == "__main__":
    asyncio.run(main())
