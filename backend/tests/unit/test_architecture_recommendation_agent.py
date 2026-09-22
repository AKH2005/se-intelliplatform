"""Comprehensive Unit Tests for Phase 5 Architecture Recommendation Agent."""

import uuid
from datetime import datetime, timezone
from unittest.mock import patch
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.architecture_recommendation import (
    ArchitectureRecommendationAgent,
    ArchitectureRecommendationCandidate,
    ArchitectureRecommendationOutput,
    ArchitectureRequirementTrace,
    ArchitectureStyle,
    ArchitectureStyleRecommendation,
    ComponentRecommendation,
    DataFlowRecommendation,
    TechnologyCategory,
    TechnologyRecommendation,
    TradeOffAnalysis,
)
from app.agents.contracts import AgentExecutionStatus, AgentType
from app.agents.execution import AgentExecutor
from app.agents.providers.mock import MockLLMProvider
from app.agents.registry import AgentRegistry, register_default_agents
from app.agents.requirement_analysis.agent import RequirementAnalysisAgent
from app.agents.requirement_analysis.contracts import (
    AnalysisSeverity,
    RequirementConflict,
    RequirementAnalysisOutput,
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
def sample_arch_context() -> tuple[ProjectContextResponse, uuid.UUID, uuid.UUID]:
    """Provide a canonical ProjectContextResponse with two active requirements."""
    project_id = uuid.uuid4()
    req1_id = uuid.uuid4()
    req2_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    req1 = RequirementResponse(
        id=req1_id,
        project_id=project_id,
        title="Payment Gateway Integration",
        description="Process credit card transactions via Stripe API with PCI compliance.",
        type=RequirementType.FUNCTIONAL,
        priority=RequirementPriority.CRITICAL,
        status=RequirementStatus.APPROVED,
        is_archived=False,
        created_at=now,
        updated_at=now,
    )
    req2 = RequirementResponse(
        id=req2_id,
        project_id=project_id,
        title="Transaction History Audit",
        description="All payment transactions must be archived immutably for 7 years.",
        type=RequirementType.CONSTRAINT,
        priority=RequirementPriority.HIGH,
        status=RequirementStatus.APPROVED,
        is_archived=False,
        created_at=now,
        updated_at=now,
    )

    stats = RequirementStatistics(
        total_requirements=2,
        active_requirements=2,
        functional_count=1,
        non_functional_count=0,
        constraint_count=1,
        by_priority={"CRITICAL": 1, "HIGH": 1},
        by_status={"APPROVED": 2},
        completion_percentage=0.0,
    )

    context = ProjectContextResponse(
        project=ProjectResponse(
            id=project_id,
            name="FinTech Payment Service",
            slug="fintech-pay",
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


@pytest.fixture
def sample_req_analysis(sample_arch_context) -> RequirementAnalysisOutput:
    """Provide a validated Phase 4 RequirementAnalysisOutput."""
    _, req1_id, req2_id = sample_arch_context
    return RequirementAnalysisOutput(
        summary="Requirements show strong security and audit constraints around payments.",
        ambiguities=[],
        conflicts=[
            RequirementConflict(
                requirement_id=req1_id,
                related_requirement_id=req2_id,
                issue="Sync Latency vs Immutable Audit",
                explanation="Card processing latency may be hindered by synchronous cross-region audit writes.",
                severity=AnalysisSeverity.HIGH,
            )
        ],
        missing_information=[],
        refinements=[],
        scope_clarifications=[],
        completeness_score=0.0,
        active_requirements_count=2,
        total_requirements_count=2,
    )


# --------------------------------------------------------------------------
# 1. Metadata and Agent Identity
# --------------------------------------------------------------------------
def test_architecture_recommendation_agent_metadata():
    agent = ArchitectureRecommendationAgent()
    meta = agent.metadata
    assert meta.agent_id == "architecture-recommendation"
    assert meta.name == "Architecture Recommendation Agent"
    assert meta.version == "1.0.0"
    assert meta.agent_type == AgentType.RECOMMENDATION
    assert agent.output_schema == ArchitectureRecommendationOutput


# --------------------------------------------------------------------------
# 2. Successful Execution Lifecycle & Input Composition
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_successful_architecture_execution_with_phase4_findings(
    sample_arch_context, sample_req_analysis
):
    """Verify full execution lifecycle with injected Phase 4 requirement analysis findings."""
    context, req1_id, req2_id = sample_arch_context
    agent = ArchitectureRecommendationAgent()
    provider = MockLLMProvider()

    candidate = ArchitectureRecommendationCandidate(
        summary="Recommended Modular Monolith with dedicated payment isolation and asynchronous audit logging.",
        architecture_styles=[
            ArchitectureStyleRecommendation(
                style=ArchitectureStyle.MODULAR_MONOLITH,
                rationale="Provides strict domain boundaries while keeping operational complexity low.",
                confidence=0.85,
            )
        ],
        components=[
            ComponentRecommendation(
                name="Payment Module",
                responsibility="Handles payment gateway communication and tokenization.",
                reason="Isolates sensitive PCI payment processing logic.",
                related_requirement_ids=[req1_id],
            ),
            ComponentRecommendation(
                name="Audit Log Module",
                responsibility="Durable immutable audit storage and reporting.",
                reason="Fulfills 7-year regulatory compliance constraint.",
                related_requirement_ids=[req2_id],
            ),
        ],
        data_flows=[
            DataFlowRecommendation(
                source_component="Payment Module",
                target_component="Audit Log Module",
                interaction="Asynchronous Event Queue (Event-Driven Audit)",
                reason="Decouples payment latency from synchronous audit disk persistence.",
            )
        ],
        technologies=[
            TechnologyRecommendation(
                technology="PostgreSQL",
                category=TechnologyCategory.DATABASE,
                reason="ACID compliance and proven transactional integrity for ledger records.",
                trade_off="Requires vertical scaling or sharding under extreme concurrent load.",
            )
        ],
        trade_offs=[
            TradeOffAnalysis(
                decision_area="Monolith vs Microservices",
                recommended_option="Modular Monolith",
                advantages=["Single deployable unit", "Low network overhead", "Simplified local testing"],
                disadvantages=["Coupled deployment cycle", "Shared runtime resources"],
                alternative="Microservices",
                alternative_tradeoff="Significantly higher deployment and monitoring operational burden.",
            )
        ],
        assumptions=["Expected volume is under 5,000 transactions per second."],
        constraints=["PCI-DSS compliance requires isolated token handling."],
        unknowns=["Long-term cold storage retention format for 7-year archive."],
        traceability_matrix=[
            ArchitectureRequirementTrace(
                requirement_id=req1_id,
                component_names=["Payment Module"],
                rationale="Directly handles transaction processing.",
            ),
            ArchitectureRequirementTrace(
                requirement_id=req2_id,
                component_names=["Audit Log Module"],
                rationale="Ensures immutable retention compliance.",
            ),
        ],
    )
    provider.register_structured_response(candidate)

    executor = AgentExecutor(provider=provider)
    result = await executor.execute(
        agent=agent,
        context=context,
        requirement_analysis=sample_req_analysis,
    )

    assert result.status == AgentExecutionStatus.COMPLETED
    assert result.output is not None
    assert len(result.output.components) == 2
    assert len(result.output.data_flows) == 1
    assert result.output.architecture_styles[0].style == ArchitectureStyle.MODULAR_MONOLITH
    assert result.validation.is_valid is True
    assert result.error is None


@pytest.mark.asyncio
async def test_successful_architecture_execution_without_phase4_findings(sample_arch_context):
    """Verify agent operates successfully in standalone mode (without Phase 4 findings)."""
    context, req1_id, _ = sample_arch_context
    agent = ArchitectureRecommendationAgent()
    provider = MockLLMProvider()

    candidate = ArchitectureRecommendationCandidate(
        summary="Standalone architecture recommendation.",
        architecture_styles=[
            ArchitectureStyleRecommendation(
                style=ArchitectureStyle.LAYERED,
                rationale="Simple layered design suitable for current scope.",
                confidence=0.8,
            )
        ],
        components=[
            ComponentRecommendation(
                name="Core API",
                responsibility="Central request handler.",
                reason="Processes user requests.",
                related_requirement_ids=[req1_id],
            )
        ],
        data_flows=[],
        technologies=[],
        trade_offs=[],
        assumptions=[],
        constraints=[],
        unknowns=[],
        traceability_matrix=[],
    )
    provider.register_structured_response(candidate)

    executor = AgentExecutor(provider=provider)
    # Execute without requirement_analysis kwarg
    result = await executor.execute(agent=agent, context=context)

    assert result.status == AgentExecutionStatus.COMPLETED
    assert result.output is not None
    assert result.output.summary == "Standalone architecture recommendation."


# --------------------------------------------------------------------------
# 3. Explicit Prohibition of Internal Agent Execution
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_architecture_agent_does_not_call_requirement_analysis_agent_internally(
    sample_arch_context,
):
    """Verify that ArchitectureRecommendationAgent never calls RequirementAnalysisAgent.execute internally."""
    context, req1_id, _ = sample_arch_context
    agent = ArchitectureRecommendationAgent()
    provider = MockLLMProvider()

    provider.register_structured_response(
        ArchitectureRecommendationCandidate(
            summary="Clean boundary check.",
            components=[
                ComponentRecommendation(
                    name="Test Module",
                    responsibility="Verification",
                    reason="Verify no internal execution",
                    related_requirement_ids=[req1_id],
                )
            ],
        )
    )

    with patch.object(RequirementAnalysisAgent, "execute") as mock_req_exec:
        executor = AgentExecutor(provider=provider)
        result = await executor.execute(agent=agent, context=context)

        assert result.status == AgentExecutionStatus.COMPLETED
        # Must NEVER have been invoked internally
        assert not mock_req_exec.called


# --------------------------------------------------------------------------
# 4. Deterministic Validation Checks
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_rejects_duplicate_component_names(sample_arch_context):
    """Verify that duplicate component names trigger deterministic validation failure."""
    context, req1_id, _ = sample_arch_context
    agent = ArchitectureRecommendationAgent()
    provider = MockLLMProvider()

    candidate = ArchitectureRecommendationCandidate(
        summary="Duplicate component test",
        components=[
            ComponentRecommendation(
                name="Billing Service",
                responsibility="Billing",
                reason="Reason 1",
                related_requirement_ids=[req1_id],
            ),
            ComponentRecommendation(
                name="billing service",  # Duplicate (case-insensitive)
                responsibility="Billing duplicate",
                reason="Reason 2",
                related_requirement_ids=[req1_id],
            ),
        ],
    )
    provider.register_structured_response(candidate)

    executor = AgentExecutor(provider=provider)
    result = await executor.execute(agent=agent, context=context)

    assert result.status == AgentExecutionStatus.FAILED
    assert result.error.error_code == "VALIDATION_FAILED"
    assert any("duplicate name" in err for err in result.validation.errors)


@pytest.mark.asyncio
async def test_rejects_invalid_data_flow_source_and_target(sample_arch_context):
    """Verify that data flows referencing undeclared components are rejected."""
    context, req1_id, _ = sample_arch_context
    agent = ArchitectureRecommendationAgent()
    provider = MockLLMProvider()

    candidate = ArchitectureRecommendationCandidate(
        summary="Invalid data flow test",
        components=[
            ComponentRecommendation(
                name="Known Component",
                responsibility="Known",
                reason="Reason",
                related_requirement_ids=[req1_id],
            )
        ],
        data_flows=[
            DataFlowRecommendation(
                source_component="Known Component",
                target_component="Phantom Target",  # Does not exist!
                interaction="REST",
                reason="Testing",
            )
        ],
    )
    provider.register_structured_response(candidate)

    executor = AgentExecutor(provider=provider)
    result = await executor.execute(agent=agent, context=context)

    assert result.status == AgentExecutionStatus.FAILED
    assert result.error.error_code == "VALIDATION_FAILED"
    assert any("unknown target_component" in err for err in result.validation.errors)


@pytest.mark.asyncio
async def test_rejects_self_loop_data_flow(sample_arch_context):
    """Verify that data flows with identical source and target are rejected."""
    context, req1_id, _ = sample_arch_context
    agent = ArchitectureRecommendationAgent()
    provider = MockLLMProvider()

    candidate = ArchitectureRecommendationCandidate(
        summary="Self loop test",
        components=[
            ComponentRecommendation(
                name="Isolated Node",
                responsibility="Node handler service",
                reason="Reason",
                related_requirement_ids=[req1_id],
            )
        ],
        data_flows=[
            DataFlowRecommendation(
                source_component="Isolated Node",
                target_component="Isolated Node",  # Self loop!
                interaction="Loopback",
                reason="Invalid self flow",
            )
        ],
    )
    provider.register_structured_response(candidate)

    executor = AgentExecutor(provider=provider)
    result = await executor.execute(agent=agent, context=context)

    assert result.status == AgentExecutionStatus.FAILED
    assert any("identical source and target component" in err for err in result.validation.errors)


@pytest.mark.asyncio
async def test_rejects_hallucinated_requirement_id(sample_arch_context):
    """Verify that component referencing an invented requirement UUID fails deterministic validation."""
    context, _, _ = sample_arch_context
    agent = ArchitectureRecommendationAgent()
    provider = MockLLMProvider()

    fake_id = uuid.uuid4()
    candidate = ArchitectureRecommendationCandidate(
        summary="Hallucinated req test",
        components=[
            ComponentRecommendation(
                name="Auth Gateway",
                responsibility="Authentication gateway",
                reason="Reason",
                related_requirement_ids=[fake_id],  # Phantom ID!
            )
        ],
    )
    provider.register_structured_response(candidate)

    executor = AgentExecutor(provider=provider)
    result = await executor.execute(agent=agent, context=context)

    assert result.status == AgentExecutionStatus.FAILED
    assert any(str(fake_id) in err for err in result.validation.errors)


@pytest.mark.asyncio
async def test_rejects_traceability_matrix_unknown_component(sample_arch_context):
    """Verify traceability matrix referencing an undeclared component fails validation."""
    context, req1_id, _ = sample_arch_context
    agent = ArchitectureRecommendationAgent()
    provider = MockLLMProvider()

    candidate = ArchitectureRecommendationCandidate(
        summary="Traceability check",
        components=[
            ComponentRecommendation(
                name="Order Service",
                responsibility="Orders",
                reason="Order tracking",
                related_requirement_ids=[req1_id],
            )
        ],
        traceability_matrix=[
            ArchitectureRequirementTrace(
                requirement_id=req1_id,
                component_names=["NonExistentComponent"],  # Undeclared!
                rationale="Testing",
            )
        ],
    )
    provider.register_structured_response(candidate)

    executor = AgentExecutor(provider=provider)
    result = await executor.execute(agent=agent, context=context)

    assert result.status == AgentExecutionStatus.FAILED
    assert any("references unknown component: 'NonExistentComponent'" in err for err in result.validation.errors)


# --------------------------------------------------------------------------
# 5. Strict Read-Only Guarantee: Zero Database Mutation
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_architecture_execution_never_mutates_database(db_session: AsyncSession):
    """Verify that executing ArchitectureRecommendationAgent does NOT alter database requirements."""
    proj = Project(
        name="Arch Mutation Guard Project",
        slug=f"arch-mut-{uuid.uuid4().hex[:8]}",
        status=ProjectStatus.IN_PROGRESS,
    )
    db_session.add(proj)
    await db_session.commit()
    await db_session.refresh(proj)

    req = Requirement(
        project_id=proj.id,
        title="Payment Invariant",
        description="Immutable requirement.",
        type=RequirementType.FUNCTIONAL,
        priority=RequirementPriority.HIGH,
        status=RequirementStatus.APPROVED,
    )
    db_session.add(req)
    await db_session.commit()
    await db_session.refresh(req)

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

    agent = ArchitectureRecommendationAgent()
    provider = MockLLMProvider()
    provider.register_structured_response(
        ArchitectureRecommendationCandidate(
            summary="Mutation test",
            components=[
                ComponentRecommendation(
                    name="Service A",
                    responsibility="Service A",
                    reason="Reason",
                    related_requirement_ids=[req.id],
                )
            ],
        )
    )

    executor = AgentExecutor(provider=provider)
    result = await executor.execute(agent=agent, context=context, session=db_session)
    assert result.status == AgentExecutionStatus.COMPLETED

    await db_session.refresh(req)
    assert req.title == "Payment Invariant"
    assert req.type == RequirementType.FUNCTIONAL
    assert req.priority == RequirementPriority.HIGH
    assert req.status == RequirementStatus.APPROVED


# --------------------------------------------------------------------------
# 6. Idempotent Registry Integration Tests
# --------------------------------------------------------------------------
def test_register_default_agents_idempotent_includes_architecture():
    """Verify register_default_agents registers both agents and is idempotent."""
    test_reg = AgentRegistry()
    register_default_agents(registry=test_reg)
    assert test_reg.has("requirement-analysis")
    assert test_reg.has("architecture-recommendation")

    # Repeat call must not raise ConflictError
    register_default_agents(registry=test_reg)
    assert len(test_reg.list_agents()) == 2


@pytest.mark.asyncio
async def test_architecture_agent_discovery_via_api(client: AsyncClient):
    """Verify that ArchitectureRecommendationAgent is discoverable via GET /api/v1/agents."""
    register_default_agents()
    res = await client.get("/api/v1/agents")
    assert res.status_code == 200
    agents = res.json()
    agent_ids = [a["agent_id"] for a in agents]
    assert "architecture-recommendation" in agent_ids

    target = next(a for a in agents if a["agent_id"] == "architecture-recommendation")
    assert target["name"] == "Architecture Recommendation Agent"
    assert target["version"] == "1.0.0"
    assert target["agent_type"] == "RECOMMENDATION"


# --------------------------------------------------------------------------
# 7. Transient Provider Failure Retry Verification
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_architecture_agent_transient_failure_retry(sample_arch_context):
    """Verify transient provider errors are transparently retried by AgentExecutor."""
    context, req1_id, _ = sample_arch_context
    agent = ArchitectureRecommendationAgent()
    provider = MockLLMProvider()

    provider.simulate_transient_failures(1)
    provider.register_structured_response(
        ArchitectureRecommendationCandidate(
            summary="Successful after retry",
            components=[
                ComponentRecommendation(
                    name="Retry Component",
                    responsibility="Retry verification",
                    reason="Verify retry capability",
                    related_requirement_ids=[req1_id],
                )
            ],
        )
    )

    executor = AgentExecutor(provider=provider, max_retries=3)
    result = await executor.execute(agent=agent, context=context)

    assert result.status == AgentExecutionStatus.COMPLETED
    assert result.output.summary == "Successful after retry"
    assert result.metadata.get("attempts") == 2
