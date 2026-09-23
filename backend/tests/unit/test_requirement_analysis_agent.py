"""Comprehensive Unit Tests for Phase 4 Requirement Analysis Agent."""

import uuid
from datetime import datetime, timezone
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.contracts import AgentExecutionStatus, AgentType
from app.agents.exceptions import AgentValidationError
from app.agents.execution import AgentExecutor
from app.agents.providers.mock import MockLLMProvider
from app.agents.registry import AgentRegistry, agent_registry, register_default_agents
from app.agents.requirement_analysis import (
    AnalysisSeverity,
    MissingInformation,
    RequirementAmbiguity,
    RequirementAnalysisAgent,
    RequirementAnalysisCandidate,
    RequirementAnalysisOutput,
    RequirementConflict,
    RequirementRefinement,
    ScopeClarification,
)
from app.models.project import Project, ProjectStatus
from app.models.requirement import (
    Requirement,
    RequirementPriority,
    RequirementStatus,
    RequirementType,
)
from app.schemas.context import ProjectContextResponse, RequirementStatistics
from app.schemas.project import ProjectResponse
from app.schemas.requirement import RequirementResponse


@pytest.fixture
def sample_context() -> tuple[ProjectContextResponse, uuid.UUID, uuid.UUID]:
    """Provide a canonical ProjectContextResponse with two active requirements."""
    project_id = uuid.uuid4()
    req1_id = uuid.uuid4()
    req2_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    req1 = RequirementResponse(
        id=req1_id,
        project_id=project_id,
        title="High Performance Search",
        description="The search must be super fast and return instantly.",
        type=RequirementType.NON_FUNCTIONAL,
        priority=RequirementPriority.HIGH,
        status=RequirementStatus.APPROVED,
        is_archived=False,
        created_at=now,
        updated_at=now,
    )
    req2 = RequirementResponse(
        id=req2_id,
        project_id=project_id,
        title="Extensive Deep Auditing",
        description="All searches must block until all audit logs are synched across 5 regions.",
        type=RequirementType.CONSTRAINT,
        priority=RequirementPriority.HIGH,
        status=RequirementStatus.APPROVED,
        is_archived=False,
        created_at=now,
        updated_at=now,
    )

    stats = RequirementStatistics(
        total_requirements=3,
        active_requirements=2,
        functional_count=0,
        non_functional_count=1,
        constraint_count=1,
        by_priority={"HIGH": 2},
        by_status={"APPROVED": 2, "DEFERRED": 1},
        completion_percentage=0.0,
    )

    context = ProjectContextResponse(
        project=ProjectResponse(
            id=project_id,
            name="E-Commerce Search Engine",
            slug="ecom-search",
            status="IN_PROGRESS",
            created_at=now,
            updated_at=now,
        ),
        requirements=[req1, req2],
        statistics=stats,
        context_version=1,
        generated_at=now,
    )
    return context, req1_id, req2_id


# --------------------------------------------------------------------------
# 1. Metadata and Agent Identity
# --------------------------------------------------------------------------
def test_requirement_analysis_agent_metadata():
    agent = RequirementAnalysisAgent()
    meta = agent.metadata
    assert meta.agent_id == "requirement-analysis"
    assert meta.name == "Requirement Analysis Agent"
    assert meta.version == "1.0.0"
    assert meta.agent_type == AgentType.ANALYSIS
    assert agent.output_schema == RequirementAnalysisOutput


