"""Remediation API Endpoints: Human-in-the-Loop Proposal, Approval, Application & Verification."""

import uuid
from typing import Annotated, Any
from fastapi import APIRouter, Depends, Path, status
from pydantic import BaseModel, ConfigDict, Field

from app.agents.remediation.contracts import (
    RemediationProposal,
    RemediationVerificationResult,
)
from app.agents.remediation.service import RemediationService
from app.api.dependencies import get_remediation_service

router = APIRouter()


class CreateProposalRequest(BaseModel):
    """Payload to trigger remediation proposal generation."""

    model_config = ConfigDict(extra="forbid")

    workflow_execution_id: uuid.UUID | None = Field(
        default=None,
        description="Optional specific workflow execution to remediate. Defaults to latest.",
    )


class RejectProposalRequest(BaseModel):
    """Payload to reject a remediation proposal."""

    model_config = ConfigDict(extra="forbid")

    reason: str | None = Field(
        default=None,
        description="Optional human-specified rationale for rejection.",
    )


class ApplyRemediationResponse(BaseModel):
    """Response returned upon applying an approved remediation proposal."""

    proposal: RemediationProposal
    verification: RemediationVerificationResult


@router.post(
    "/proposals",
    response_model=RemediationProposal,
    status_code=status.HTTP_201_CREATED,
    summary="Create structured remediation proposal from authoritative diagnosis",
    description=(
        "Consumes authoritative FailureDiagnosis and CodeGeneration artifact to propose "
        "a minimal, structured patch. Status begins at AWAITING_APPROVAL. The patch is NOT applied."
    ),
)
async def create_proposal(
    project_id: Annotated[uuid.UUID, Path(description="Project UUID")],
    service: Annotated[RemediationService, Depends(get_remediation_service)],
    request: CreateProposalRequest | None = None,
) -> RemediationProposal:
    """Generate and validate a new remediation proposal without applying it."""
    wf_id = request.workflow_execution_id if request else None
    return await service.create_proposal(
        project_id=project_id,
        workflow_execution_id=wf_id,
    )


@router.get(
    "/proposals/latest",
    response_model=RemediationProposal | None,
    status_code=status.HTTP_200_OK,
    summary="Get latest active remediation proposal for a project",
    description="Retrieves the current active remediation proposal stored in the project workflow artifacts.",
)
async def get_latest_proposal(
    project_id: Annotated[uuid.UUID, Path(description="Project UUID")],
    service: Annotated[RemediationService, Depends(get_remediation_service)],
) -> RemediationProposal | None:
    """Retrieve the latest remediation proposal for the project, if one exists."""
    target_exec = await service._resolve_target_execution(project_id)
    artifacts = target_exec.artifacts or {}
    prop_data = artifacts.get("remediation_proposal")
    if not prop_data:
        return None
    return RemediationProposal.model_validate(prop_data)


@router.get(
    "/proposals/{proposal_id}",
    response_model=RemediationProposal,
    status_code=status.HTTP_200_OK,
    summary="Retrieve remediation proposal by ID",
    description="Fetches a remediation proposal by its unique identifier.",
)
async def get_proposal(
    project_id: Annotated[uuid.UUID, Path(description="Project UUID")],
    proposal_id: Annotated[uuid.UUID, Path(description="Proposal UUID")],
    service: Annotated[RemediationService, Depends(get_remediation_service)],
) -> RemediationProposal:
    """Retrieve proposal by ID."""
    return await service.get_proposal(project_id=project_id, proposal_id=proposal_id)


@router.post(
    "/proposals/{proposal_id}/approve",
    response_model=RemediationProposal,
    status_code=status.HTTP_200_OK,
    summary="Explicitly approve remediation proposal",
    description=(
        "Transition proposal status from AWAITING_APPROVAL to APPROVED. "
        "Mandatory authorization step prior to patch application."
    ),
)
async def approve_proposal(
    project_id: Annotated[uuid.UUID, Path(description="Project UUID")],
    proposal_id: Annotated[uuid.UUID, Path(description="Proposal UUID")],
    service: Annotated[RemediationService, Depends(get_remediation_service)],
) -> RemediationProposal:
    """Explicit human approval of a remediation proposal."""
    return await service.approve_proposal(project_id=project_id, proposal_id=proposal_id)


@router.post(
    "/proposals/{proposal_id}/reject",
    response_model=RemediationProposal,
    status_code=status.HTTP_200_OK,
    summary="Explicitly reject remediation proposal",
    description="Transition proposal status to REJECTED. Rejection is final.",
)
async def reject_proposal(
    project_id: Annotated[uuid.UUID, Path(description="Project UUID")],
    proposal_id: Annotated[uuid.UUID, Path(description="Proposal UUID")],
    service: Annotated[RemediationService, Depends(get_remediation_service)],
    request: RejectProposalRequest | None = None,
) -> RemediationProposal:
    """Explicit human rejection of a remediation proposal."""
    reason = request.reason if request else None
    return await service.reject_proposal(
        project_id=project_id,
        proposal_id=proposal_id,
        reason=reason,
    )


@router.post(
    "/proposals/{proposal_id}/apply",
    response_model=ApplyRemediationResponse,
    status_code=status.HTTP_200_OK,
    summary="Apply an approved patch in controlled workspace and run verification",
    description=(
        "Applies the approved patch ONLY if proposal is in APPROVED status. "
        "Rejects any unapproved or rejected proposal. "
        "Preserves original artifact, creates new version, runs static analysis and sandbox tests."
    ),
)
async def apply_proposal(
    project_id: Annotated[uuid.UUID, Path(description="Project UUID")],
    proposal_id: Annotated[uuid.UUID, Path(description="Proposal UUID")],
    service: Annotated[RemediationService, Depends(get_remediation_service)],
) -> ApplyRemediationResponse:
    """Apply approved proposal and verify regressions."""
    prop, verification = await service.apply_proposal(
        project_id=project_id,
        proposal_id=proposal_id,
    )
    return ApplyRemediationResponse(
        proposal=prop,
        verification=verification,
    )
