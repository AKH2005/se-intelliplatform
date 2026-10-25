"""Strongly Typed Contracts for Failure Analysis & Diagnostic Reasoning."""

import uuid
from enum import Enum
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from app.sandbox.contracts import ExecutionResult
from app.sandbox.static_analysis.contracts import (
    DiagnosticSeverity,
    StaticAnalysisResult,
)


class FailureSource(str, Enum):
    """Controlled categorization of failure origin sources."""

    AI_TEST = "AI_TEST"
    STATIC_ANALYSIS = "STATIC_ANALYSIS"
    SANDBOX = "SANDBOX"
    APPLICATION = "APPLICATION"
    VALIDATION = "VALIDATION"
    ENVIRONMENT = "ENVIRONMENT"
    DEPENDENCY = "DEPENDENCY"
    BROWSER = "BROWSER"


class FailureType(str, Enum):
    """Controlled taxonomy of diagnosable failures in generated projects."""

    SYNTAX_ERROR = "SYNTAX_ERROR"
    IMPORT_ERROR = "IMPORT_ERROR"
    DEPENDENCY_ERROR = "DEPENDENCY_ERROR"
    LINT_ERROR = "LINT_ERROR"
    TEST_FAILURE = "TEST_FAILURE"
    ASSERTION_FAILURE = "ASSERTION_FAILURE"
    TEST_ERROR = "TEST_ERROR"
    APPLICATION_ERROR = "APPLICATION_ERROR"
    STATIC_ANALYSIS_ISSUE = "STATIC_ANALYSIS_ISSUE"
    RUNTIME_ERROR = "RUNTIME_ERROR"
    TIMEOUT = "TIMEOUT"
    RESOURCE_LIMIT = "RESOURCE_LIMIT"
    SANDBOX_ERROR = "SANDBOX_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    ENVIRONMENT_ERROR = "ENVIRONMENT_ERROR"
    UNKNOWN = "UNKNOWN"


class ClaimType(str, Enum):
    """Epistemic classification of statements in the diagnosis."""

    FACT = "FACT"
    INTERPRETATION = "INTERPRETATION"
    RECOMMENDATION = "RECOMMENDATION"
    LIMITATION = "LIMITATION"


