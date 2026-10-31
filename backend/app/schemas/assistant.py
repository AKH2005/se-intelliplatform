"""Contracts and Domain Schemas for Phase 11I Intelli Assistant & Engineering Action Layer."""

import enum
import uuid
from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ActionCategory(str, enum.Enum):
    """Authoritative action classification categories."""

    READ_ONLY = "READ_ONLY"
    ANALYSIS = "ANALYSIS"
    GENERATION = "GENERATION"
    EXECUTION = "EXECUTION"
    MUTATING = "MUTATING"


class ActionStatus(str, enum.Enum):
    """Outcome status of an engineering action execution."""

    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PENDING_CONFIRMATION = "PENDING_CONFIRMATION"
    REJECTED = "REJECTED"
    INVALID_PARAMETERS = "INVALID_PARAMETERS"
    UNAUTHORIZED_TARGET = "UNAUTHORIZED_TARGET"


class AssistantRole(str, enum.Enum):
    """Message author role."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


# -----------------------------------------------------------------------------
# Parameter Schemas for all 26 Registered Actions
# -----------------------------------------------------------------------------

class EmptyParams(BaseModel):
    """Empty parameters schema for parameterless actions."""
    model_config = ConfigDict(extra="forbid")


class GetRequirementParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    requirement_id: str = Field(..., min_length=1, max_length=128)


class ListRequirementsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status_filter: str | None = Field(default=None, max_length=64)


class GetWorkflowHistoryParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    limit: int = Field(default=10, ge=1, le=100)


class VersionTargetParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version_id: uuid.UUID = Field(..., description="Target version UUID")


class OptionalVersionTargetParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version_id: uuid.UUID | None = Field(default=None, description="Optional target version UUID")


class GetVersionFileContentParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version_id: uuid.UUID = Field(..., description="Version UUID")
    file_path: str = Field(..., min_length=1, max_length=512, description="Project-relative file path")

    @field_validator("file_path")
    @classmethod
    def validate_file_path(cls, v: str) -> str:
        clean = v.replace("\\", "/").strip().lstrip("/")
        if ".." in clean.split("/"):
            raise ValueError("Path traversal ('..') is strictly prohibited.")
        if clean.startswith("/"):
            raise ValueError("Absolute paths are prohibited.")
        return clean


class CompareVersionsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    from_version_id: uuid.UUID = Field(..., description="Base version UUID")
    to_version_id: uuid.UUID = Field(..., description="Target version UUID")


class GetRemediationProposalParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    proposal_id: uuid.UUID | None = Field(default=None, description="Optional proposal UUID (defaults to latest)")


class AnalyzeFailureParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    workflow_execution_id: uuid.UUID | None = Field(default=None)
    suite_id: uuid.UUID | None = Field(default=None)


class CreateRemediationProposalParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    diagnosis_id: uuid.UUID = Field(..., description="Failure diagnosis UUID")
    workflow_execution_id: uuid.UUID | None = Field(default=None)
    guidance: str | None = Field(default=None, max_length=1000)


class RunAITestsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    suite_id: uuid.UUID | None = Field(default=None, description="AI test suite UUID")


class RunBrowserTestsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version_id: uuid.UUID | None = Field(default=None, description="Optional target version UUID")


class GetBrowserTestResultsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version_id: uuid.UUID | None = Field(default=None, description="Optional target version UUID")
    run_id: uuid.UUID | None = Field(default=None, description="Optional browser test run UUID")


class GenerateBrowserJourneysParams(BaseModel):
    """Parameters for GENERATE_BROWSER_JOURNEYS engineering action."""
    model_config = ConfigDict(extra="forbid")
    version_id: uuid.UUID | None = Field(default=None, description="Optional target development version UUID")
    execute_browser_tests: bool = Field(default=True, description="Whether to execute generated journeys in browser container runtime")
    max_journeys: int = Field(default=10, ge=1, le=10, description="Maximum number of journeys to generate (capped at 10)")


class ProposalTargetParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    proposal_id: uuid.UUID = Field(..., description="Remediation proposal UUID")


class RejectRemediationParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    proposal_id: uuid.UUID = Field(..., description="Remediation proposal UUID")
    reason: str | None = Field(default=None, max_length=500)


class ActivateVersionParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version_id: uuid.UUID = Field(..., description="Version UUID to activate")
    reason: str | None = Field(default=None, max_length=500)


class RollbackVersionParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target_version_id: uuid.UUID = Field(..., description="Target version UUID to roll back to")
    reason: str | None = Field(default=None, max_length=500)


class RunWorkflowParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    workflow_id: str = Field(..., min_length=1, max_length=128)
    workflow_input: dict[str, Any] = Field(default_factory=dict)


# -----------------------------------------------------------------------------
# Parameter Schemas for Phase 11L Testing Actions
# -----------------------------------------------------------------------------

class GetTestInventoryParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version_id: uuid.UUID | None = Field(default=None, description="Optional target version UUID")
    strict: bool = Field(default=True, description="Strict collision detection flag")


class GetCoverageReportParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version_id: uuid.UUID | None = Field(default=None, description="Optional target version UUID")


class AnalyzeCoverageGapsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version_id: uuid.UUID | None = Field(default=None, description="Optional target version UUID")


class AnalyzeRegressionImpactParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    base_version_id: uuid.UUID | None = Field(default=None, description="Optional base version UUID")
    target_version_id: uuid.UUID | None = Field(default=None, description="Optional target version UUID")
    changed_files: list[str] | None = Field(default=None, description="Optional list of changed file paths")


class PlanRegressionParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    base_version_id: uuid.UUID | None = Field(default=None, description="Optional base version UUID")
    target_version_id: uuid.UUID | None = Field(default=None, description="Optional target version UUID")
    changed_files: list[str] | None = Field(default=None, description="Optional list of changed file paths")
    mode: str = Field(default="SELECTIVE", description="Regression scope: SELECTIVE, BROAD, FULL")
    auto_broaden: bool = Field(default=False, description="Auto-broaden on uncertainty")


class ExecuteRegressionParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    base_version_id: uuid.UUID | None = Field(default=None, description="Optional base version UUID")
    target_version_id: uuid.UUID | None = Field(default=None, description="Optional target version UUID")
    changed_files: list[str] | None = Field(default=None, description="Optional list of changed file paths")
    mode: str = Field(default="SELECTIVE", description="Regression scope: SELECTIVE, BROAD, FULL")
    auto_broaden: bool = Field(default=False, description="Auto-broaden on uncertainty")
    skip_browser_tests: bool = Field(default=False, description="Whether to skip browser tier executions")
    browser_base_url: str | None = Field(default=None, description="Optional browser test base URL")

class GetEnvironmentsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")


class GetEnvironmentStatusParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    environment_type: str = Field(..., description="Target environment type: DEVELOPMENT, STAGING, or PRODUCTION")


class GetDeploymentHistoryParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    environment_type: str | None = Field(default=None, description="Optional environment type filter")
    limit: int = Field(default=10, ge=1, le=50)


class CheckPromotionEligibilityParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version_id: uuid.UUID = Field(..., description="Candidate DevelopmentVersion UUID to promote")
    target_environment: str = Field(..., description="Target environment type: STAGING or PRODUCTION")
    source_environment: str | None = Field(default=None, description="Optional source environment type")


class PromoteVersionParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version_id: uuid.UUID = Field(..., description="DevelopmentVersion UUID to promote")
    target_environment: str = Field(..., description="Target environment type: STAGING or PRODUCTION")
    source_environment: str | None = Field(default=None, description="Optional source environment type")
    notes: str | None = Field(default=None, max_length=512)


class DeployToEnvironmentParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    environment_type: str = Field(..., description="Target environment type: DEVELOPMENT, STAGING, or PRODUCTION")
    version_id: uuid.UUID = Field(..., description="DevelopmentVersion UUID to deploy")
    notes: str | None = Field(default=None, max_length=512)


class RollbackEnvironmentParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    environment_type: str = Field(..., description="Target environment type: STAGING or PRODUCTION")
    target_version_id: uuid.UUID = Field(..., description="Target version UUID to roll back to")
    reason: str = Field(..., min_length=1, max_length=512, description="Audit reason for rollback")


class FileChangeItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    file_path: str = Field(..., min_length=1, max_length=512, description="Project-relative file path")
    content: str = Field(default="", max_length=1_048_576, description="Full replacement content for the file")
    code_change: str | None = Field(default=None, description="Alternative key for replacement content")
    reason: str | None = Field(default=None, max_length=500, description="Reason for modifying this file")

    @model_validator(mode="before")
    @classmethod
    def populate_content(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if not data.get("content") and data.get("code_change"):
                data["content"] = data["code_change"]
            elif not data.get("content") and data.get("updated_code"):
                data["content"] = data["updated_code"]
        return data

    @field_validator("file_path")
    @classmethod
    def validate_file_path(cls, v: str) -> str:
        clean = v.replace("\\", "/").strip()
        if ":" in clean or clean.startswith("/"):
            raise ValueError("Absolute paths and drive letters are strictly prohibited.")
        clean = clean.lstrip("/")
        while clean.startswith("./"):
            clean = clean[2:]
        parts = [p for p in clean.split("/") if p and p != "."]
        if ".." in parts:
            raise ValueError("Path traversal ('..') is strictly prohibited.")
        return "/".join(parts)


class ApplyCodeChangeParams(BaseModel):
    model_config = ConfigDict(extra="ignore")
    version_id: uuid.UUID | int | str = Field(default="1", description="Parent development version UUID or version identifier (e.g. 4 or 'v4') being modified")
    changes: list[FileChangeItem] = Field(..., min_length=1, description="List of file changes to apply atomically")
    reason: str = Field(default="Code modification requested by user", min_length=1, max_length=500, description="Human-readable reason for the change set")


# -----------------------------------------------------------------------------
# Action Definition & Result DTOs
# -----------------------------------------------------------------------------


class ActionDefinition(BaseModel):
    """Metadata describing a registered platform engineering action."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    action_id: str
    description: str
    category: ActionCategory
    requires_confirmation: bool
    requires_execution: bool
    requires_llm: bool
    supported_targets: list[str] = Field(default_factory=list)
    parameter_schema: type[BaseModel]


