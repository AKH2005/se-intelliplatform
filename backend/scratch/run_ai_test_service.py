import asyncio
import selectors
import uuid

loop = asyncio.SelectorEventLoop(selectors.SelectSelector())
asyncio.set_event_loop(loop)

from app.core.database import AsyncSessionLocal
from app.services.workflow_service import WorkflowService
from app.services.context_engine import ProjectContextEngine
from app.api.dependencies import get_agent_executor
from app.agents.test_generation.service import AITestService

async def main():
    async with AsyncSessionLocal() as session:
        proj_id = uuid.UUID("df084c2c-4fff-464f-84a3-9104f07f31c4")
        context_engine = ProjectContextEngine(session=session)
        workflow_service = WorkflowService(
            session=session,
            context_engine=context_engine,
            coordinator=None,
        )
        service = AITestService(
            session=session,
            workflow_service=workflow_service,
            executor=get_agent_executor(),
            context_engine=context_engine,
        )
        print("Calling service.generate_tests...")
        suite = await service.generate_tests(project_id=proj_id)
        print(f"Generated suite {suite.suite_id} with {suite.test_count} tests!")
        for t in suite.test_cases:
            print(f" - [{t.category}] {t.test_name} ({t.target_file})")

if __name__ == "__main__":
    loop.run_until_complete(main())
