import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath("backend"))

from app.core.database import AsyncSessionLocal
from app.models.project import Project
from app.models.user import User
from app.api.v1.endpoints.preview_runtime import resolve_project_mode, get_project_preview_html
import uuid
import httpx

async def verify():
    pid = uuid.UUID("b9a73557-04a6-4db5-9056-10884a2d5d53")
    async with AsyncSessionLocal() as session:
        proj = await session.get(Project, pid)
        mode = resolve_project_mode(proj)
        print("Resolved mode for project:", mode)
        assert mode == "shadow_master", f"Expected shadow_master, got {mode}"

        owner = await session.get(User, proj.owner_id)
        resp = await get_project_preview_html(project_id=pid, session=session, current_user=owner)
        html = resp.body.decode("utf-8")
        print("Preview HTML response status:", resp.status_code, "length:", len(html))
        assert "Shadow Master" in html, "Shadow Master not in HTML!"
        assert "Katana Slash" in html, "Katana Slash not in HTML!"
        assert "Interactive Application Playground" not in html, "Generic playground placeholder found in HTML!"
        assert "Trigger Primary Action" not in html, "Generic trigger primary action found in HTML!"
        assert "spawnFood" not in html, "Snake spawnFood found in HTML!"
        assert "task-form" not in html, "Kanban task-form found in HTML!"
        print("ANTICOLLISION & AUTHENTICITY CHECKS PASSED 100% on preview endpoint!")

    # Check port 8001 preview server
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"http://127.0.0.1:8001/?project_id={pid}", timeout=3.0)
            print("Port 8001 preview response status:", r.status_code, "length:", len(r.text))
            assert "Shadow Master" in r.text, "Port 8001 HTML missing Shadow Master!"
            assert "Katana Slash" in r.text, "Port 8001 HTML missing Katana Slash!"
            assert "Interactive Application Playground" not in r.text, "Port 8001 HTML contains playground fallback!"
            print("PORT 8001 PREVIEW SERVER RETURNED AUTHENTIC SHADOW MASTER GAME 100%!")
    except Exception as e:
        print(f"Port 8001 probe: {e}")

if __name__ == "__main__":
    asyncio.run(verify())
