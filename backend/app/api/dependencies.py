"""API Dependencies and Inversion of Control."""

from collections.abc import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.architecture_recommendation.contracts import (
    ArchitectureRecommendationCandidate,
    ArchitectureStyle,
    ArchitectureStyleRecommendation,
    ComponentRecommendation,
)
from app.agents.code_review.contracts import (
    CodeReviewCandidate,
    CodeReviewFinding,
    FindingCategory,
    FindingSeverity,
    FindingSource,
)
from app.agents.database_design.contracts import (
    AttributeRecommendation,
    DataType,
    DatabaseDesignCandidate,
    DatabaseParadigm,
    EntityRecommendation,
    PrimaryKeyRecommendation,
)
from app.agents.execution import AgentExecutor
from app.agents.explainability.contracts import (
    ClaimType,
    EngineeringInsight,
    ExplainabilityCandidate,
    InsightCategory,
    SourceReference,
)
from app.agents.providers.mock import MockLLMProvider
from app.agents.registry import agent_registry
from app.agents.requirement_analysis.contracts import RequirementAnalysisCandidate
from app.agents.test_case_generation.contracts import (
    TestCase,
    TestCaseGenerationCandidate,
    TestPriority,
    TestStep,
    TestType,
)
from app.core.config import settings
from app.core.database import get_db
from app.services.context_engine import ProjectContextEngine
from app.services.project_service import ProjectService
from app.services.requirement_service import RequirementService
from app.services.workflow_service import WorkflowService
from app.workflows.coordinator import WorkflowCoordinator


async def get_project_service(
    session: AsyncSession = Depends(get_db),
) -> ProjectService:
    """Dependency injecting a project service with an active session."""
    return ProjectService(session=session)


async def get_requirement_service(
    session: AsyncSession = Depends(get_db),
) -> RequirementService:
    """Dependency injecting a requirement service with an active session."""
    return RequirementService(session=session)


async def get_context_engine(
    session: AsyncSession = Depends(get_db),
) -> ProjectContextEngine:
    """Dependency injecting a project context engine with an active session."""
    return ProjectContextEngine(session=session)


def build_default_mock_provider() -> MockLLMProvider:

    """Build a MockLLMProvider pre-configured with valid candidates for all platform agents."""
    provider = MockLLMProvider()

    req_candidate = RequirementAnalysisCandidate(
        summary="Verified requirement analysis summary.",
        ambiguities=[],
        conflicts=[],
        missing_information=[],
        refinements=[],
        scope_clarifications=[],
    )
    arch_candidate = ArchitectureRecommendationCandidate(
        summary="Modular Monolith architecture recommendation.",
        architecture_styles=[
            ArchitectureStyleRecommendation(
                style=ArchitectureStyle.MODULAR_MONOLITH,
                rationale="High cohesion and maintainability for initial growth phase.",
                confidence=0.9,
            )
        ],
        components=[
            ComponentRecommendation(
                name="CoreService",
                responsibility="Manage core business logic.",
                reason="Core system requirement.",
                related_requirement_ids=[],
            )
        ],
        data_flows=[],
        technologies=[],
        trade_offs=[],
        assumptions=["Initial deployment"],
        constraints=["Python 3.12+"],
        unknowns=[],
        traceability_matrix=[],
    )
    db_candidate = DatabaseDesignCandidate(
        summary="Relational database design modeling core entities.",
        database_paradigm=DatabaseParadigm.RELATIONAL,
        entities=[
            EntityRecommendation(
                name="ProjectEntity",
                description="Core entity records",
                purpose="System data",
                attributes=[
                    AttributeRecommendation(
                        name="id",
                        data_type=DataType.UUID,
                        nullable=False,
                        description="Primary ID",
                        unique=True,
                    ),
                ],
                primary_key=PrimaryKeyRecommendation(attributes=["id"], is_composite=False),
                related_requirement_ids=[],
            )
        ],
        relationships=[],
        indexes=[],
        constraints=[],
        assumptions=[],
        trade_offs=[],
    )
    test_case_candidate = TestCaseGenerationCandidate(
        summary="Generated test scenarios.",
        test_cases=[
            TestCase(
                test_case_id="TC-001",
                title="Basic Functional Test",
                description="Verify primary workflow function",
                test_type=TestType.FUNCTIONAL,
                priority=TestPriority.HIGH,
                preconditions=[],
                steps=[
                    TestStep(
                        step_number=1,
                        action="Execute operation",
                        expected_behavior="Returns 200 OK",
                    )
                ],
                expected_result="Returns 200 OK",
                requirement_ids=["REQ-001"],
            )
        ],
    )

    code_review_candidate = CodeReviewCandidate(
        summary="AI code review findings summary.",
        findings=[
            CodeReviewFinding(
                finding_id="CR-001",
                file_path="app/main.py",
                line_start=1,
                line_end=1,
                severity=FindingSeverity.INFO,
                category=FindingCategory.READABILITY,
                source=FindingSource.AI_REVIEW,
                title="Code structure",
                description="Clean modular code structure.",
                evidence="def run():",
                recommendation="Add function docstring.",
            )
        ],
    )
    explainability_candidate = ExplainabilityCandidate(
        summary="Engineering synthesis across domain outputs.",
        insights=[
            EngineeringInsight(
                insight_id="INSIGHT-001",
                category=InsightCategory.CROSS_CUTTING,
                title="System Alignment",
                summary="Architecture aligns with specifications.",
                explanation="Components cleanly satisfy design criteria.",
                source_references=[
                    SourceReference(
                        agent_id="requirement-analysis",
                        source_entity_id="req-1",
                        source_field="summary",
                        claim_type=ClaimType.FACT,
                    )
                ],
                suggested_actions=["Implement tests."],
            )
        ],
    )

    for candidate in [
        req_candidate,
        arch_candidate,
        db_candidate,
        test_case_candidate,
        code_review_candidate,
        explainability_candidate,
    ]:
        provider.register_structured_response(candidate)

    return provider


def get_agent_executor() -> AgentExecutor:
    """Dependency injecting an AgentExecutor configured with platform defaults."""
    provider = build_default_mock_provider() if settings.LLM_PROVIDER == "mock" else MockLLMProvider()
    return AgentExecutor(
        provider=provider,
        max_retries=settings.LLM_MAX_RETRIES,
    )



def get_workflow_coordinator(
    executor: AgentExecutor = Depends(get_agent_executor),
) -> WorkflowCoordinator:
    """Dependency injecting a WorkflowCoordinator instance."""
    return WorkflowCoordinator(executor=executor, registry=agent_registry)


async def get_workflow_service(
    session: AsyncSession = Depends(get_db),
    context_engine: ProjectContextEngine = Depends(get_context_engine),
    coordinator: WorkflowCoordinator = Depends(get_workflow_coordinator),
) -> WorkflowService:
    """Dependency injecting a WorkflowService with an active session and context engine."""
    return WorkflowService(
        session=session,
        context_engine=context_engine,
        coordinator=coordinator,
    )