class ActionResult(BaseModel):
    """Envelope returned upon action dispatch or execution."""

    model_config = ConfigDict(extra="forbid")

    action_id: str
    status: ActionStatus
    summary: str
    data: dict[str, Any] | None = None
    requires_confirmation: bool = False
    confirmation_token: str | None = None
    confirmation_prompt: str | None = None
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    audit_reference: str | None = None


# -----------------------------------------------------------------------------
# LLM Structured Response Schemas
# -----------------------------------------------------------------------------

class AssistantActionCandidate(BaseModel):
    """Candidate engineering action suggested by the conversational model."""

    model_config = ConfigDict(extra="ignore")

    action_id: str = Field(..., description="Registered action ID")
    target_id: str | None = Field(default=None, description="Optional entity UUID or slug")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Action-specific parameters")


class AssistantResponseSchema(BaseModel):
    """Strict structured generation contract returned by AbstractLLMProvider for assistant turns."""

    model_config = ConfigDict(extra="ignore")

    message: str = Field(..., min_length=1, description="Conversational explanation or answer for the user")
    suggested_action: AssistantActionCandidate | None = Field(
        default=None,
        description="Optional action candidate chosen strictly from the registered action catalog",
    )
    referenced_entity_type: str | None = Field(
        default=None,
        description="Type of entity discussed: version, diagnosis, proposal, workflow, requirement",
    )
    referenced_entity_id: str | None = Field(
        default=None,
        description="UUID or ID of the referenced entity",
    )
    persona: str | None = Field(
        default=None,
        description="Active assistant persona: 'IntelliGuide' or 'IntelliDev'",
    )
    intent: str | None = Field(
        default=None,
        description="Classified user intent: CODE_EXPLANATION, DEBUGGING, etc.",
    )


