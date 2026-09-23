"""Unit tests for Phase 8.1 Code Review Agent."""

from datetime import datetime, timezone
import uuid
import pytest

from app.agents.code_review.agent import CodeReviewAgent
from app.agents.code_review.contracts import (
    CodeFile,
    CodeReviewCandidate,
    CodeReviewFinding,
    CodeReviewInput,
    CodeReviewOutput,
    FindingCategory,
    FindingSeverity,
    FindingSource,
)
from app.agents.contracts import AgentType
from app.agents.exceptions import AgentValidationError
from app.agents.providers.mock import MockLLMProvider
from app.agents.registry import AgentRegistry, register_default_agents
from app.models.requirement import RequirementPriority, RequirementStatus, RequirementType
from app.schemas.context import ProjectContextResponse, RequirementStatistics
from app.schemas.project import ProjectResponse
from app.schemas.requirement import RequirementResponse


@pytest.fixture
def mock_context():
    project_id = uuid.uuid4()
    req_active_id = uuid.uuid4()
    req_deferred_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    project = ProjectResponse(
        id=project_id,
        name="ReviewEngine",
        slug="reviewengine",
        description="Smart review platform",
        created_at=now,
        updated_at=now,
    )
    req1 = RequirementResponse(
        id=req_active_id,
        project_id=project_id,
        title="Input Validation",
        description="All user input must be sanitized and validated.",
        type=RequirementType.FUNCTIONAL,
        priority=RequirementPriority.CRITICAL,
        status=RequirementStatus.APPROVED,
        is_archived=False,
        created_at=now,
        updated_at=now,
    )
    req_deferred = RequirementResponse(
        id=req_deferred_id,
        project_id=project_id,
        title="Old Legacy Feature",
        description="Deprecated feature",
        type=RequirementType.FUNCTIONAL,
        priority=RequirementPriority.LOW,
        status=RequirementStatus.DEFERRED,
        is_archived=False,
        created_at=now,
        updated_at=now,
    )
    stats = RequirementStatistics(
        total_requirements=2,
        active_requirements=1,
        functional_count=2,
        non_functional_count=0,
        constraint_count=0,
        by_priority={"CRITICAL": 1, "LOW": 1},
        by_status={"APPROVED": 1, "DEFERRED": 1},
        completion_percentage=0.0,
    )
    return ProjectContextResponse(
        project=project,
        requirements=[req1, req_deferred],
        statistics=stats,
        context_version=1,
        generated_at=now,
    )


def test_agent_metadata():
    agent = CodeReviewAgent()
    meta = agent.metadata
    assert meta.agent_id == "code-review"
    assert meta.name == "AI Code Review Agent"
    assert meta.version == "1.0.0"
    assert meta.agent_type == AgentType.REVIEW
    assert agent.output_schema == CodeReviewOutput


@pytest.mark.asyncio
async def test_analyze_missing_code_input(mock_context):
    agent = CodeReviewAgent()
    with pytest.raises(AgentValidationError, match="requires 'code_input'"):
        await agent.analyze(mock_context)


@pytest.mark.asyncio
async def test_analyze_filters_inactive_requirements(mock_context):
    agent = CodeReviewAgent()
    code_input = CodeReviewInput(
        files=[CodeFile(file_path="service.py", language="python", content="x = 1\n")]
    )
    analysis = await agent.analyze(mock_context, code_input=code_input)

    assert "active_requirements" in analysis
    active_reqs = analysis["active_requirements"]
    assert len(active_reqs) == 1
    assert active_reqs[0].title == "Input Validation"


@pytest.mark.asyncio
async def test_analyze_detects_secrets_and_redacts(mock_context):
    agent = CodeReviewAgent()
    fake_key = "AKIA1111222233334444"
    code = f"AWS_KEY = '{fake_key}'\n"
    code_input = CodeReviewInput(
        files=[CodeFile(file_path="config.py", language="python", content=code)]
    )
    analysis = await agent.analyze(mock_context, code_input=code_input)

    # Invariant: static_findings must include secret finding
    static_findings = analysis["static_findings"]
    assert len(static_findings) == 1
    assert static_findings[0].category == FindingCategory.SECURITY
    assert static_findings[0].rule_id == "SECRET-DETECTION"

    # Redacted files for prompt must NOT contain raw secret
    redacted_files = analysis["redacted_files"]
    assert fake_key not in redacted_files[0].content
    assert "***REDACTED_SECRET***" in redacted_files[0].content


