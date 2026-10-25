"""Browser Testing REST API Endpoints for Phase 11J (Stage 5).

Exposes project-scoped browser test execution and telemetry retrieval
backed strictly by BrowserTestingService. Directly invoking Docker, constructing
arbitrary shell commands, or passing untrusted container options is strictly prohibited.
"""

import logging
import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, Path, Query, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_browser_testing_service, get_db, get_development_version_service
from app.browser.browser_testing_service import BrowserTestingService
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.project import Project
from app.schemas.browser_testing import BrowserTestRun, RunBrowserTestsRequest
from app.services.development_version_service import DevelopmentVersionService

logger = logging.getLogger(__name__)

router = APIRouter()


async def _verify_project_exists(session: AsyncSession, project_id: uuid.UUID) -> None:
    """Verify project exists or raise RFC7807 NotFoundError."""
    stmt = select(Project.id).where(Project.id == project_id)
    res = await session.execute(stmt)
    if not res.scalar_one_or_none():
        raise NotFoundError("Project", str(project_id))


@router.post(
    "/tests/run",
    response_model=BrowserTestRun,
    status_code=status.HTTP_200_OK,
    summary="Execute deterministic browser smoke tests",
    description=(
        "Executes deterministic UI smoke tests in an isolated Playwright container "
        "against the application runtime on an internal bridge network. "
        "Arbitrary Docker parameters, shell commands, and internet navigation are strictly forbidden."
    ),
)
async def run_browser_tests(
    project_id: Annotated[uuid.UUID, Path(description="Project UUID")],
    request: RunBrowserTestsRequest,
    browser_service: Annotated[BrowserTestingService, Depends(get_browser_testing_service)],
    version_service: Annotated[DevelopmentVersionService, Depends(get_development_version_service)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> BrowserTestRun:
    """Run deterministic browser smoke tests against project version."""
    await _verify_project_exists(session, project_id)

    # 1. Deterministic version resolution
    target_version_id = request.development_version_id
    if target_version_id:
        # Must verify version belongs strictly to this project
        ver = await version_service.get_version(project_id, target_version_id)
        if not ver:
            raise NotFoundError("DevelopmentVersion", str(target_version_id))
    else:
        # Resolve active version for project
        active_ver = await version_service.get_active_version(project_id)
        if not active_ver:
            raise ConflictError(
                "No active development version found for project. Explicit development_version_id is required."
            )
        target_version_id = active_ver.version_id

    logger.info(
        f"Initiating browser smoke tests for project '{project_id}', version '{target_version_id}'"
    )

    # 2. Invoke BrowserTestingService (never Docker directly)
    return await browser_service.execute_browser_tests(
        project_id=project_id,
        version_id=target_version_id,
    )


@router.get(
    "/tests/latest",
    response_model=BrowserTestRun,
    status_code=status.HTTP_200_OK,
    summary="Get latest browser test execution result",
    description="Retrieves the most recent deterministic browser test run for the project or version.",
)
async def get_latest_browser_test_run(
    project_id: Annotated[uuid.UUID, Path(description="Project UUID")],
    browser_service: Annotated[BrowserTestingService, Depends(get_browser_testing_service)],
    session: Annotated[AsyncSession, Depends(get_db)],
    version_id: Annotated[uuid.UUID | None, Query(description="Optional target version UUID filter")] = None,
) -> BrowserTestRun:
    """Retrieve latest browser test run for project or specific version."""
    await _verify_project_exists(session, project_id)

    run = await browser_service.get_latest_browser_test_run(
        project_id=project_id,
        version_id=version_id,
    )
    if not run:
        raise NotFoundError("BrowserTestRun", f"No browser test run found for project {project_id}.")
    return run


@router.get(
    "/tests/{run_id}",
    response_model=BrowserTestRun,
    status_code=status.HTTP_200_OK,
    summary="Get browser test execution result by run ID",
    description="Retrieves a specific browser test execution result by its unique UUID within project scope.",
)
async def get_browser_test_run_by_id(
    project_id: Annotated[uuid.UUID, Path(description="Project UUID")],
    run_id: Annotated[uuid.UUID, Path(description="Browser test run UUID")],
    browser_service: Annotated[BrowserTestingService, Depends(get_browser_testing_service)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> BrowserTestRun:
    """Retrieve specific browser test run by run ID."""
    await _verify_project_exists(session, project_id)

    run = await browser_service.get_browser_test_run(
        project_id=project_id,
        run_id=run_id,
    )
    if not run:
        raise NotFoundError("BrowserTestRun", str(run_id))
    return run


@router.get(
    "/tests/{run_id}/screenshots/{filename}",
    response_class=FileResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve scoped browser test screenshot",
    description="Securely streams a browser screenshot artifact with strict path traversal validation.",
)
async def get_browser_screenshot(
    project_id: Annotated[uuid.UUID, Path(description="Project UUID")],
    run_id: Annotated[uuid.UUID, Path(description="Browser test run UUID")],
    filename: Annotated[str, Path(description="Screenshot image filename")],
    browser_service: Annotated[BrowserTestingService, Depends(get_browser_testing_service)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> FileResponse:
    """Stream authorized screenshot artifact binary."""
    await _verify_project_exists(session, project_id)

    safe_path = browser_service.get_screenshot_path(
        project_id=project_id,
        run_id=run_id,
        filename=filename,
    )
    media_type = "image/png"
    if safe_path.suffix.lower() == ".webp":
        media_type = "image/webp"
    elif safe_path.suffix.lower() in (".jpg", ".jpeg"):
        media_type = "image/jpeg"

    return FileResponse(
        path=str(safe_path),
        media_type=media_type,
        filename=safe_path.name,
    )


@router.get(
    "/artifacts/{run_id}/{filename}",
    response_class=FileResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def get_browser_artifact_alias(
    project_id: Annotated[uuid.UUID, Path(description="Project UUID")],
    run_id: Annotated[uuid.UUID, Path(description="Browser test run UUID")],
    filename: Annotated[str, Path(description="Screenshot image filename")],
    browser_service: Annotated[BrowserTestingService, Depends(get_browser_testing_service)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> FileResponse:
    """Alias for screenshot streaming."""
    return await get_browser_screenshot(
        project_id=project_id,
        run_id=run_id,
        filename=filename,
        browser_service=browser_service,
        session=session,
    )
