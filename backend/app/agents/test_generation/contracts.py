"""Contracts, Data Models, and Conservative Limits for AI Test Generation."""

import enum
import uuid
from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from app.sandbox.contracts import ExecutionStatus
from app.sandbox.static_analysis.contracts import StaticAnalysisResult
from app.agents.failure_analysis.contracts import FailureDiagnosis

# ==============================================================================
# 1. Conservative Platform Bounds for AI Test Generation
# ==============================================================================

MAX_TESTS: int = 10
MAX_TEST_FILES: int = 5
MAX_INDIVIDUAL_TEST_CODE_BYTES: int = 10 * 1024  # 10 KB per test
MAX_TOTAL_TEST_CODE_BYTES: int = 50 * 1024        # 50 KB total test code
MAX_NAME_LENGTH: int = 120
MAX_DESCRIPTION_LENGTH: int = 500


# ==============================================================================
# 2. Enumerations
# ==============================================================================

class TestCategory(str, enum.Enum):
    """Functional classification of AI-generated tests."""

    __test__ = False

    HAPPY_PATH = "HAPPY_PATH"
    EDGE_CASE = "EDGE_CASE"
    VALIDATION = "VALIDATION"
    ERROR_HANDLING = "ERROR_HANDLING"
    BUSINESS_LOGIC = "BUSINESS_LOGIC"
    API_BEHAVIOR = "API_BEHAVIOR"


# ==============================================================================
# 3. Test Specification Models
# ==============================================================================

class GeneratedTest(BaseModel):
    """Strongly-typed individual test definition with code and traceability."""

    __test__ = False
    model_config = ConfigDict(extra="forbid")

    test_id: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Unique identifier for the test case (e.g. 'TEST-001')",
    )
    name: str = Field(
        ...,
        min_length=3,
        max_length=MAX_NAME_LENGTH,
        pattern=r"^test_[a-zA-Z0-9_]+$",
        description="Python test function name (must begin with 'test_')",
    )
    description: str = Field(
        ...,
        min_length=5,
        max_length=MAX_DESCRIPTION_LENGTH,
        description="Human-readable description of what this test verifies",
    )
    category: TestCategory = Field(
        ...,
        description="Categorical scope of the test",
    )
    target_file: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Relative project path of the file under test (e.g. 'app/calculator.py')",
    )
    target_symbol: str | None = Field(
        default=None,
        max_length=120,
        description="Target function, method, or class under test (e.g. 'average')",
    )
    requirement_ids: list[str] = Field(
        default_factory=list,
        description="Requirement UUIDs or titles this test traces to",
    )
    architecture_component: str | None = Field(
        default=None,
        max_length=120,
        description="Architecture component this test targets",
    )
    rationale: str = Field(
        ...,
        min_length=5,
        max_length=1000,
        description="Engineering explanation for why this test scenario is necessary",
    )
    code: str = Field(
        ...,
        min_length=10,
        description="Python test function code containing assertions",
    )
    expected_behavior: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="Expected assertion outcome or system behavior",
    )


# ==============================================================================
# 4. LLM Candidate Schemas (Stage 1)
# ==============================================================================

class GeneratedTestCandidate(BaseModel):
    """Raw candidate test returned by LLM before deterministic validation."""

    __test__ = False
    model_config = ConfigDict(extra="ignore")

    test_id: str
    name: str
    description: str = "AI-generated test scenario"
    category: str = "HAPPY_PATH"
    target_file: str
    target_symbol: str | None = None
    requirement_ids: list[str] = Field(default_factory=list)
    architecture_component: str | None = None
    rationale: str = "Verifies specified software component behavior"
    code: str
    expected_behavior: str = "Assertions pass successfully"


class AITestSuiteCandidate(BaseModel):
    """Raw test suite candidate returned by LLM before deterministic validation."""

    __test__ = False
    model_config = ConfigDict(extra="ignore")

    summary: str = "AI-generated test suite for software artifact"
    tests: list[GeneratedTestCandidate] = Field(default_factory=list)


# ==============================================================================
# 5. Authoritative Test Suite & Input Schemas (Stage 2)
# ==============================================================================

class TestGenerationInput(BaseModel):
    """Authoritative, bounded input provided to TestGenerationAgent."""

    __test__ = False
    model_config = ConfigDict(extra="forbid")

    project_id: uuid.UUID = Field(
        ...,
        description="Target project UUID",
    )
    workflow_execution_id: uuid.UUID | None = Field(
        default=None,
        description="Optional workflow execution UUID",
    )
    manifest: list[str] = Field(
        ...,
        description="List of verified relative file paths in the generated project",
    )
    files: dict[str, str] = Field(
        ...,
        description="Bounded map of relative file paths to their source contents",
    )
    available_requirement_ids: list[str] = Field(
        default_factory=list,
        description="Valid requirement UUIDs and titles for traceability validation",
    )
    available_architecture_components: list[str] = Field(
        default_factory=list,
        description="Valid architecture component names",
    )
    available_database_entities: list[str] = Field(
        default_factory=list,
        description="Valid database entity names",
    )
    static_analysis_result: StaticAnalysisResult | None = Field(
        default=None,
        description="Deterministic static analysis findings for context",
    )
    failure_diagnosis: FailureDiagnosis | None = Field(
        default=None,
        description="Optional failure diagnosis from previous runs",
    )
    allowed_categories: list[TestCategory] = Field(
        default_factory=lambda: list(TestCategory),
        description="Allowed test categories for this generation session",
    )


