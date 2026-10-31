"""Forensic verification script to audit all core endpoints and contracts against MiniTask."""

import asyncio
import json
import uuid
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.project import Project
from app.core.security import create_access_token
from sqlalchemy import select


async def run_audit():
    transport = ASGITransport(app=app)
    results = {}

    # Target MiniTask project
    async with AsyncSessionLocal() as session:
        res_p = await session.execute(
            select(Project).where(Project.name.ilike("%MiniTask%"))
        )
        minitask = res_p.scalar_one_or_none()
        if not minitask:
            print("MiniTask not found in DB")
            return

        proj_id = str(minitask.id)
        owner_id = minitask.owner_id

        # Get owner token
        res_owner = await session.execute(select(User).where(User.id == owner_id))
        owner = res_owner.scalar_one_or_none()
        owner_token = create_access_token({"sub": str(owner.id)}) if owner else None

        # Get non-owner token
        res_other = await session.execute(select(User).where(User.id != owner_id))
        other = res_other.scalar_one_or_none()
        other_token = create_access_token({"sub": str(other.id)}) if other else None

    auth_headers = {"Authorization": f"Bearer {owner_token}"}
    other_headers = {"Authorization": f"Bearer {other_token}"}

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Target Project Info
        results["target_project"] = {
            "id": proj_id,
            "name": minitask.name,
            "owner": owner.email if owner else None,
            "active_version_id": (minitask.settings or {}).get("active_version_id"),
        }

        # 2. Authorization checks
        unauth_resp = await client.get(f"/api/v1/projects/{proj_id}/files")
        other_resp = await client.get(f"/api/v1/projects/{proj_id}/files", headers=other_headers)
        owner_resp = await client.get(f"/api/v1/projects/{proj_id}/files", headers=auth_headers)

        results["authorization_enforcement"] = {
            "unauthenticated_status": unauth_resp.status_code,
            "cross_user_forbidden_status": other_resp.status_code,
            "authorized_owner_status": owner_resp.status_code,
            "strictly_isolated": (
                unauth_resp.status_code == 403
                and other_resp.status_code == 403
                and owner_resp.status_code == 200
            ),
        }

        # 3. Development Versions
        resp_vers = await client.get(f"/api/v1/projects/{proj_id}/versions", headers=auth_headers)
        vers_data = resp_vers.json()
        results["versions"] = {
            "total": vers_data.get("total"),
            "active_version_id": vers_data.get("active_version_id"),
            "versions_list": [
                {
                    "number": v.get("version_number"),
                    "status": v.get("status"),
                    "file_count": v.get("file_count"),
                    "is_active": v.get("is_active"),
                }
                for v in vers_data.get("items", [])
            ],
        }

        # 4. Code Studio File Tree
        files_data = owner_resp.json()
        results["code_studio_active_files"] = {
            "version_number": files_data.get("version_number"),
            "total_files": files_data.get("total_files"),
            "file_paths": [f.get("path") for f in files_data.get("files", [])],
        }

        # 5. Workflows Discovery
        resp_wf = await client.get("/api/v1/workflows", headers=auth_headers)
        wf_list = resp_wf.json()
        results["workflows_discovery"] = {
            "count": len(wf_list),
            "workflows": [w.get("workflow_id") for w in wf_list],
            "has_code_generation": any(w.get("workflow_id") == "code-generation-workflow" for w in wf_list),
            "has_browser_journey": any(w.get("workflow_id") == "browser-journey-workflow" for w in wf_list),
        }

        # 6. Workflow History
        resp_hist = await client.get(f"/api/v1/projects/{proj_id}/workflows/history", headers=auth_headers)
        hist_data = resp_hist.json()
        results["workflow_history"] = {
            "total": hist_data.get("total"),
            "executions": [
                {
                    "workflow_id": h.get("workflow_id"),
                    "status": h.get("status"),
                    "completed_steps": h.get("completed_steps"),
                    "step_count": h.get("step_count"),
                }
                for h in hist_data.get("items", [])
            ],
        }

        # 7. Assistant Conversations
        resp_conv = await client.get(f"/api/v1/projects/{proj_id}/assistant/conversations", headers=auth_headers)
        conv_data = resp_conv.json()
        results["assistant_conversations"] = {
            "total": conv_data.get("total"),
            "conversations": conv_data.get("items", []),
        }

        # 8. Environments
        resp_env = await client.get(f"/api/v1/projects/{proj_id}/environments", headers=auth_headers)
        env_list = resp_env.json()
        results["environments"] = [
            {
                "type": e.get("environment_type"),
                "status": e.get("status"),
                "current_version_id": e.get("current_version_id"),
                "current_version_number": e.get("current_version_number"),
            }
            for e in (env_list if isinstance(env_list, list) else [])
        ]

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    asyncio.run(run_audit())