@pytest.mark.asyncio
async def test_generate_end_to_end_with_mock_provider(mock_context):
    agent = CodeReviewAgent()
    provider = MockLLMProvider()

    code = (
        "def process(data):\n"
        "    result = eval(data)\n"
        "    return result\n"
    )
    code_input = CodeReviewInput(
        files=[CodeFile(file_path="processor.py", language="python", content=code)]
    )

    candidate = CodeReviewCandidate(
        summary="Review indicates serious dynamic code execution risks.",
        findings=[
            CodeReviewFinding(
                finding_id="CANDIDATE-01",
                file_path="processor.py",
                line_start=1,
                line_end=1,
                severity=FindingSeverity.INFO,
                category=FindingCategory.READABILITY,
                source=FindingSource.AI_REVIEW,
                title="Missing Type Annotation",
                description="Parameter 'data' should be typed.",
                evidence="def process(data):",
                recommendation="Add type annotations like data: str.",
            )
        ],
    )
    provider.register_structured_response(candidate)

    analysis = await agent.analyze(mock_context, code_input=code_input)
    output = await agent.generate(analysis, provider)

    assert isinstance(output, CodeReviewOutput)
    assert output.agent_id == "code-review"
    assert output.files_reviewed == ["processor.py"]
    assert len(output.findings) >= 2  # AST eval finding + candidate finding

    # Check finding IDs normalized to CR-001, CR-002...
    ids = [f.finding_id for f in output.findings]
    assert "CR-001" in ids
    assert "CR-002" in ids

    # Check metrics
    assert output.metrics.files_analyzed_count == 1
    assert output.metrics.total_findings == len(output.findings)
    assert output.metrics.static_findings_count >= 1
    assert output.metrics.ai_findings_count >= 1

    # Invariant validation passes
    val_res = agent.validate_output(output, mock_context)
    assert val_res.is_valid is True


@pytest.mark.asyncio
async def test_generate_discards_hallucinated_file(mock_context):
    agent = CodeReviewAgent()
    provider = MockLLMProvider()

    code = "x = 10\n"
    code_input = CodeReviewInput(
        files=[CodeFile(file_path="real.py", language="python", content=code)]
    )

    candidate = CodeReviewCandidate(
        summary="Review completed.",
        findings=[
            CodeReviewFinding(
                finding_id="CAND-01",
                file_path="non_existent.py",  # Hallucinated file
                line_start=1,
                line_end=1,
                severity=FindingSeverity.LOW,
                category=FindingCategory.READABILITY,
                source=FindingSource.AI_REVIEW,
                title="Hallucinated File Issue",
                description="Should be dropped.",
                evidence="fake line",
                recommendation="Fix",
            )
        ],
    )
    provider.register_structured_response(candidate)

    analysis = await agent.analyze(mock_context, code_input=code_input)
    output = await agent.generate(analysis, provider)

    # Hallucinated file finding must be discarded
    assert not any(f.file_path == "non_existent.py" for f in output.findings)


@pytest.mark.asyncio
async def test_generate_discards_hallucinated_lines_and_evidence(mock_context):
    agent = CodeReviewAgent()
    provider = MockLLMProvider()

    code = "def foo():\n    return 1\n"  # 2 lines
    code_input = CodeReviewInput(
        files=[CodeFile(file_path="foo.py", language="python", content=code)]
    )

    candidate = CodeReviewCandidate(
        summary="Review completed.",
        findings=[
            CodeReviewFinding(
                finding_id="CAND-LINE",
                file_path="foo.py",
                line_start=1,
                line_end=99,  # Hallucinated line bounds
                severity=FindingSeverity.LOW,
                category=FindingCategory.MAINTAINABILITY,
                source=FindingSource.AI_REVIEW,
                title="Bad Line Range",
                description="Should be dropped.",
                evidence="def foo():",
                recommendation="Fix",
            ),
            CodeReviewFinding(
                finding_id="CAND-EVID",
                file_path="foo.py",
                line_start=1,
                line_end=1,
                severity=FindingSeverity.LOW,
                category=FindingCategory.MAINTAINABILITY,
                source=FindingSource.AI_REVIEW,
                title="Bad Evidence",
                description="Evidence not on line 1.",
                evidence="def hallucinated_function():",  # Hallucinated evidence
                recommendation="Fix",
            ),
        ],
    )
    provider.register_structured_response(candidate)

    analysis = await agent.analyze(mock_context, code_input=code_input)
    output = await agent.generate(analysis, provider)

    # Both hallucinated findings must be dropped
    assert len(output.findings) == 0


def test_registry_integration():
    registry = AgentRegistry()
    register_default_agents(registry)

    assert registry.has("code-review")
    agent = registry.get("code-review")
    assert isinstance(agent, CodeReviewAgent)
    assert agent.metadata.agent_id == "code-review"
    assert len(registry.list_agents()) == 8

    # Idempotent registration
    register_default_agents(registry)
    assert len(registry.list_agents()) == 8
