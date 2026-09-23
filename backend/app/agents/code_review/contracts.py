"""Contracts and Data Models for AI Code Review Agent."""

import enum
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


MAX_FILES: int = 10
MAX_TOTAL_SIZE_BYTES: int = 100 * 1024  # 100 KB
MAX_LINES_PER_FILE: int = 1000
SUPPORTED_LANGUAGES: set[str] = {"python", "py"}


class FindingSeverity(str, enum.Enum):
    """Execution priority tier for code review findings."""

    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class FindingCategory(str, enum.Enum):
    """Categorical classification of review findings."""

    CORRECTNESS = "CORRECTNESS"
    SECURITY = "SECURITY"
    PERFORMANCE = "PERFORMANCE"
    MAINTAINABILITY = "MAINTAINABILITY"
    READABILITY = "READABILITY"
    ERROR_HANDLING = "ERROR_HANDLING"
    ARCHITECTURE = "ARCHITECTURE"


class FindingSource(str, enum.Enum):
    """Provenance origin of code review findings."""

    STATIC_ANALYSIS = "STATIC_ANALYSIS"
    AI_REVIEW = "AI_REVIEW"
    HYBRID = "HYBRID"


class CodeFile(BaseModel):
    """In-memory source code file representation."""

    model_config = ConfigDict(extra="forbid")

    file_path: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Relative project path of the file (e.g. 'app/services/auth.py')",
    )
    language: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Programming language identifier (e.g. 'python', 'py')",
    )
    content: str = Field(
        ...,
        min_length=1,
        description="UTF-8 source code content",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional auxiliary file metadata",
    )


class CodeReviewInput(BaseModel):
    """Input payload envelope for CodeReviewAgent."""

    model_config = ConfigDict(extra="forbid")

    files: list[CodeFile] = Field(
        ...,
        min_length=1,
        max_length=MAX_FILES,
        description=f"Collection of files to review (max {MAX_FILES} files)",
    )
    review_scope: str | None = Field(
        default=None,
        max_length=500,
        description="Optional review focus or specific instructions",
    )


class CodeReviewFinding(BaseModel):
    """Discrete code review issue or recommendation with verified provenance."""

    model_config = ConfigDict(extra="forbid")

    finding_id: str = Field(
        ...,
        min_length=1,
        description="Unique identifier for the finding within the review (e.g. 'CR-001')",
    )
    file_path: str = Field(
        ...,
        min_length=1,
        description="Relative path of the target file containing the finding",
    )
    line_start: int = Field(
        ...,
        ge=1,
        description="1-indexed starting line number of the code segment",
    )
    line_end: int = Field(
        ...,
        ge=1,
        description="1-indexed ending line number of the code segment (>= line_start)",
    )
    severity: FindingSeverity = Field(
        ...,
        description="Severity level of the finding",
    )
    category: FindingCategory = Field(
        ...,
        description="Category classification of the finding",
    )
    source: FindingSource = Field(
        ...,
        description="Provenance source of the finding (STATIC_ANALYSIS, AI_REVIEW, HYBRID)",
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Concise descriptive title of the finding",
    )
    description: str = Field(
        ...,
        min_length=1,
        description="Detailed explanation of the issue, risk, or observation",
    )
    evidence: str = Field(
        ...,
        min_length=1,
        description="Exact code snippet or offending expression from the reviewed source",
    )
    recommendation: str = Field(
        ...,
        min_length=1,
        description="Actionable suggestion or refactoring guidance to resolve the finding",
    )
    rule_id: str | None = Field(
        default=None,
        description="Deterministic static analysis rule identifier if applicable (e.g. 'AST-SYNTAX-ERROR')",
    )


class CodeReviewSummary(BaseModel):
    """Authoritative, backend-calculated code review metrics."""

    model_config = ConfigDict(extra="forbid")

    files_analyzed_count: int = Field(
        ...,
        ge=0,
        description="Total number of files analyzed",
    )
    total_findings: int = Field(
        ...,
        ge=0,
        description="Total number of validated findings across all files",
    )
    findings_by_severity: dict[str, int] = Field(
        default_factory=dict,
        description="Counts of findings grouped by severity (INFO, LOW, MEDIUM, HIGH, CRITICAL)",
    )
    findings_by_category: dict[str, int] = Field(
        default_factory=dict,
        description="Counts of findings grouped by category",
    )
    static_findings_count: int = Field(
        ...,
        ge=0,
        description="Number of findings produced deterministically via static analysis",
    )
    ai_findings_count: int = Field(
        ...,
        ge=0,
        description="Number of findings produced via LLM contextual review",
    )


DEFAULT_CODE_REVIEW_LIMITATIONS: list[str] = [
    (
        "AI code review findings are advisory and probabilistic. They should be verified by "
        "qualified software engineers before merging or deploying."
    ),
    (
        "The agent performs strictly in-memory static AST and lexical inspection; "
        "it does NOT execute code, run tests, or evaluate runtime performance."
    ),
    (
        "Deterministic static analysis in Phase 8.1 is limited to Python standard library "
        "AST rules and lexical secret detection; it does not replace full CI/CD linting suites."
    ),
    (
        "Secret detection utilizes deterministic regular expression pattern matching and is not "
        "an exhaustive guarantee against all possible forms of credentials or proprietary tokens."
    ),
    (
        "Architectural alignment observations depend on the quality and completeness of active "
        "project requirements provided in canonical Project Context."
    ),
]


class CodeReviewCandidate(BaseModel):
    """Raw structured candidate generated by the LLM before deterministic backend merge and validation."""

    model_config = ConfigDict(extra="forbid")

    summary: str = Field(
        ...,
        description="High-level narrative summarizing the code review assessment",
    )
    findings: list[CodeReviewFinding] = Field(
        default_factory=list,
        description="Proposed review findings derived from contextual analysis",
    )


class CodeReviewOutput(BaseModel):
    """Authoritative, validated structured result emitted by CodeReviewAgent."""

    model_config = ConfigDict(extra="forbid")

    agent_id: str = Field(
        default="code-review",
        description="Executing agent identifier",
    )
    agent_version: str = Field(
        default="1.0.0",
        description="Agent implementation semantic version",
    )
    summary: str = Field(
        ...,
        description="Authoritative executive summary of the code review",
    )
    files_reviewed: list[str] = Field(
        ...,
        description="List of relative file paths that were analyzed",
    )
    findings: list[CodeReviewFinding] = Field(
        ...,
        description="Validated collection of code review findings with verified line and evidence bounds",
    )
    metrics: CodeReviewSummary = Field(
        ...,
        description="Deterministic backend-calculated review summary statistics",
    )
    limitations: list[str] = Field(
        default_factory=lambda: list(DEFAULT_CODE_REVIEW_LIMITATIONS),
        description="Acknowledged limitations of the code review process",
    )
