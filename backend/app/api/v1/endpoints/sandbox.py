"""Sandbox Execution and Status API Endpoints."""

import uuid
from typing import Annotated, Any
from fastapi import APIRouter, Depends, Path, status

from app.api.dependencies import get_sandbox_service
from app.sandbox.contracts import ExecutionRequest, ExecutionResult
from app.sandbox.service import SandboxService

router = APIRouter()


@router.get(
    "/status",
    response_model=dict[str, Any],
    summary="Get sandbox runtime status and availability",
    description="Returns runtime isolation diagnostics, Docker daemon reachability, and active security policy.",
)
async def get_sandbox_status(
    project_id: Annotated[uuid.UUID, Path(description="Project UUID")],
    service: Annotated[SandboxService, Depends(get_sandbox_service)],
) -> dict[str, Any]:
    """Get sandbox runtime health and capability diagnostics."""
    return await service.get_status()


@router.post(
    "/execute",
    response_model=ExecutionResult,
    status_code=status.HTTP_200_OK,
    summary="Execute tests or static validation against generated code in isolated sandbox",
    description=(
        "Executes a controlled test runner (pytest) or static AST validation in a hardened container sandbox. "
        "Arbitrary shell commands, host paths, custom Docker options, and internet access are strictly prohibited."
    ),
)
async def execute_sandbox(
    project_id: Annotated[uuid.UUID, Path(description="Project UUID")],
    request: ExecutionRequest,
    service: Annotated[SandboxService, Depends(get_sandbox_service)],
) -> ExecutionResult:
    """Execute validation or tests against project code artifact in the sandbox."""
    if request.project_id != project_id:
        request = request.model_copy(update={"project_id": project_id})

    return await service.execute(request)
