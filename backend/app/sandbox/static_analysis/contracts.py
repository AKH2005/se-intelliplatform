"""Static Analysis Contracts, Diagnostic Categories, and Unified Result Schemas."""

import enum
import uuid
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


# ==============================================================================
# 1. Diagnostic Severity & Categories
# ==============================================================================

class DiagnosticSeverity(str, enum.Enum):
    """Deterministic severity classification for static analysis findings."""

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class DiagnosticCategory(str, enum.Enum):
    """Functional classification of static analysis diagnostics."""

    SECURITY = "SECURITY"
    SYNTAX = "SYNTAX"
    LINT = "LINT"
    IMPORT = "IMPORT"
    DEPENDENCY = "DEPENDENCY"
    TEST = "TEST"
    STRUCTURE = "STRUCTURE"


class StaticAnalysisStatus(str, enum.Enum):
    """Deterministic terminal status of a static analysis pipeline run."""

    PASSED = "PASSED"
    ISSUES_FOUND = "ISSUES_FOUND"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    ANALYSIS_ERROR = "ANALYSIS_ERROR"


# ==============================================================================
# 2. Diagnostic Model
# ==============================================================================

class StaticDiagnostic(BaseModel):
    """Normalized diagnostic finding produced by any analyzer in the pipeline."""

    model_config = ConfigDict(extra="forbid")

    diagnostic_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Deterministic or unique identifier for the diagnostic finding",
    )
    category: DiagnosticCategory = Field(
        ...,
        description="Functional classification of the issue",
    )
    severity: DiagnosticSeverity = Field(
        ...,
        description="Deterministic severity level",
    )
    code: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Machine-readable rule or error identifier (e.g. 'F401', 'SEC_KEY', 'SYN_ERR')",
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Human-readable explanation of the finding",
    )
    file_path: str | None = Field(
        default=None,
        max_length=200,
        description="Relative project path where issue was found, if applicable",
    )
    line: int | None = Field(
        default=None,
        ge=1,
        description="1-indexed line number where finding occurs",
    )
    column: int | None = Field(
        default=None,
        ge=1,
        description="1-indexed column offset where finding occurs",
    )
    source: str = Field(
        ...,
        max_length=64,
        description="Originating analyzer component (e.g. 'ruff', 'ast', 'secret_scanner', 'dependency_analyzer')",
    )
    evidence: str | None = Field(
        default=None,
        max_length=500,
        description="Code snippet or contextual evidence supporting the finding",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional tool-specific metadata or URL references",
    )


# ==============================================================================
# 3. Request & Result Schemas
# ==============================================================================

class StaticAnalysisRequest(BaseModel):
    """API request payload triggering deterministic static analysis."""

    model_config = ConfigDict(extra="forbid")

    project_id: uuid.UUID = Field(
        ...,
        description="Target project UUID owning the artifact",
    )
    workflow_execution_id: uuid.UUID | None = Field(
        default=None,
        description="Optional specific workflow execution UUID to analyze",
    )


class StaticAnalysisResult(BaseModel):
    """Unified authoritative report aggregating all static analysis findings."""

    model_config = ConfigDict(extra="forbid")

    analysis_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        description="Unique correlation ID for this static analysis run",
    )
    project_id: uuid.UUID = Field(
        ...,
        description="Target project UUID",
    )
    workflow_execution_id: uuid.UUID | None = Field(
        default=None,
        description="Associated workflow execution UUID if artifact-backed",
    )
    status: StaticAnalysisStatus = Field(
        ...,
        description="Terminal status of the static analysis run",
    )
    duration_seconds: float = Field(
        default=0.0,
        ge=0.0,
        description="Total analysis runtime in seconds",
    )
    diagnostics: list[StaticDiagnostic] = Field(
        default_factory=list,
        description="Normalized, deduplicated list of findings",
    )
    files_analyzed: int = Field(
        default=0,
        ge=0,
        description="Count of project files successfully analyzed",
    )
    files_skipped: int = Field(
        default=0,
        ge=0,
        description="Count of files skipped (e.g. non-source assets)",
    )
    error_count: int = Field(
        default=0,
        ge=0,
        description="Total ERROR and CRITICAL severity diagnostics",
    )
    warning_count: int = Field(
        default=0,
        ge=0,
        description="Total WARNING severity diagnostics",
    )
    info_count: int = Field(
        default=0,
        ge=0,
        description="Total INFO severity diagnostics",
    )
    security_issue_count: int = Field(
        default=0,
        ge=0,
        description="Number of findings in SECURITY category",
    )
    syntax_error_count: int = Field(
        default=0,
        ge=0,
        description="Number of findings in SYNTAX category",
    )
    lint_issue_count: int = Field(
        default=0,
        ge=0,
        description="Number of findings in LINT category",
    )
    test_file_count: int = Field(
        default=0,
        ge=0,
        description="Number of test files discovered in project",
    )
    summary: str = Field(
        ...,
        description="Executive summary of static analysis findings",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Analyzer environment versions and diagnostics telemetry",
    )
