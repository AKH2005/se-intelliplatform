"""Remediation Proposal, Approval, and Patch Application Contracts for Phase 11E.

Guarantees:
- Strongly-typed models for proposed changes, proposals, approvals, and verification.
- Enforces strict human-in-the-loop approval state machine (AWAITING_APPROVAL -> APPROVED -> APPLIED).
- Strictly prevents autonomous or unapproved patch application.
"""

import enum
import uuid
from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from app.agents.failure_analysis.contracts import FailureDiagnosis, RelevantSourceFile
from app.sandbox.contracts import ExecutionResult
from app.sandbox.static_analysis.contracts import DiagnosticSeverity, StaticAnalysisResult


# ==============================================================================
# 1. Enumerations
# ==============================================================================

class ChangeOperation(str, enum.Enum):
    """Permitted filesystem operations on generated project artifacts."""

    MODIFY = "MODIFY"
    ADD = "ADD"
    DELETE = "DELETE"


class RemediationProposalStatus(str, enum.Enum):
    """Strict lifecycle states for human-in-the-loop patch proposals."""

    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    APPLIED = "APPLIED"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"
    VERIFIED = "VERIFIED"
    EXPIRED = "EXPIRED"


class RiskLevel(str, enum.Enum):
    """Categorized assessment of remediation modification blast radius."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


# ==============================================================================
# 2. Change & Proposal Models
# ==============================================================================

class ProposedChange(BaseModel):
    """Individual file modification proposal."""

    model_config = ConfigDict(extra="forbid")

    file_path: str = Field(
        ...,
        min_length=1,
        max_length=260,
        description="Project-relative normalized path to the target file",
    )
    operation: ChangeOperation = Field(
        ...,
        description="Operation type: MODIFY, ADD, or DELETE",
    )
    original_region: str | None = Field(
        default=None,
        max_length=50000,
        description="Exact original code snippet or lines to replace/delete (None for ADD)",
    )
    proposed_region: str = Field(
        default="",
        max_length=50000,
        description="Proposed replacement code or new file content (empty for DELETE)",
    )
    reason: str = Field(
        ...,
        min_length=5,
        max_length=1000,
        description="Technical justification for this specific change",
    )
    evidence_ids: list[str] = Field(
        default_factory=list,
        description="Diagnostic or execution evidence IDs that this change resolves",
    )


class RemediationProposalCandidate(BaseModel):
    """Raw structured candidate returned by the LLM before backend validation & diff generation."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(
        ...,
        min_length=5,
        max_length=200,
        description="Headline summarizing the proposed fix",
    )
    summary: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Overview of how the proposal resolves the identified diagnosis",
    )
    rationale: str = Field(
        ...,
        min_length=10,
        max_length=3000,
        description="Detailed explanation of the change strategy and architectural preservation",
    )
    changes: list[ProposedChange] = Field(
        ...,
        min_length=1,
        max_length=5,
        description="List of structured file modifications",
    )
    expected_effect: str = Field(
        ...,
        min_length=5,
        max_length=1000,
        description="Expected behavior of tests and static analysis after applying this fix",
    )
    verification_plan: str = Field(
        ...,
        min_length=5,
        max_length=1000,
        description="Plan for verifying the fix (e.g. specific test target, ruff check)",
    )
    risk_level: RiskLevel = Field(
        default=RiskLevel.LOW,
        description="Risk level assessment of potential side effects",
    )
    requirement_links: list[str] = Field(
        default_factory=list,
        description="Upstream requirement IDs correlated with this change",
    )
    architecture_links: list[str] = Field(
        default_factory=list,
        description="Upstream architecture components preserved or modified",
    )
    database_links: list[str] = Field(
        default_factory=list,
        description="Upstream database entities touched",
    )


class RemediationProposal(BaseModel):
    """Complete, validated remediation proposal ready for human review and approval."""

    model_config = ConfigDict(extra="forbid")

    proposal_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        description="Unique UUID identifying this remediation proposal",
    )
    diagnosis_id: str = Field(
        ...,
        description="Correlation ID of the originating FailureDiagnosis",
    )
    project_id: uuid.UUID = Field(
        ...,
        description="Target project UUID",
    )
    workflow_execution_id: uuid.UUID | None = Field(
        default=None,
        description="Originating workflow execution UUID",
    )
    title: str = Field(..., min_length=5, max_length=200)
    summary: str = Field(..., min_length=10, max_length=2000)
    rationale: str = Field(..., min_length=10, max_length=3000)
    changes: list[ProposedChange] = Field(..., min_length=1)
    affected_files: list[str] = Field(default_factory=list)
    unified_diff: str = Field(
        default="",
        description="Authoritative unified diff generated deterministically by backend",
    )
    expected_effect: str = Field(..., min_length=5, max_length=1000)
    verification_plan: str = Field(..., min_length=5, max_length=1000)
    risk_level: RiskLevel = Field(default=RiskLevel.LOW)
    status: RemediationProposalStatus = Field(
        default=RemediationProposalStatus.AWAITING_APPROVAL,
        description="Lifecycle status in human approval gate",
    )
    requirement_links: list[str] = Field(default_factory=list)
    architecture_links: list[str] = Field(default_factory=list)
    database_links: list[str] = Field(default_factory=list)
    model_metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when proposal was generated and validated (UTC)",
    )
    approved_at: datetime | None = Field(default=None)
    rejected_at: datetime | None = Field(default=None)
    applied_at: datetime | None = Field(default=None)
    rejection_reason: str | None = Field(default=None)
    parent_artifact_version: int = Field(default=1)
    resulting_artifact_version: int | None = Field(default=None)


class RemediationProposalInput(BaseModel):
    """Authoritative input context for the RemediationProposalAgent."""

    model_config = ConfigDict(extra="forbid")

    project_id: uuid.UUID = Field(..., description="Target project UUID")
    workflow_execution_id: uuid.UUID | None = Field(default=None)
    diagnosis: FailureDiagnosis = Field(..., description="Authoritative failure diagnosis")
    static_analysis_result: StaticAnalysisResult | None = Field(default=None)
    execution_result: ExecutionResult | None = Field(default=None)
    relevant_files: list[RelevantSourceFile] = Field(default_factory=list)
    project_manifest: list[str] = Field(default_factory=list)
    available_requirement_ids: list[str] = Field(default_factory=list)
    available_architecture_components: list[str] = Field(default_factory=list)
    available_database_entities: list[str] = Field(default_factory=list)
    current_artifact_version: int = Field(default=1)


class RemediationVerificationResult(BaseModel):
    """Deterministic outcome of post-application static analysis and sandbox verification."""

    model_config = ConfigDict(extra="forbid")

    verification_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    proposal_id: uuid.UUID = Field(...)
    status: RemediationProposalStatus = Field(
        ...,
        description="Outcome: VERIFIED (passed all criteria) or VERIFICATION_FAILED",
    )
    static_analysis_passed: bool = Field(...)
    sandbox_passed: bool = Field(...)
    browser_passed: bool | None = Field(
        default=None,
        description="Deterministic outcome of post-application browser smoke verification (None if no browser suite configured)",
    )
    browser_test_run: Any | None = Field(
        default=None,
        description="BrowserTestRun output if browser regression was executed",
    )
    resolved_diagnostic_codes: list[str] = Field(default_factory=list)
    new_critical_or_error_diagnostics: list[str] = Field(default_factory=list)
    summary: str = Field(...)
    static_analysis_result: StaticAnalysisResult | None = Field(default=None)
    execution_result: ExecutionResult | None = Field(default=None)
    verified_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
