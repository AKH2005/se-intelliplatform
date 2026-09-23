"""Unit tests for Phase 8.1 Code Review Agent contracts and deterministic validation."""

from datetime import datetime, timezone
import uuid
import pytest
from pydantic import ValidationError

from app.agents.code_review.contracts import (
    DEFAULT_CODE_REVIEW_LIMITATIONS,
    MAX_FILES,
    MAX_LINES_PER_FILE,
    MAX_TOTAL_SIZE_BYTES,
    CodeFile,
    CodeReviewCandidate,
    CodeReviewFinding,
    CodeReviewInput,
    CodeReviewOutput,
    CodeReviewSummary,
    FindingCategory,
    FindingSeverity,
    FindingSource,
)
from app.agents.code_review.validation import (
    validate_code_review_input,
    validate_code_review_output,
)
from app.agents.exceptions import AgentValidationError
from app.models.requirement import RequirementPriority, RequirementStatus, RequirementType
from app.schemas.context import ProjectContextResponse, RequirementStatistics
from app.schemas.project import ProjectResponse
from app.schemas.requirement import RequirementResponse


@pytest.fixture
def sample_context():
    project_id = uuid.uuid4()
    req_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    project = ProjectResponse(
        id=project_id,
        name="CodeReviewDemo",
        slug="codereviewdemo",
        description="Demo project for testing code review",
        created_at=now,
        updated_at=now,
    )
    req = RequirementResponse(
        id=req_id,
        project_id=project_id,
        title="Secure Auth",
        description="Must enforce secure password hashing.",
        type=RequirementType.FUNCTIONAL,
        priority=RequirementPriority.HIGH,
        status=RequirementStatus.APPROVED,
        is_archived=False,
        created_at=now,
        updated_at=now,
    )
    stats = RequirementStatistics(
        total_requirements=1,
        active_requirements=1,
        functional_count=1,
        non_functional_count=0,
        constraint_count=0,
        by_priority={"HIGH": 1},
        by_status={"APPROVED": 1},
        completion_percentage=0.0,
    )
    return ProjectContextResponse(
        project=project,
        requirements=[req],
        statistics=stats,
        context_version=1,
        generated_at=now,
    )


def test_code_file_valid():
    cf = CodeFile(
        file_path="app/main.py",
        language="python",
        content="print('hello')",
    )
    assert cf.file_path == "app/main.py"
    assert cf.language == "python"
    assert cf.content == "print('hello')"


def test_code_file_empty_path_fails():
    with pytest.raises(ValidationError):
        CodeFile(file_path="", language="python", content="print('hello')")


def test_code_file_empty_content_fails():
    with pytest.raises(ValidationError):
        CodeFile(file_path="app/main.py", language="python", content="")


def test_code_file_forbid_extra():
    with pytest.raises(ValidationError):
        CodeFile(file_path="app/main.py", language="python", content="x=1", unexpected_field="foo")


def test_code_review_input_valid():
    inp = CodeReviewInput(
        files=[
            CodeFile(file_path="a.py", language="python", content="x = 1\n"),
            CodeFile(file_path="b.py", language="python", content="y = 2\n"),
        ],
        review_scope="Focus on security",
    )
    assert len(inp.files) == 2
    assert inp.review_scope == "Focus on security"


def test_code_review_input_empty_files_fails():
    with pytest.raises(ValidationError):
        CodeReviewInput(files=[])


def test_code_review_input_max_files_exceeded_fails():
    files = [
        CodeFile(file_path=f"file_{i}.py", language="python", content="x = 1\n")
        for i in range(MAX_FILES + 1)
    ]
    with pytest.raises(ValidationError):
        CodeReviewInput(files=files)


def test_validate_input_path_traversal():
    inp = CodeReviewInput(
        files=[CodeFile(file_path="../secret.py", language="python", content="x = 1\n")]
    )
    with pytest.raises(AgentValidationError, match="path traversal"):
        validate_code_review_input(inp)


def test_validate_input_absolute_path():
    inp = CodeReviewInput(
        files=[CodeFile(file_path="/etc/passwd.py", language="python", content="x = 1\n")]
    )
    with pytest.raises(AgentValidationError, match="Absolute paths"):
        validate_code_review_input(inp)


def test_validate_input_windows_drive():
    inp = CodeReviewInput(
        files=[CodeFile(file_path="C:/app/main.py", language="python", content="x = 1\n")]
    )
    with pytest.raises(AgentValidationError, match="Drive letters"):
        validate_code_review_input(inp)


def test_validate_input_unsupported_language():
    inp = CodeReviewInput(
        files=[CodeFile(file_path="app/main.js", language="javascript", content="console.log('hi');\n")]
    )
    with pytest.raises(AgentValidationError, match="Unsupported language"):
        validate_code_review_input(inp)


def test_validate_input_duplicate_paths():
    inp = CodeReviewInput(
        files=[
            CodeFile(file_path="app/main.py", language="python", content="x = 1\n"),
            CodeFile(file_path="app/main.py", language="python", content="x = 2\n"),
        ]
    )
    with pytest.raises(AgentValidationError, match="Duplicate file path"):
        validate_code_review_input(inp)


