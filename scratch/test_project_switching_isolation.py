import asyncio
import os
import sys
import uuid
import urllib.request
from sqlalchemy import select

sys.path.insert(0, os.path.abspath("backend"))

from app.core.database import AsyncSessionLocal
from app.core.security import create_preview_token
from app.models.project import Project

async def run_switching_isolation_test():
    print("=== TESTING AUTHENTICATED PROJECT SWITCHING & ISOLATION ===")
    
    target_pids = [
        ("Shadow Master", uuid.UUID("b9a73557-04a6-4db5-9056-10884a2d5d53"), ["combatCanvas", "Shadow Master", "Katana Slash"], ["carromCanvas", "spawnFood", "new-task-input"]),
        ("Carrom Master", uuid.UUID("657e9d2a-4dd2-4fe9-9bb7-20717c43b588"), ["carromCanvas", "Carrom Master"], ["combatCanvas", "spawnFood", "new-task-input"]),
        ("Executive Analytics", uuid.UUID("51458fe8-776f-4325-9e5a-bfc33dce112d"), ["Executive", "Analytics"], ["combatCanvas", "carromCanvas", "spawnFood", "new-task-input"]),
        ("EventHub", uuid.UUID("114251d8-772d-4444-9035-af66154d2612"), ["EventHub", "events"], ["combatCanvas", "carromCanvas", "spawnFood"]),
    ]

    all_passed = True
    async with AsyncSessionLocal() as session:
        for cycle in range(1, 4):
            print(f"\n--- Isolation Cycle {cycle} ---")
            for name, pid, expected, forbidden in target_pids:
                stmt = select(Project).where(Project.id == pid)
                res = await session.execute(stmt)
                proj = res.scalar_one_or_none()
                if not proj:
                    print(f"ERROR: Project {pid} not found")
                    all_passed = False
                    continue

                # Generate secure preview token
                user_id = proj.owner_id or uuid.UUID("4efd163c-cd5d-483c-89c8-0d40e43ff3eb")
                token = create_preview_token(user_id=user_id, project_id=pid)

                # Test 1: Backend Secure Endpoint
                backend_url = f"http://127.0.0.1:8000/api/v1/projects/{pid}/runtime/preview?preview_token={token}"
                req = urllib.request.Request(backend_url)
                try:
                    with urllib.request.urlopen(req, timeout=5) as resp:
                        html = resp.read().decode("utf-8", errors="replace")
                        missing = [m for m in expected if m.lower() not in html.lower()]
                        leaked = [m for m in forbidden if m.lower() in html.lower()]

                        if missing:
                            print(f"FAIL [{name} - Backend]: Missing expected markers: {missing}")
                            all_passed = False
                        elif leaked:
                            print(f"FAIL [{name} - Backend]: LEAK detected: {leaked}")
                            all_passed = False
                        else:
                            print(f"PASS [{name} - Backend]: Verified authentic serving, zero leakage (HTTP {resp.status})")
                except Exception as e:
                    print(f"ERROR [{name} - Backend]: {e}")
                    all_passed = False

                # Test 2: Preview Server Port 8001
                preview_srv_url = f"http://127.0.0.1:8001/?project_id={pid}"
                req_srv = urllib.request.Request(preview_srv_url)
                try:
                    with urllib.request.urlopen(req_srv, timeout=5) as resp:
                        html_srv = resp.read().decode("utf-8", errors="replace")
                        missing_srv = [m for m in expected if m.lower() not in html_srv.lower()]
                        leaked_srv = [m for m in forbidden if m.lower() in html_srv.lower()]

                        if missing_srv:
                            print(f"FAIL [{name} - Preview Server 8001]: Missing expected markers: {missing_srv}")
                            all_passed = False
                        elif leaked_srv:
                            print(f"FAIL [{name} - Preview Server 8001]: LEAK detected: {leaked_srv}")
                            all_passed = False
                        else:
                            print(f"PASS [{name} - Preview Server 8001]: Verified authentic serving, zero leakage (HTTP {resp.status})")
                except Exception as e:
                    print(f"ERROR [{name} - Preview Server 8001]: {e}")
                    all_passed = False

    if all_passed:
        print("\nALL PROJECT SWITCHING & ISOLATION CHECKS PASSED 100%! ZERO CROSS-PROJECT LEAKAGE!")
    else:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_switching_isolation_test())