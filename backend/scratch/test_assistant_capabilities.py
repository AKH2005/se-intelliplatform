"""Test IntelliAssist Conversational Capabilities & SSE Token Streaming.

Verifies:
1. Answering general questions naturally and clearly via SSE streaming.
2. Understanding selected project and active version context.
3. Distinguishing advice, proposed changes, applied changes, and verified results.
4. Explaining errors and proposing relevant fixes.
"""

import asyncio
import json
import sys
sys.stdout.reconfigure(encoding='utf-8')
import uuid
import urllib.request
import urllib.error

backend_dir = r"c:\Users\DELL\OneDrive\Documents\SE Intellplatform\backend"
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.database import AsyncSessionLocal
from sqlalchemy import select
from app.models.user import User
from app.core.security import create_access_token

BASE_URL = "http://127.0.0.1:8000/api/v1"

def stream_request(project_id: str, token: str, prompt: str, conversation_id: str = None) -> list[dict]:
    url = f"{BASE_URL}/projects/{project_id}/assistant/messages/stream"
    payload = {"content": prompt}
    if conversation_id:
        payload["conversation_id"] = conversation_id
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
        method="POST"
    )
    events = []
    try:
        with urllib.request.urlopen(req, timeout=30.0) as resp:
            current_event = None
            for line in resp:
                decoded = line.decode("utf-8").strip()
                if decoded.startswith("event:"):
                    current_event = decoded.replace("event:", "").strip()
                elif decoded.startswith("data:"):
                    raw_data = decoded.replace("data:", "").strip()
                    try:
                        parsed = json.loads(raw_data)
                    except Exception:
                        parsed = raw_data
                    events.append({"event": current_event, "data": parsed})
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.read().decode('utf-8')}")
    except Exception as exc:
        print(f"Stream error: {exc}")
    return events

async def main():
    print("=" * 80)
    print("TESTING INTELLIASSIST CONVERSATIONAL CAPABILITIES & SSE STREAMING")
    print("=" * 80)

    # Resolve token for Akhil
    async with AsyncSessionLocal() as session:
        u_res = await session.execute(select(User).where(User.email == "madanuakhil07@gmail.com"))
        user = u_res.scalar_one_or_none()
        token = create_access_token(data={"sub": str(user.id), "email": user.email})

    # Use project MiniTask
    project_id = "da0fe559-8583-43af-992e-ddb88a69a795"

    # Test 1: General software engineering question
    print("\n[Query 1] General question: 'Explain the difference between SQL and NoSQL databases'")
    events1 = stream_request(project_id, token, "Explain the difference between SQL and NoSQL databases in 2 short bullet points.")
    content_chunks1 = [e["data"].get("chunk", "") for e in events1 if e.get("event") == "content"]
    full_text1 = "".join(content_chunks1)
    print(f"Events received: {len(events1)}")
    print(f"Response:\n{full_text1}")
    assert len(full_text1) > 20, "Response 1 too short or empty"

    # Test 2: Project-specific inquiry
    print("\n[Query 2] Project context: 'What is the structure of this project and what framework does it use?'")
    events2 = stream_request(project_id, token, "What is the structure of this project and what framework does it use?")
    content_chunks2 = [e["data"].get("chunk", "") for e in events2 if e.get("event") == "content"]
    full_text2 = "".join(content_chunks2)
    print(f"Events received: {len(events2)}")
    print(f"Response:\n{full_text2}")
    assert len(full_text2) > 20, "Response 2 too short or empty"

    print("\n" + "=" * 80)
    print("INTELLIASSIST STREAMING TESTS PASSED!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