# --------------------------------------------------------------------------
# 2. Successful Execution Lifecycle & Context Consumption
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_successful_analysis_lifecycle(sample_context):
    context, req1_id, req2_id = sample_context
    agent = RequirementAnalysisAgent()
    provider = MockLLMProvider()

    candidate = RequirementAnalysisCandidate(
        summary="Analysis found performance ambiguity and conflict between search latency and auditing.",
        ambiguities=[
            RequirementAmbiguity(
                requirement_id=req1_id,
                issue="Vague latency goal",
                explanation="'super fast and return instantly' is not testable or quantifiable.",
                suggested_clarification="Specify maximum p99 latency in milliseconds (e.g. p99 < 150ms).",
                severity=AnalysisSeverity.HIGH,
            )
        ],
        conflicts=[
            RequirementConflict(
                requirement_id=req1_id,
                related_requirement_id=req2_id,
                issue="Latency vs Synchronous Distributed Audit",
                explanation="Sub-second instant search cannot wait for synchronous cross-region audit replication.",
                severity=AnalysisSeverity.CRITICAL,
            )
        ],
        missing_information=[
            MissingInformation(
                area="Telemetry",
                description="No logging or latency metrics pipeline specified for search queries.",
                reason="Necessary for SLA observability.",
                severity=AnalysisSeverity.MEDIUM,
            )
        ],
        refinements=[
            RequirementRefinement(
                requirement_id=req1_id,
                suggestion="Define exact SLA threshold for search response times.",
                reason="Improves testability.",
                suggested_type=RequirementType.NON_FUNCTIONAL,
                suggested_priority=RequirementPriority.HIGH,
            )
        ],
        scope_clarifications=[
            ScopeClarification(
                topic="External Sync",
                question="Is asynchronous audit streaming acceptable instead of synchronous block?",
                rationale="Unblocks high-speed search SLA.",
            )
        ],
    )
    provider.register_structured_response(candidate)

    executor = AgentExecutor(provider=provider)
    result = await executor.execute(agent=agent, context=context)

    assert result.status == AgentExecutionStatus.COMPLETED
    assert result.output is not None
    assert len(result.output.ambiguities) == 1
    assert result.output.ambiguities[0].requirement_id == req1_id
    assert len(result.output.conflicts) == 1
    assert result.output.conflicts[0].related_requirement_id == req2_id
    assert len(result.output.refinements) == 1
    assert result.output.refinements[0].suggested_type == RequirementType.NON_FUNCTIONAL
    assert result.validation.is_valid is True
    assert result.error is None


# --------------------------------------------------------------------------
# 3. Deterministic Metric Integrity Tests (User Mandatory Correction Pass)
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_deterministic_metric_injection_ignores_llm_spoof(sample_context):
    """Test A: LLM attempts to supply a spoofed completeness score.
    Authoritative backend overrides it with Phase 2 canonical statistics.
    """
    context, req1_id, _ = sample_context
    # In context: completion_percentage=0.0, active=2, total=3
    agent = RequirementAnalysisAgent()
    provider = MockLLMProvider()

    # Model returns raw dict attempting to inject false metrics
    spoofed_candidate = {
        "summary": "Spoofed attempt output",
        "ambiguities": [],
        "conflicts": [],
        "missing_information": [],
        "refinements": [],
        "scope_clarifications": [],
        "completeness_score": 98.5,  # Spoofed!
        "active_requirements_count": 999,  # Spoofed!
        "total_requirements_count": 9999,  # Spoofed!
    }
    provider.register_response(str(spoofed_candidate).replace("'", '"'))

    executor = AgentExecutor(provider=provider)
    result = await executor.execute(agent=agent, context=context)

    assert result.status == AgentExecutionStatus.COMPLETED
    assert result.output is not None
    # Authoritative Phase 2 values must overwrite spoofed values
    assert result.output.completeness_score == 0.0
    assert result.output.active_requirements_count == 2
    assert result.output.total_requirements_count == 3


