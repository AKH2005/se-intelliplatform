import asyncio
import uuid
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.core.database import AsyncSessionLocal
from app.models.project import Project
from app.models.requirement import Requirement, RequirementPriority, RequirementType, RequirementStatus
from app.services.workflow_service import WorkflowService
from app.schemas.workflow import WorkflowExecuteRequest
from app.workflows.contracts import WorkflowStatus

async def test_build():
    async with AsyncSessionLocal() as session:
        proj = Project(
            name="Test Taskflow",
            slug=f"test-taskflow-{uuid.uuid4().hex[:6]}",
            description="A modern task manager app",
            status="DRAFT",
            settings={},
        )
        session.add(proj)
        await session.commit()
        await session.refresh(proj)
        print(f"Created project: {proj.id}")

        reqs = [
            Requirement(
                project_id=proj.id,
                title="Task Management Dashboard",
                description="Dashboard displaying tasks with filter by active, completed, all, and a counter.",
                priority=RequirementPriority.HIGH,
                type=RequirementType.FUNCTIONAL,
                status=RequirementStatus.APPROVED,
            ),
            Requirement(
                project_id=proj.id,
                title="Create and Delete Tasks",
                description="Modal dialog to add tasks and ability to delete tasks.",
                priority=RequirementPriority.HIGH,
                type=RequirementType.FUNCTIONAL,
                status=RequirementStatus.APPROVED,
            ),
            Requirement(
                project_id=proj.id,
                title="Task State Toggle",
                description="Mark task as complete with strikethrough styling.",
                priority=RequirementPriority.MEDIUM,
                type=RequirementType.FUNCTIONAL,
                status=RequirementStatus.APPROVED,
            ),
            Requirement(
                project_id=proj.id,
                title="REST API & Persistence",
                description="FastAPI endpoints for tasks and SQLite database.",
                priority=RequirementPriority.HIGH,
                type=RequirementType.NON_FUNCTIONAL,
                status=RequirementStatus.APPROVED,
            ),
        ]
        session.add_all(reqs)
        await session.commit()

        wf_svc = WorkflowService(session)
        print("Executing code-generation-workflow...")
        res = await wf_svc.execute_workflow(
            "code-generation-workflow",
            WorkflowExecuteRequest(project_id=proj.id, options={"fail_fast": True}),
        )
        print(f"Workflow status: {res.status.value}")
        print(f"Artifacts: {list(res.artifacts.keys())}")
        if res.errors:
            print(f"Errors: {res.errors}")
        if res.status in (WorkflowStatus.COMPLETED, WorkflowStatus.PARTIAL_SUCCESS):
            print("SUCCESS! Code generation workflow completed!")
        else:
            print("FAILED workflow!")

if __name__ == "__main__":
    asyncio.run(test_build())