def test_validate_input_max_lines_exceeded():
    long_content = "\n".join(f"line_{i} = {i}" for i in range(MAX_LINES_PER_FILE + 5))
    inp = CodeReviewInput(
        files=[CodeFile(file_path="app/long.py", language="python", content=long_content)]
    )
    with pytest.raises(AgentValidationError, match="Line count"):
        validate_code_review_input(inp)


def test_validate_input_max_size_exceeded():
    # Construct content > 100 KB
    huge_content = "a" * (MAX_TOTAL_SIZE_BYTES + 10)
    inp = CodeReviewInput(
        files=[CodeFile(file_path="app/huge.py", language="python", content=huge_content)]
    )
    with pytest.raises(AgentValidationError, match="Cumulative source code size"):
        validate_code_review_input(inp)


def test_validate_output_valid(sample_context):
    source = "def add(a, b):\n    return a + b\n"
    finding = CodeReviewFinding(
        finding_id="CR-001",
        file_path="calc.py",
        line_start=1,
        line_end=1,
        severity=FindingSeverity.INFO,
        category=FindingCategory.READABILITY,
        source=FindingSource.AI_REVIEW,
        title="Add Type Hints",
        description="Function lacks type annotations.",
        evidence="def add(a, b):",
        recommendation="Annotate parameters with types.",
        rule_id=None,
    )
    summary = CodeReviewSummary(
        files_analyzed_count=1,
        total_findings=1,
        findings_by_severity={"INFO": 1, "LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0},
        findings_by_category={"READABILITY": 1, "CORRECTNESS": 0, "SECURITY": 0, "PERFORMANCE": 0, "MAINTAINABILITY": 0, "ERROR_HANDLING": 0, "ARCHITECTURE": 0},
        static_findings_count=0,
        ai_findings_count=1,
    )
    output = CodeReviewOutput(
        summary="Code review completed successfully.",
        files_reviewed=["calc.py"],
        findings=[finding],
        metrics=summary,
        limitations=list(DEFAULT_CODE_REVIEW_LIMITATIONS),
    )
    res = validate_code_review_output(output, sample_context, file_contents_map={"calc.py": source})
    assert res.is_valid is True
    assert len(res.errors) == 0


def test_validate_output_empty_summary(sample_context):
    output = CodeReviewOutput(
        summary="  ",
        files_reviewed=["calc.py"],
        findings=[],
        metrics=CodeReviewSummary(
            files_analyzed_count=1,
            total_findings=0,
            findings_by_severity={"INFO": 0, "LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0},
            findings_by_category={"READABILITY": 0, "CORRECTNESS": 0, "SECURITY": 0, "PERFORMANCE": 0, "MAINTAINABILITY": 0, "ERROR_HANDLING": 0, "ARCHITECTURE": 0},
            static_findings_count=0,
            ai_findings_count=0,
        ),
        limitations=list(DEFAULT_CODE_REVIEW_LIMITATIONS),
    )
    res = validate_code_review_output(output, sample_context)
    assert res.is_valid is False
    assert any("summary cannot be empty" in e for e in res.errors)


def test_validate_output_line_bounds_exceeded(sample_context):
    source = "x = 1\ny = 2\n"  # 2 lines
    finding = CodeReviewFinding(
        finding_id="CR-001",
        file_path="calc.py",
        line_start=1,
        line_end=5,  # Exceeds total lines
        severity=FindingSeverity.LOW,
        category=FindingCategory.MAINTAINABILITY,
        source=FindingSource.AI_REVIEW,
        title="Invalid Line",
        description="Refers to non-existent lines.",
        evidence="x = 1",
        recommendation="Fix lines",
    )
    summary = CodeReviewSummary(
        files_analyzed_count=1,
        total_findings=1,
        findings_by_severity={"INFO": 0, "LOW": 1, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0},
        findings_by_category={"READABILITY": 0, "CORRECTNESS": 0, "SECURITY": 0, "PERFORMANCE": 0, "MAINTAINABILITY": 1, "ERROR_HANDLING": 0, "ARCHITECTURE": 0},
        static_findings_count=0,
        ai_findings_count=1,
    )
    output = CodeReviewOutput(
        summary="Review complete.",
        files_reviewed=["calc.py"],
        findings=[finding],
        metrics=summary,
        limitations=list(DEFAULT_CODE_REVIEW_LIMITATIONS),
    )
    res = validate_code_review_output(output, sample_context, file_contents_map={"calc.py": source})
    assert res.is_valid is False
    assert any("exceeds total file lines" in e for e in res.errors)


def test_validate_output_mismatched_evidence(sample_context):
    source = "def compute():\n    return 42\n"
    finding = CodeReviewFinding(
        finding_id="CR-001",
        file_path="calc.py",
        line_start=1,
        line_end=1,
        severity=FindingSeverity.LOW,
        category=FindingCategory.MAINTAINABILITY,
        source=FindingSource.AI_REVIEW,
        title="Bad Evidence",
        description="Evidence does not appear in line 1.",
        evidence="def hallucinated_func():",
        recommendation="Fix evidence",
    )
    summary = CodeReviewSummary(
        files_analyzed_count=1,
        total_findings=1,
        findings_by_severity={"INFO": 0, "LOW": 1, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0},
        findings_by_category={"READABILITY": 0, "CORRECTNESS": 0, "SECURITY": 0, "PERFORMANCE": 0, "MAINTAINABILITY": 1, "ERROR_HANDLING": 0, "ARCHITECTURE": 0},
        static_findings_count=0,
        ai_findings_count=1,
    )
    output = CodeReviewOutput(
        summary="Review complete.",
        files_reviewed=["calc.py"],
        findings=[finding],
        metrics=summary,
        limitations=list(DEFAULT_CODE_REVIEW_LIMITATIONS),
    )
    res = validate_code_review_output(output, sample_context, file_contents_map={"calc.py": source})
    assert res.is_valid is False
    assert any("evidence text does not match" in e for e in res.errors)


def test_validate_output_duplicate_findings(sample_context):
    source = "x = 1\n"
    f1 = CodeReviewFinding(
        finding_id="CR-001",
        file_path="calc.py",
        line_start=1,
        line_end=1,
        severity=FindingSeverity.INFO,
        category=FindingCategory.READABILITY,
        source=FindingSource.AI_REVIEW,
        title="Duplicate",
        description="Duplicate finding 1",
        evidence="x = 1",
        recommendation="Fix",
    )
    f2 = CodeReviewFinding(
        finding_id="CR-002",
        file_path="calc.py",
        line_start=1,
        line_end=1,
        severity=FindingSeverity.INFO,
        category=FindingCategory.READABILITY,
        source=FindingSource.AI_REVIEW,
        title="Duplicate",
        description="Duplicate finding 2",
        evidence="x = 1",
        recommendation="Fix",
    )
    summary = CodeReviewSummary(
        files_analyzed_count=1,
        total_findings=2,
        findings_by_severity={"INFO": 2, "LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0},
        findings_by_category={"READABILITY": 2, "CORRECTNESS": 0, "SECURITY": 0, "PERFORMANCE": 0, "MAINTAINABILITY": 0, "ERROR_HANDLING": 0, "ARCHITECTURE": 0},
        static_findings_count=0,
        ai_findings_count=2,
    )
    output = CodeReviewOutput(
        summary="Review complete.",
        files_reviewed=["calc.py"],
        findings=[f1, f2],
        metrics=summary,
        limitations=list(DEFAULT_CODE_REVIEW_LIMITATIONS),
    )
    res = validate_code_review_output(output, sample_context, file_contents_map={"calc.py": source})
    assert res.is_valid is False
    assert any("duplicate finding detected" in e for e in res.errors)


def test_validate_output_metrics_mismatch(sample_context):
    source = "x = 1\n"
    f1 = CodeReviewFinding(
        finding_id="CR-001",
        file_path="calc.py",
        line_start=1,
        line_end=1,
        severity=FindingSeverity.INFO,
        category=FindingCategory.READABILITY,
        source=FindingSource.STATIC_ANALYSIS,
        title="Static Issue",
        description="Static test",
        evidence="x = 1",
        recommendation="Fix",
    )
    # Claiming static_findings_count=0 when it is 1
    summary = CodeReviewSummary(
        files_analyzed_count=1,
        total_findings=1,
        findings_by_severity={"INFO": 1, "LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0},
        findings_by_category={"READABILITY": 1, "CORRECTNESS": 0, "SECURITY": 0, "PERFORMANCE": 0, "MAINTAINABILITY": 0, "ERROR_HANDLING": 0, "ARCHITECTURE": 0},
        static_findings_count=0,  # MISMATCH
        ai_findings_count=1,       # MISMATCH
    )
    output = CodeReviewOutput(
        summary="Review complete.",
        files_reviewed=["calc.py"],
        findings=[f1],
        metrics=summary,
        limitations=list(DEFAULT_CODE_REVIEW_LIMITATIONS),
    )
    res = validate_code_review_output(output, sample_context, file_contents_map={"calc.py": source})
    assert res.is_valid is False
    assert any("static_findings_count" in e for e in res.errors)


def test_validate_output_missing_limitations(sample_context):
    output = CodeReviewOutput(
        summary="Review complete.",
        files_reviewed=["calc.py"],
        findings=[],
        metrics=CodeReviewSummary(
            files_analyzed_count=1,
            total_findings=0,
            findings_by_severity={"INFO": 0, "LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0},
            findings_by_category={"READABILITY": 0, "CORRECTNESS": 0, "SECURITY": 0, "PERFORMANCE": 0, "MAINTAINABILITY": 0, "ERROR_HANDLING": 0, "ARCHITECTURE": 0},
            static_findings_count=0,
            ai_findings_count=0,
        ),
        limitations=["Only one limitation"],  # < 3
    )
    res = validate_code_review_output(output, sample_context)
    assert res.is_valid is False
    assert any("limitations list must comprehensively document" in e for e in res.errors)