# -----------------------------------------------------------------------------
# Anti-Replay Confirmation Token Contract
# -----------------------------------------------------------------------------

class ActionConfirmationTokenPayload(BaseModel):
    """Payload bound into a single-use anti-replay confirmation token."""

    model_config = ConfigDict(extra="forbid")

    token_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    project_id: uuid.UUID
    conversation_id: uuid.UUID
    action_id: str
    target_id: str | None = None
    parameters_hash: str
    issued_to_user_id: str = "assistant_user"
    expires_at: datetime
    consumed_at: datetime | None = None


# -----------------------------------------------------------------------------
# Assistant Bounded Context Contract
# -----------------------------------------------------------------------------

class AssistantContext(BaseModel):
    """Bounded, canonical snapshot passed to the Assistant LLM (target: <= 2,000 tokens)."""

    model_config = ConfigDict(extra="forbid")

    project_id: uuid.UUID
    project_name: str
    project_slug: str
    project_status: str
    active_version_id: uuid.UUID | str | None = None
    active_version_number: int | None = None
    active_version_status: str | None = None
    active_version_hash: str | None = None
    verification_summary: str | None = None
    total_requirements_count: int = 0
    recent_failure_title: str | None = None
    recent_failure_severity: str | None = None
    active_remediation_proposal_id: str | None = None
    active_remediation_status: str | None = None
    recent_change_summary: str | None = None
    latest_browser_status: str | None = None
    latest_browser_summary: str | None = None
    active_executions_summary: str | None = None
    environments_summary: str | None = None
    polyglot_languages_summary: str | None = None
    project_description: str | None = None
    technology_stack: dict[str, Any] | None = None
    key_requirements: list[dict[str, str]] | None = None
    files_manifest_summary: list[dict[str, Any]] | None = None
    retrieved_files: list[dict[str, Any]] | None = None
    missing_files_requested: list[str] | None = None
    supplied_error_text: str | None = None
    detected_intent: str | None = None
    active_persona: str | None = None
    preview_runtime_status: str | None = None
    preview_runtime_mode: str | None = None
    preview_runtime_port: int | None = None
    preview_active_project_id: str | None = None
    preview_diagnostics_summary: str | None = None


