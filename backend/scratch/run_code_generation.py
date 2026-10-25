import asyncio, sys
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
import uuid
from app.core.database import AsyncSessionLocal
from app.services.context_engine import ProjectContextEngine
from app.workflows.coordinator import WorkflowCoordinator
from app.services.workflow_service import WorkflowService
from app.api.dependencies import get_agent_executor, agent_registry
from app.agents.registry import register_all_agents
from app.schemas.workflow import WorkflowExecuteRequest
from app.services.development_version_service import DevelopmentVersionService

async def main():
    register_all_agents(agent_registry)
    project_id = uuid.UUID('df084c2c-4fff-464f-84a3-9104f07f31c4')
    async with AsyncSessionLocal() as session:
        engine = ProjectContextEngine(session=session)
        executor = get_agent_executor()
        coordinator = WorkflowCoordinator(executor=executor, registry=agent_registry)
        service = WorkflowService(session=session, context_engine=engine, coordinator=coordinator)
        
        req = WorkflowExecuteRequest(project_id=project_id, options={'fail_fast': True})
        print("Executing code-generation-workflow...")
        res = await service.execute_workflow('code-generation-workflow', req)
        print("Workflow status:", res.status)
        print("Total steps:", len(res.step_results))
        for step in res.step_results:
            print(f" - Step '{step.step_id}': status={step.status}, error={step.error}")

        if res.status.value in ("COMPLETED", "PARTIAL_SUCCESS"):
            # Register DevelopmentVersion
            print("Registering DevelopmentVersion from workflow execution...")
            dev_service = DevelopmentVersionService(session=session)
            dev_ver = await dev_service.register_version_from_workflow(
                project_id=project_id,
                workflow_execution_id=res.workflow_execution_id,
                artifact_key="code-generation",
                source_reason="INITIAL_GENERATION",
            )
            await session.commit()
            print(f"Created DevelopmentVersion v{dev_ver.version_number}: id={dev_ver.id}, status={dev_ver.status}, files={dev_ver.file_count}")

asyncio.run(main())