@pytest.mark.asyncio
async def test_deterministic_metrics_present_when_candidate_omits_them(sample_context):
    """Test B: Candidate output omits all metrics. Final output must contain authoritative metrics."""
    context, _, _ = sample_context
    agent = RequirementAnalysisAgent()
    provider = MockLLMProvider()

    candidate = RequirementAnalysisCandidate(
        summary="Candidate with no metrics provided.",
        ambiguities=[],
        conflicts=[],
        missing_information=[],
        refinements=[],
        scope_clarifications=[],
    )
    provider.register_structured_response(candidate)

    executor = AgentExecutor(provider=provider)
    result = await executor.execute(agent=agent, context=context)

    assert result.status == AgentExecutionStatus.COMPLETED
    assert result.output is not None
    assert result.output.completeness_score == context.statistics.completion_percentage
    assert result.output.active_requirements_count == context.statistics.active_requirements
    assert result.output.total_requirements_count == context.statistics.total_requirements


@pytest.mark.asyncio
async def test_canonical_statistics_consistency(sample_context):
    """Test C: Verify output deterministic metrics correspond exactly to actual Phase 2 statistics."""
    context, _, _ = sample_context
    # Update context statistics to non-zero values to test exact mapping
    context.statistics.completion_percentage = 66.67
    context.statistics.active_requirements = 3
    context.statistics.total_requirements = 5

    agent = RequirementAnalysisAgent()
    provider = MockLLMProvider()
    provider.register_structured_response(RequirementAnalysisCandidate(summary="Test C check"))

    executor = AgentExecutor(provider=provider)
    result = await executor.execute(agent=agent, context=context)

    assert result.status == AgentExecutionStatus.COMPLETED
    assert result.output.completeness_score == 66.67
    assert result.output.active_requirements_count == 3
    assert result.output.total_requirements_count == 5


# --------------------------------------------------------------------------
# 4. Hallucination Defense & Reference Validation
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_rejects_hallucinated_requirement_id(sample_context):
    """Verify that referencing an invented UUID fails deterministic validation."""
    context, _, _ = sample_context
    agent = RequirementAnalysisAgent()
    provider = MockLLMProvider()

    fake_id = uuid.uuid4()
    candidate = RequirementAnalysisCandidate(
        summary="Hallucinated ID candidate",
        ambiguities=[
            RequirementAmbiguity(
                requirement_id=fake_id,
                issue="Invented requirement",
                explanation="Does not exist.",
                suggested_clarification="Please clarify this requirement specification.",
            )
        ],
    )
    provider.register_structured_response(candidate)

    executor = AgentExecutor(provider=provider)
    result = await executor.execute(agent=agent, context=context)

    assert result.status == AgentExecutionStatus.FAILED
    assert result.error is not None
    assert result.error.error_code == "VALIDATION_FAILED"
    assert result.validation.is_valid is False
    assert any(str(fake_id) in err for err in result.validation.errors)


@pytest.mark.asyncio
async def test_rejects_self_conflicting_requirement(sample_context):
    """Verify that a conflict pair referencing the same requirement twice is rejected."""
    context, req1_id, _ = sample_context
    agent = RequirementAnalysisAgent()
    provider = MockLLMProvider()

    candidate = RequirementAnalysisCandidate(
        summary="Self-conflict candidate",
        conflicts=[
            RequirementConflict(
                requirement_id=req1_id,
                related_requirement_id=req1_id,  # Same requirement!
                issue="Self contradiction",
                explanation="Cannot conflict with itself.",
            )
        ],
    )
    provider.register_structured_response(candidate)

    executor = AgentExecutor(provider=provider)
    result = await executor.execute(agent=agent, context=context)

    assert result.status == AgentExecutionStatus.FAILED
    assert result.error.error_code == "VALIDATION_FAILED"
    assert any("cannot reference the same requirement ID" in err for err in result.validation.errors)