# -----------------------------------------------------------------------------
# REST API Request & Response DTOs
# -----------------------------------------------------------------------------

class CreateConversationRequest(BaseModel):
    """Payload to initialize a new Assistant conversation."""

    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, max_length=256, description="Optional conversation title")


class SendMessageRequest(BaseModel):
    """User input sent to the Assistant."""

    model_config = ConfigDict(extra="forbid")

    content: str = Field(..., min_length=1, max_length=4000, description="User question or instruction")
    conversation_id: uuid.UUID | None = Field(default=None, description="Optional existing conversation UUID")
    explicit_file_paths: list[str] | None = Field(default=None, description="Optional specific file paths to inspect")
    error_message: str | None = Field(default=None, max_length=4000, description="Optional explicit error message or stack trace")

    @field_validator("content")
    @classmethod
    def validate_content_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Message content cannot be empty or whitespace only.")
        return v



class ConfirmActionRequest(BaseModel):
    """Payload sent by user to confirm a pending mutating action."""

    model_config = ConfigDict(extra="forbid")

    confirmation_token: str = Field(..., min_length=10, description="Anti-replay confirmation token")


class DirectExecuteActionRequest(BaseModel):
    """Direct execution request bypassing natural-language turn."""

    model_config = ConfigDict(extra="forbid")

    action_id: str = Field(..., description="Action ID from 28-action registry")
    target_id: str | None = Field(default=None)
    parameters: dict[str, Any] = Field(default_factory=dict)
    conversation_id: uuid.UUID | None = Field(default=None)


class AssistantMessageResponse(BaseModel):
    """DTO representing a message in an Assistant conversation."""

    model_config = ConfigDict(extra="forbid")

    message_id: uuid.UUID
    conversation_id: uuid.UUID
    role: AssistantRole
    content: str
    action_id: str | None = None
    action_status: ActionStatus | None = None
    action_result: ActionResult | None = None
    referenced_entity_type: str | None = None
    referenced_entity_id: str | None = None
    created_at: datetime


class AssistantConversationResponse(BaseModel):
    """DTO representing an Assistant conversation thread."""

    model_config = ConfigDict(extra="forbid")

    conversation_id: uuid.UUID
    project_id: uuid.UUID
    user_id: uuid.UUID | None = None
    title: str
    messages: list[AssistantMessageResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class AssistantConversationListResponse(BaseModel):
    """List of conversations for a project."""

    model_config = ConfigDict(extra="forbid")

    items: list[AssistantConversationResponse]
    total: int