class FailureConfidence(str, Enum):
    """Bounded qualitative assessment of diagnostic certainty."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


class EvidenceReference(BaseModel):
    """Grounding reference pointing to deterministic static analysis or execution data."""

    model_config = ConfigDict(extra="forbid")

    evidence_id: str = Field(
        ...,
        description="Deterministic diagnostic_id or execution evidence identifier",
    )
    source: str = Field(
        ...,
        description="Originating source ('static_analysis', 'execution', 'ast', etc.)",
    )
    code: str | None = Field(
        default=None,
        description="Rule code (e.g. 'F821', 'DEP_MISSING', 'EXIT_CODE_1')",
    )
    file_path: str | None = Field(
        default=None,
        description="Relative file path where the evidence occurs",
    )
    line: int | None = Field(
        default=None,
        ge=1,
        description="Line coordinate if available",
    )
    snippet: str | None = Field(
        default=None,
        max_length=500,
        description="Code snippet or terminal line snippet",
    )
    description: str | None = Field(
        default=None,
        max_length=500,
        description="Brief description of the evidence finding",
    )


class DiagnosticClaim(BaseModel):
    """Classified claim distinguishing facts from interpretations and recommendations."""

    model_config = ConfigDict(extra="forbid")

    claim_type: ClaimType = Field(
        ...,
        description="Epistemic type of claim",
    )
    statement: str = Field(
        ...,
        min_length=5,
        max_length=1000,
        description="Clear statement of fact, interpretation, recommendation, or limitation",
    )
    evidence_ids: list[str] = Field(
        default_factory=list,
        description="List of evidence_ids supporting this claim (required for FACT and INTERPRETATION)",
    )


class RelevantSourceFile(BaseModel):
    """Labeled source code segment selected deterministically for diagnostic context."""

    model_config = ConfigDict(extra="forbid")

    path: str = Field(..., description="Project-relative file path")
    content: str = Field(..., description="Source code text with line annotations")
    line_start: int = Field(default=1, ge=1)
    line_end: int = Field(default=1, ge=1)
    selection_reason: str = Field(..., description="Why this file was included in context")


class FailureAnalysisInput(BaseModel):
    """Authoritative, bounded input package prepared for FailureAnalysisAgent."""

    model_config = ConfigDict(extra="forbid")

    project_id: uuid.UUID = Field(..., description="Target project UUID")
    workflow_execution_id: uuid.UUID | None = Field(
        default=None,
        description="Workflow execution UUID if artifact-backed",
    )
    execution_result: ExecutionResult | None = Field(
        default=None,
        description="Docker sandbox execution result if tests ran",
    )
    ai_test_execution_result: Any | None = Field(
        default=None,
        description="Authoritative AI test execution result if AI tests were executed",
    )
    ai_test_suite: Any | None = Field(
        default=None,
        description="Authoritative AI test suite containing test specifications and source mappings",
    )
    browser_test_run: Any | None = Field(
        default=None,
        description="Authoritative browser test run if browser validation was executed",
    )
    failure_source: FailureSource = Field(
        default=FailureSource.SANDBOX,
        description="Categorical source of the failure under analysis (AI_TEST, SANDBOX, STATIC_ANALYSIS, etc.)",
    )
    static_analysis_result: StaticAnalysisResult | None = Field(
        default=None,
        description="Static analysis report if static analysis ran",
    )
    relevant_files: list[RelevantSourceFile] = Field(
        default_factory=list,
        description="Deterministically selected source files and snippets",
    )
    all_project_files: list[str] = Field(
        default_factory=list,
        description="Complete list of valid file paths in generated project for reference validation",
    )
    available_diagnostic_ids: list[str] = Field(
        default_factory=list,
        description="All valid diagnostic UUIDs/IDs available for evidence grounding",
    )
    available_test_ids: list[str] = Field(
        default_factory=list,
        description="All valid test case IDs or test function names available for evidence grounding",
    )
    available_requirement_ids: list[str] = Field(
        default_factory=list,
        description="All valid requirement IDs from project context",
    )
    available_architecture_components: list[str] = Field(
        default_factory=list,
        description="All valid architecture component names from architecture context",
    )
    available_database_entities: list[str] = Field(
        default_factory=list,
        description="All valid database entity names from database context",
    )


UnifiedFailureAnalysisInput = FailureAnalysisInput


class FailureDiagnosis(BaseModel):
    """Structured, evidence-grounded failure diagnosis output emitted by FailureAnalysisAgent."""

    model_config = ConfigDict(extra="forbid")

    diagnosis_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        description="Unique identifier for this failure diagnosis",
    )
    failure_source: FailureSource | None = Field(
        default=None,
        description="Categorical origin source of the diagnosed failure (e.g. AI_TEST, SANDBOX, STATIC_ANALYSIS)",
    )
    failure_type: FailureType = Field(
        ...,
        description="Taxonomic classification of the primary failure",
    )
    title: str = Field(
        ...,
        min_length=5,
        max_length=200,
        description="Concise, technical headline summarizing the diagnosis",
    )
    summary: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Structured explanation of the failure",
    )
    root_cause: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="In-depth hypothesis explaining why the failure occurred",
    )
    severity: DiagnosticSeverity = Field(
        ...,
        description="Deterministic severity classification (CRITICAL, ERROR, WARNING, INFO)",
    )
    affected_files: list[str] = Field(
        default_factory=list,
        description="List of verified project file paths affected by the failure",
    )
    evidence: list[EvidenceReference] = Field(
        default_factory=list,
        description="Grounding evidence records tying the diagnosis to deterministic data",
    )
    claims: list[DiagnosticClaim] = Field(
        default_factory=list,
        description="Decomposed claims categorized by epistemic type",
    )
    requirement_links: list[str] = Field(
        default_factory=list,
        description="Verified requirement IDs correlated with this failure",
    )
    architecture_links: list[str] = Field(
        default_factory=list,
        description="Verified architecture component names correlated with this failure",
    )
    database_links: list[str] = Field(
        default_factory=list,
        description="Verified database entity names correlated with this failure",
    )
    suggested_remediation: str = Field(
        ...,
        min_length=10,
        max_length=3000,
        description="Conceptual explanation of the recommended fix (strictly conceptual guidance; no code snippets, 'replace ... with ...' directives, 'add this line' instructions, or diffs)",
    )
    limitations: list[str] = Field(
        default_factory=list,
        description="Explicit caveats regarding unobservable state or diagnostic bounds",
    )
    confidence: FailureConfidence = Field(
        default=FailureConfidence.MEDIUM,
        description="Qualitative assessment of diagnosis certainty based on available evidence",
    )
    model_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Provider, model, and token telemetry",
    )
