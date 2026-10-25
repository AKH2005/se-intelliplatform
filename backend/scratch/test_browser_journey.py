import asyncio
import selectors
import sys
import uuid
from pathlib import Path

backend_dir = str(Path(__file__).resolve().parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

loop = asyncio.SelectorEventLoop(selectors.SelectSelector())
asyncio.set_event_loop(loop)

from app.core.database import AsyncSessionLocal
from app.services.browser_journey_service import BrowserJourneyService
from app.services.context_engine import ProjectContextEngine
from app.services.development_version_service import DevelopmentVersionService
from app.services.workflow_service import WorkflowService
from app.browser.browser_testing_service import BrowserTestingService

async def main():
    async with AsyncSessionLocal() as session:
        proj_id = uuid.UUID("df084c2c-4fff-464f-84a3-9104f07f31c4")
        context_engine = ProjectContextEngine(session=session)
        version_service = DevelopmentVersionService(session=session)
        browser_testing_service = BrowserTestingService(session=session)
        workflow_service = WorkflowService(session=session, context_engine=context_engine, coordinator=None)
        
        service = BrowserJourneyService(
            session=session,
            context_engine=context_engine,
            version_service=version_service,
            browser_testing_service=browser_testing_service,
            workflow_service=workflow_service,
        )

        print(f"Triggering generate_and_execute_journeys for project {proj_id}...")
        res = await service.generate_and_execute_journeys(
            project_id=proj_id,
            execute_browser_tests=True,
            max_journeys=5,
        )
        print(f"Workflow Status: {res.status}")
        print(f"Stage Reached: {res.stage_reached}")
        print(f"Error: {res.error_message}")
        if res.candidate_suite:
            print(f"Candidate journeys: {len(res.candidate_suite.journeys)}")
            for j in res.candidate_suite.journeys:
                print(f"  - [{j.category}] {j.name} (steps: {len(j.steps)})")
        if res.test_definitions:
            print(f"Adapted test definitions: {len(res.test_definitions)}")
            for t in res.test_definitions:
                print(f"  - {t.test_id}: {t.name} -> {t.target_path}")
        if res.browser_test_run:
            print(f"Browser test run status: {res.browser_test_run.status}")
            print(f"Tests passed: {res.browser_test_run.tests_passed}, failed: {res.browser_test_run.tests_failed}")

if __name__ == "__main__":
    loop.run_until_complete(main())
