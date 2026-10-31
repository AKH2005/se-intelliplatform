"""Forensic test script to verify the entire 12-step safe code modification lifecycle on the live DB."""

import asyncio
import json
import uuid
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.project import Project
from app.models.development_version import DevelopmentVersion, DevelopmentVersionStatus
from app.core.security import create_access_token
from sqlalchemy import select


async def run_lifecycle_verification():
    transport = ASGITransport(app=app)
    results = {}

    async with AsyncSessionLocal() as session:
        # Get MiniTask and owner token
        res_p = await session.execute(select(Project).where(Project.name.ilike("%MiniTask%")))
        minitask = res_p.scalar_one_or_none()
        assert minitask is not None, "MiniTask project not found"
        proj_id = str(minitask.id)
        owner_id = minitask.owner_id

        res_u = await session.execute(select(User).where(User.id == owner_id))
        owner = res_u.scalar_one_or_none()
        token = create_access_token({"sub": str(owner.id)})

        # Get active version
        active_ver_id = (minitask.settings or {}).get("active_version_id")
        res_v = await session.execute(
            select(DevelopmentVersion).where(DevelopmentVersion.id == uuid.UUID(active_ver_id))
        )
        active_ver = res_v.scalar_one_or_none()
        assert active_ver is not None, "Active version not found"
        current_version_num = active_ver.version_number

    auth_headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Step 1: Create a conversation
        conv_resp = await client.post(
            f"/api/v1/projects/{proj_id}/assistant/conversations",
            headers=auth_headers,
        )
        assert conv_resp.status_code == 201, f"Failed to create conversation: {conv_resp.text}"
        conv_id = conv_resp.json()["conversation_id"]
        results["1_conversation_created"] = conv_id

        # Step 2: Propose code change via assistant action execution endpoint
        # Action candidate payload
        candidate_params = {
            "version_id": str(active_ver.id),
            "reason": "Add priority badge color documentation to README.md",
            "changes": [
                {
                    "file_path": "README.md",
                    "content": "# MiniTask — React Task Manager\n\nUpdated with Priority Badge Color Documentation.\n\n- Urgent: Red\n- High: Orange\n- Normal: Blue\n- Low: Gray\n",
                }
            ],
        }

        # Step 3: Trigger execute_action with APPLY_CODE_CHANGE
        # Test endpoint /api/v1/projects/{proj_id}/assistant/actions/execute
        exec_action_resp = await client.post(
            f"/api/v1/projects/{proj_id}/assistant/actions/execute",
            headers=auth_headers,
            json={
                "action_id": "APPLY_CODE_CHANGE",
                "parameters": candidate_params,
                "conversation_id": conv_id,
            },
        )
        assert exec_action_resp.status_code == 200, f"Action execution failed: {exec_action_resp.text}"
        exec_data = exec_action_resp.json()
        results["2_pending_confirmation"] = {
            "status": exec_data.get("status"),
            "requires_confirmation": exec_data.get("requires_confirmation"),
            "has_token": bool(exec_data.get("confirmation_token")),
            "files_diff": [
                {
                    "path": f.get("path"),
                    "status": f.get("status"),
                    "diff_lines": f.get("diff", "").splitlines()[:4],
                }
                for f in exec_data.get("data", {}).get("files", [])
            ],
        }

        confirmation_token = exec_data.get("confirmation_token")
        assert confirmation_token is not None, "Missing confirmation token"

        # Step 4: Test security - path traversal rejection
        bad_traversal_resp = await client.post(
            f"/api/v1/projects/{proj_id}/assistant/actions/execute",
            headers=auth_headers,
            json={
                "action_id": "APPLY_CODE_CHANGE",
                "parameters": {
                    "version_id": str(active_ver.id),
                    "reason": "Path traversal attack",
                    "changes": [{"file_path": "../../evil.py", "content": "malicious"}],
                },
                "conversation_id": conv_id,
            },
        )
        results["3_path_traversal_rejected"] = bad_traversal_resp.status_code in (400, 422) or (
            exec_data.get("status") == "INVALID_PARAMETERS"
        )

        # Step 5: Test security - invalid syntax rejection (Python syntax error)
        bad_syntax_resp = await client.post(
            f"/api/v1/projects/{proj_id}/assistant/actions/execute",
            headers=auth_headers,
            json={
                "action_id": "APPLY_CODE_CHANGE",
                "parameters": {
                    "version_id": str(active_ver.id),
                    "reason": "Broken python code",
                    "changes": [{"file_path": "app/syntax_error.py", "content": "def broken_code(\n"}],
                },
                "conversation_id": conv_id,
            },
        )
        # Should be rejected either at execution or confirmation
        results["4_syntax_error_rejected"] = bad_syntax_resp.status_code in (400, 422) or (
            bad_syntax_resp.json().get("status") in ("INVALID_PARAMETERS", "FAILED")
        )

        # Step 6: Confirm the valid action using confirmation token
        confirm_resp = await client.post(
            f"/api/v1/projects/{proj_id}/assistant/actions/confirm",
            headers=auth_headers,
            json={"confirmation_token": confirmation_token},
        )
        assert confirm_resp.status_code == 200, f"Confirm failed: {confirm_resp.text}"
        confirm_data = confirm_resp.json()
        results["5_confirm_action_success"] = {
            "status": confirm_data.get("status"),
            "summary": confirm_data.get("summary"),
            "new_version": confirm_data.get("data", {}).get("new_version"),
        }

        # Step 7: Test anti-replay - token reuse rejection
        replay_resp = await client.post(
            f"/api/v1/projects/{proj_id}/assistant/actions/confirm",
            headers=auth_headers,
            json={"confirmation_token": confirmation_token},
        )
        results["6_token_replay_prevented"] = replay_resp.status_code == 409  # ConflictError

        # Step 8: Verify in database that new version was created and previous superseded
        async with AsyncSessionLocal() as session:
            res_p_updated = await session.execute(select(Project).where(Project.id == minitask.id))
            p_updated = res_p_updated.scalar_one()
            new_active_id = (p_updated.settings or {}).get("active_version_id")

            res_new_v = await session.execute(
                select(DevelopmentVersion).where(DevelopmentVersion.id == uuid.UUID(new_active_id))
            )
            new_v = res_new_v.scalar_one()

            res_old_v = await session.execute(
                select(DevelopmentVersion).where(DevelopmentVersion.id == active_ver.id)
            )
            old_v = res_old_v.scalar_one()

            results["7_database_versioning"] = {
                "old_version_number": old_v.version_number,
                "old_version_status": old_v.status.value,
                "new_version_number": new_v.version_number,
                "new_version_status": new_v.status.value,
                "parent_version_id": str(new_v.parent_version_id),
                "is_monotonically_increasing": new_v.version_number == current_version_num + 1,
                "is_previous_superseded": old_v.status == DevelopmentVersionStatus.SUPERSEDED,
            }

        # Step 9: Verify Code Studio endpoint returns the updated README.md from new active version
        files_resp = await client.get(f"/api/v1/projects/{proj_id}/files", headers=auth_headers)
        f_json = files_resp.json()
        readme_entry = next((f for f in f_json.get("files", []) if f.get("path") == "README.md"), None)

        readme_content_resp = await client.get(
            f"/api/v1/projects/{proj_id}/files/content?file_path=README.md",
            headers=auth_headers,
        )
        readme_content = readme_content_resp.json().get("content", "")

        results["8_code_studio_sync"] = {
            "active_version_number": f_json.get("version_number"),
            "readme_present": readme_entry is not None,
            "contains_new_content": "Priority Badge Color Documentation" in readme_content,
        }

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    asyncio.run(run_lifecycle_verification())
