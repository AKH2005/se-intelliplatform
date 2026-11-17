import asyncio
import json
import httpx
import uuid
from app.core.security import create_access_token

BASE_URL = "http://127.0.0.1:8000"
PROJECT_ID = "68289eab-12f4-4602-a4b7-143f29c52c58"
USER_ID = "4efd163c-cd5d-483c-89c8-0d40e43ff3eb"

async def test_assistant_flow():
    # 1. Create valid JWT token for project owner
    token = create_access_token(data={"sub": USER_ID, "role": "ADMIN"})
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 2. Check project active version before
        proj_res = await client.get(f"{BASE_URL}/api/v1/projects/{PROJECT_ID}", headers=headers)
        print("Project name:", proj_res.json()["name"])
        settings_obj = proj_res.json().get("settings") or {}
        print("Active Version ID before:", settings_obj.get("active_version_id"))

        # 3. Create conversation
        conv_res = await client.post(
            f"{BASE_URL}/api/v1/projects/{PROJECT_ID}/assistant/conversations",
            json={"title": "Autonomous Developer Acceptance Run"},
            headers=headers,
        )
        conversation_id = conv_res.json()["conversation_id"]
        print("Conversation created:", conversation_id)

        queries = [
            ("Add a login page to my application.", True),
            ("Improve the login page design.", True),
            ("Add a forgot password link.", True),
            ("Make the login page responsive.", True),
            ("Explain how authentication works.", False),
        ]

        for query, expect_version_bump in queries:
            print(f"\n=======================================================")
            print(f"SENDING PROMPT: '{query}'")
            print(f"=======================================================")

            # Test streaming endpoint
            stream_url = f"{BASE_URL}/api/v1/projects/{PROJECT_ID}/assistant/messages/stream"
            payload = {
                "content": query,
                "conversation_id": conversation_id,
            }

            chunks = []
            statuses = []
            done_payload = None

            async with client.stream("POST", stream_url, json=payload, headers=headers, timeout=60.0) as resp:
                print(f"Stream status code: {resp.status_code}")
                async for line in resp.aiter_lines():
                    if line.startswith("event: status"):
                        pass
                    elif line.startswith("data: "):
                        data_str = line[6:]
                        try:
                            data_json = json.loads(data_str)
                            if "status" in data_json:
                                statuses.append(data_json["status"])
                                print("  [STATUS]", data_json["status"])
                            elif "chunk" in data_json:
                                chunks.append(data_json["chunk"])
                            elif "role" in data_json and data_json.get("role") == "assistant":
                                done_payload = data_json
                        except Exception:
                            pass

            full_reply = "".join(chunks)
            print("\n--- Assistant Reply ---")
            print(full_reply[:500] + ("..." if len(full_reply) > 500 else ""))

            # Check project active version after
            p_after = await client.get(f"{BASE_URL}/api/v1/projects/{PROJECT_ID}", headers=headers)
            s_after = p_after.json().get("settings") or {}
            print(f"\nActive Version ID after '{query[:30]}':", s_after.get("active_version_id"))

            if done_payload:
                print("Action ID:", done_payload.get("action_id"))
                print("Action Status:", done_payload.get("action_status"))

            # Check preview server HTML
            try:
                prev_res = await client.get(f"http://127.0.0.1:8001/preview?project_id={PROJECT_ID}", timeout=5.0)
                print(f"Preview Server Status: {prev_res.status_code}, HTML length: {len(prev_res.text)}")
                print("  - Preview has 'btn-open-login':", 'btn-open-login' in prev_res.text)
                print("  - Preview has 'auth-modal-overlay':", 'auth-modal-overlay' in prev_res.text)
                if "design" in query.lower():
                    print("  - Preview has 'pwd-meter' or 'btn-social':", 'pwd-meter' in prev_res.text or 'btn-social' in prev_res.text)
                if "forgot" in query.lower():
                    print("  - Preview has 'link-forgot-password':", 'link-forgot-password' in prev_res.text)
                if "responsive" in query.lower():
                    print("  - Preview has responsive media queries:", '@media (max-width: 768px)' in prev_res.text)
            except Exception as e:
                print("Preview check warning:", e)

if __name__ == "__main__":
    asyncio.run(test_assistant_flow())