# --------------------------------------------------------------------------
# 5. Strict Read-Only Guarantee: Zero Database Mutation
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_agent_execution_never_mutates_database(db_session: AsyncSession):
    """Verify that executing RequirementAnalysisAgent does NOT alter requirements in PostgreSQL."""
    # 1. Seed project and requirement in database
    proj = Project(
        name="Mutation Guard Project",
        slug=f"mut-guard-{uuid.uuid4().hex[:8]}",
        status=ProjectStatus.IN_PROGRESS,
    )
    db_session.add(proj)
    await db_session.commit()
    await db_session.refresh(proj)

    req = Requirement(
        project_id=proj.id,
        title="Immutable Base Requirement",
        description="Must never be changed by agent execution.",
        type=RequirementType.FUNCTIONAL,
        priority=RequirementPriority.MEDIUM,
        status=RequirementStatus.APPROVED,
    )
    db_session.add(req)
    await db_session.commit()
    await db_session.refresh(req)

    initial_title = req.title
    initial_desc = req.description
    initial_type = req.type
    initial_priority = req.priority
    initial_status = req.status
    initial_updated_at = req.updated_at

    now = datetime.now(timezone.utc)
    context = ProjectContextResponse(
        project=ProjectResponse.model_validate(proj),
        requirements=[RequirementResponse.model_validate(req)],
        statistics=RequirementStatistics(
            total_requirements=1,
            active_requirements=1,
            functional_count=1,
            non_functional_count=0,
            constraint_count=0,
            completion_percentage=0.0,
        ),
        context_version=1,
        generated_at=now,
    )

    # 2. Agent suggests reclassifying to NON_FUNCTIONAL / CRITICAL
    agent = RequirementAnalysisAgent()
    provider = MockLLMProvider()
    candidate = RequirementAnalysisCandidate(
        summary="Refinement advisory",
        refinements=[
            RequirementRefinement(
                requirement_id=req.id,
                suggestion="Reclassify to non-functional and critical",
                reason="High security impact",
                suggested_type=RequirementType.NON_FUNCTIONAL,
                suggested_priority=RequirementPriority.CRITICAL,
            )
        ],
    )
    provider.register_structured_response(candidate)

    executor = AgentExecutor(provider=provider)
    result = await executor.execute(agent=agent, context=context, session=db_session)
    assert result.status == AgentExecutionStatus.COMPLETED

    # 3. Reload requirement from database and verify zero mutation
    await db_session.refresh(req)
    assert req.title == initial_title
    assert req.description == initial_desc
    assert req.type == initial_type  # Remains FUNCTIONAL, not NON_FUNCTIONAL
    assert req.priority == initial_priority  # Remains MEDIUM, not CRITICAL
    assert req.status == initial_status
    assert req.updated_at == initial_updated_at


# --------------------------------------------------------------------------
# 6. Idempotent Registry Integration Tests
# --------------------------------------------------------------------------
def test_register_default_agents_idempotent():
    """Verify that calling register_default_agents repeatedly does not raise ConflictError."""
    test_reg = AgentRegistry()
    register_default_agents(registry=test_reg)
    assert test_reg.has("requirement-analysis")

    # Repeat call must succeed cleanly without raising ConflictError
    register_default_agents(registry=test_reg)
    assert len(test_reg.list_agents()) == 8


@pytest.mark.asyncio
async def test_requirement_analysis_agent_discovery_via_api(client: AsyncClient):
    """Verify that RequirementAnalysisAgent is discoverable via GET /api/v1/agents."""
    register_default_agents()
    res = await client.get("/api/v1/agents")
    assert res.status_code == 200
    agents = res.json()
    agent_ids = [a["agent_id"] for a in agents]
    assert "requirement-analysis" in agent_ids

    target = next(a for a in agents if a["agent_id"] == "requirement-analysis")
    assert target["name"] == "Requirement Analysis Agent"
    assert target["version"] == "1.0.0"
    assert target["agent_type"] == "ANALYSIS"