class AITestSuite(BaseModel):
    """Authoritative, validated AI test suite ready for ephemeral sandbox execution."""

    __test__ = False
    model_config = ConfigDict(extra="forbid")

    suite_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        description="Unique identifier for this test suite",
    )
    project_id: uuid.UUID = Field(
        ...,
        description="Target project UUID",
    )
    workflow_execution_id: uuid.UUID | None = Field(
        default=None,
        description="Associated workflow execution UUID",
    )
    summary: str = Field(
        ...,
        min_length=5,
        max_length=1000,
        description="Summary of the generated test suite",
    )
    tests: list[GeneratedTest] = Field(
        ...,
        min_length=1,
        max_length=MAX_TESTS,
        description="Validated test definitions",
    )
    test_count: int = Field(
        ...,
        ge=1,
        le=MAX_TESTS,
        description="Total number of tests in the suite",
    )
    requirement_traceability: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Map of requirement ID to matching test IDs",
    )
    source_artifact_reference: str = Field(
        default="code_generation",
        description="Identifier of source artifact this suite tests",
    )
    static_analysis_reference: str | None = Field(
        default=None,
        description="Reference to static analysis result used during generation",
    )
    test_files: dict[str, str] = Field(
        ...,
        description="Compiled executable test files (e.g. {'tests/test_ai_generated.py': '...'}})",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the test suite was created and validated",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Generation and validation metadata (no secrets)",
    )


# ==============================================================================
# 6. Ephemeral Sandbox Execution Models
# ==============================================================================

class AITestCaseResult(BaseModel):
    """Individual test outcome parsed from sandbox pytest output."""

    __test__ = False
    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        ...,
        description="Test function name (e.g. 'test_calculator_valid_average')",
    )
    status: str = Field(
        ...,
        description="Outcome: 'PASSED', 'FAILED', 'ERROR', or 'SKIPPED'",
    )
    duration_seconds: float = Field(
        default=0.0,
        ge=0.0,
        description="Test runtime in seconds",
    )
    message: str | None = Field(
        default=None,
        description="Failure trace or skip reason, if any",
    )


class AITestExecutionRequest(BaseModel):
    """Request payload to execute an AI test suite inside the Docker sandbox."""

    __test__ = False
    model_config = ConfigDict(extra="forbid")

    project_id: uuid.UUID = Field(
        ...,
        description="Target project UUID",
    )
    workflow_execution_id: uuid.UUID | None = Field(
        default=None,
        description="Associated workflow execution UUID",
    )
    suite_id: uuid.UUID = Field(
        ...,
        description="Identifier of the validated AITestSuite to execute",
    )
    timeout_seconds: int = Field(
        default=30,
        ge=5,
        le=60,
        description="Execution timeout in seconds",
    )


class AITestExecutionResult(BaseModel):
    """Authoritative outcome of executing an AI test suite inside Docker sandbox."""

    __test__ = False
    model_config = ConfigDict(extra="forbid")

    execution_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        description="Unique correlation ID for this test execution",
    )
    suite_id: uuid.UUID = Field(
        ...,
        description="ID of the executed AITestSuite",
    )
    project_id: uuid.UUID = Field(
        ...,
        description="Target project UUID",
    )
    workflow_execution_id: uuid.UUID | None = Field(
        default=None,
        description="Associated workflow execution UUID",
    )
    status: ExecutionStatus = Field(
        ...,
        description="Overall terminal execution status",
    )
    exit_code: int | None = Field(
        default=None,
        description="Pytest process exit code",
    )
    duration_seconds: float = Field(
        default=0.0,
        ge=0.0,
        description="Execution duration in seconds",
    )
    tests_total: int = Field(
        default=0,
        ge=0,
        description="Total test cases executed",
    )
    tests_passed: int = Field(
        default=0,
        ge=0,
        description="Passed test count",
    )
    tests_failed: int = Field(
        default=0,
        ge=0,
        description="Failed test count",
    )
    tests_skipped: int = Field(
        default=0,
        ge=0,
        description="Skipped test count",
    )
    stdout: str = Field(
        default="",
        description="Captured standard output (bounded)",
    )
    stderr: str = Field(
        default="",
        description="Captured standard error (bounded)",
    )
    failure_summaries: list[str] = Field(
        default_factory=list,
        description="Concise diagnostic failure summaries parsed from pytest",
    )
    test_results: list[AITestCaseResult] = Field(
        default_factory=list,
        description="Individual test outcomes",
    )
    executed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Execution timestamp",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Execution metadata and sandbox environment diagnostics",
    )
