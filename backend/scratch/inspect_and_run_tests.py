import asyncio
import selectors
import uuid
import sys
from pathlib import Path

# Add backend to sys.path
backend_dir = str(Path(__file__).resolve().parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

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
        suite_id = uuid.UUID("f2619bb5-a205-4923-b396-9e5c82a62655")
        suite = await service.get_test_suite(proj_id, suite_id)
        print(f"Loaded suite {suite.suite_id} with {suite.test_count} tests:")
        for t in suite.tests:
            print(f"  - [{t.category}] {t.name} ({t.target_file})")
        print("\nTest files:")
        for path, code in suite.test_files.items():
            print(f"File: {path}")
            print(code)
            print("-" * 40)

        print("\nNow executing tests via service.execute_tests...")
        result = await service.execute_tests(project_id=proj_id, suite_id=suite_id, timeout_seconds=30)
        print(f"Execution Status: {result.status}")
        print(f"Exit code: {result.exit_code}")
        print(f"Duration: {result.duration_seconds}s")
        print(f"Passed: {result.tests_passed}, Failed: {result.tests_failed}, Total: {result.tests_total}")
        print(f"STDOUT:\n{result.stdout}")
        print(f"STDERR:\n{result.stderr}")
        if result.failure_summaries:
            print("Failure summaries:")
            for s in result.failure_summaries:
                print(f"  - {s}")

if __name__ == "__main__":
    loop.run_until_complete(main())