# --------------------------------------------------------------------------
# 7. Additional Domain Validation Edge Cases & Transient Retry Tests
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_rejects_hallucinated_conflict_peer(sample_context):
    """Verify that a conflict pair referencing a nonexistent related_requirement_id is rejected."""
    context, req1_id, _ = sample_context
    agent = RequirementAnalysisAgent()
    provider = MockLLMProvider()

    fake_peer_id = uuid.uuid4()
    candidate = RequirementAnalysisCandidate(
        summary="Invalid conflict peer candidate",
        conflicts=[
            RequirementConflict(
                requirement_id=req1_id,
                related_requirement_id=fake_peer_id,
                issue="Contradiction with phantom requirement",
                explanation="Does not exist in canonical context.",
            )
        ],
    )
    provider.register_structured_response(candidate)

    executor = AgentExecutor(provider=provider)
    result = await executor.execute(agent=agent, context=context)

    assert result.status == AgentExecutionStatus.FAILED
    assert result.error.error_code == "VALIDATION_FAILED"
    assert any(str(fake_peer_id) in err for err in result.validation.errors)


@pytest.mark.asyncio
async def test_rejects_hallucinated_refinement_target(sample_context):
    """Verify that a refinement referencing a nonexistent requirement ID is rejected."""
    context, _, _ = sample_context
    agent = RequirementAnalysisAgent()
    provider = MockLLMProvider()

    fake_id = uuid.uuid4()
    candidate = RequirementAnalysisCandidate(
        summary="Invalid refinement target",
        refinements=[
            RequirementRefinement(
                requirement_id=fake_id,
                suggestion="Improve non-existent requirement",
                reason="High priority",
            )
        ],
    )
    provider.register_structured_response(candidate)

    executor = AgentExecutor(provider=provider)
    result = await executor.execute(agent=agent, context=context)

    assert result.status == AgentExecutionStatus.FAILED
    assert result.error.error_code == "VALIDATION_FAILED"
    assert any(str(fake_id) in err for err in result.validation.errors)


@pytest.mark.asyncio
async def test_analysis_lifecycle_with_empty_requirements():
    """Verify agent handles empty requirements list gracefully."""
    now = datetime.now(timezone.utc)
    empty_context = ProjectContextResponse(
        project=ProjectResponse(
            id=uuid.uuid4(),
            name="Empty Project",
            slug="empty-proj",
            status="DRAFT",
            created_at=now,
            updated_at=now,
        ),
        requirements=[],
        statistics=RequirementStatistics(
            total_requirements=0,
            active_requirements=0,
            functional_count=0,
            non_functional_count=0,
            constraint_count=0,
            completion_percentage=0.0,
        ),
        context_version=1,
        generated_at=now,
    )

    agent = RequirementAnalysisAgent()
    provider = MockLLMProvider()
    provider.register_structured_response(
        RequirementAnalysisCandidate(
            summary="No requirements provided to analyze.",
            missing_information=[
                MissingInformation(
                    area="Specification",
                    description="Project has no requirements defined.",
                    reason="Initial requirements definition is missing.",
                )
            ],
        )
    )

    executor = AgentExecutor(provider=provider)
    result = await executor.execute(agent=agent, context=empty_context)

    assert result.status == AgentExecutionStatus.COMPLETED
    assert result.output.completeness_score == 0.0
    assert result.output.active_requirements_count == 0
    assert len(result.output.missing_information) == 1


@pytest.mark.asyncio
async def test_transient_provider_error_retried_by_executor(sample_context):
    """Verify that transient provider failures are transparently retried by AgentExecutor."""
    context, req1_id, _ = sample_context
    agent = RequirementAnalysisAgent()
    provider = MockLLMProvider()

    # Program provider to fail once transiently, then succeed
    provider.simulate_transient_failures(1)
    provider.register_structured_response(
        RequirementAnalysisCandidate(summary="Recovery after transient retry")
    )

    executor = AgentExecutor(provider=provider, max_retries=3)
    result = await executor.execute(agent=agent, context=context)

    assert result.status == AgentExecutionStatus.COMPLETED
    assert result.output.summary == "Recovery after transient retry"
    assert result.metadata.get("attempts") == 2

