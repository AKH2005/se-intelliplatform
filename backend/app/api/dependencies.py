"""API Dependencies and Inversion of Control."""

from typing import Any
import uuid
from collections.abc import AsyncGenerator
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.providers.base import AbstractLLMProvider
from app.core.database import get_db
from app.core.exceptions import ForbiddenError, NotFoundError, UnauthorizedError
from app.core.security import decode_access_token
from app.models.project import Project
from app.models.user import User, UserRole

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    auth: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    session: AsyncSession = Depends(get_db),
) -> User | None:
    """Extract and validate user from Bearer token if provided."""
    if not auth or not auth.credentials:
        return None
    token = auth.credentials
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        return None
    try:
        user_id = uuid.UUID(payload["sub"])
    except Exception:
        return None
    stmt = select(User).where(User.id == user_id, User.is_active.is_(True))
    res = await session.execute(stmt)
    return res.scalar_one_or_none()


async def get_current_user(
    auth: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    session: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate required authenticated user from Bearer token."""
    if not auth or not auth.credentials:
        raise UnauthorizedError("Authentication token is required.")
    token = auth.credentials
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise UnauthorizedError("Invalid or expired authentication token.")
    try:
        user_id = uuid.UUID(payload["sub"])
    except Exception:
        raise UnauthorizedError("Malformed authentication token.")
    stmt = select(User).where(User.id == user_id)
    res = await session.execute(stmt)
    user = res.scalar_one_or_none()
    if not user or not user.is_active:
        raise UnauthorizedError("User account not found or deactivated.")
    return user


async def get_authorized_project(
    project_id: uuid.UUID,
    current_user: User | None = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_db),
) -> Project:
    """Fetch project and enforce project ownership authorization."""
    stmt = select(Project).where(Project.id == project_id)
    res = await session.execute(stmt)
    project = res.scalar_one_or_none()
    if not project:
        raise NotFoundError("Project", str(project_id))
    if project.owner_id is not None:
        is_owner = current_user is not None and str(project.owner_id) == str(current_user.id)
        is_admin = current_user is not None and (
            getattr(current_user, "role", None) == UserRole.ADMIN
            or getattr(current_user, "role", None) == UserRole.ADMIN.value
        )
        if not (is_owner or is_admin):
            raise ForbiddenError("You do not have permission to access this project.")
    return project

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


async def get_project_download_service(
    session: AsyncSession = Depends(get_db),
):
    """Dependency injecting a project download service with an active session."""
    from app.services.project_download_service import ProjectDownloadService
    return ProjectDownloadService(session=session)


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

    from app.agents.failure_analysis.contracts import (
        ClaimType as FaClaimType,
        DiagnosticClaim as FaClaim,
        EvidenceReference as FaEvidence,
        FailureConfidence,
        FailureDiagnosis,
        FailureType,
    )
    from app.sandbox.static_analysis.contracts import DiagnosticSeverity

    failure_candidate = FailureDiagnosis(
        failure_type=FailureType.TEST_FAILURE,
        title="Test Assertion Failure in Unit Suite",
        summary="A pytest assertion failed during sandbox test execution.",
        root_cause="The returned value from the service did not match expected assertion criteria.",
        severity=DiagnosticSeverity.ERROR,
        affected_files=["app/main.py"],
        evidence=[
            FaEvidence(
                evidence_id="sandbox_stdout",
                source="execution",
                code="ASSERTION_ERROR",
                file_path="app/main.py",
                line=15,
                snippet='return {"message": "Welcome to TaskFlow API"}',
                description="Assertion mismatch in main endpoint response",
            )
        ],
        claims=[
            FaClaim(
                claim_type=FaClaimType.FACT,
                statement="The test suite returned exit code 1 due to a failed assertion.",
                evidence_ids=["sandbox_stdout"],
            ),
            FaClaim(
                claim_type=FaClaimType.INTERPRETATION,
                statement="The failure indicates a mismatch between actual function return and test assertion.",
                evidence_ids=["sandbox_stdout"],
            ),
            FaClaim(
                claim_type=FaClaimType.RECOMMENDATION,
                statement="Verify response payload structure in main endpoint.",
                evidence_ids=[],
            ),
            FaClaim(
                claim_type=FaClaimType.LIMITATION,
                statement="Diagnostic reasoning is limited to captured stdout tracebacks.",
                evidence_ids=[],
            ),
        ],
        requirement_links=[],
        architecture_links=[],
        database_links=[],
        suggested_remediation="Update main endpoint return payload to include version and healthy status.",
        limitations=["Runtime variable heap state was not captured."],
        confidence=FailureConfidence.HIGH,
    )

    from app.agents.remediation.contracts import (
        ChangeOperation,
        ProposedChange,
        RemediationProposalCandidate,
        RiskLevel,
    )

    remediation_candidate = RemediationProposalCandidate(
        title="Enhance main API endpoint response",
        summary="Adds version and healthy status to root endpoint response.",
        rationale="The root endpoint should provide full status metadata for health checks and service discovery.",
        changes=[
            ProposedChange(
                file_path="app/main.py",
                operation=ChangeOperation.MODIFY,
                original_region='return {"message": "Welcome to TaskFlow API"}',
                proposed_region='return {"message": "Welcome to TaskFlow API", "version": "v2", "status": "healthy"}',
                reason="Return enhanced status dictionary with version and status",
                evidence_ids=["sandbox_stdout"],
            )
        ],
        expected_effect="Root endpoint returns status: healthy and version: v2.",
        verification_plan="Run static analysis to confirm clean linting and run sandbox pytest suite.",
        risk_level=RiskLevel.LOW,
        requirement_links=[],
        architecture_links=[],
        database_links=[],
    )

    from app.agents.test_generation.contracts import (
        AITestSuiteCandidate,
        GeneratedTestCandidate,
    )

    ai_test_candidate = AITestSuiteCandidate(
        summary="AI-generated test suite for verified application module.",
        tests=[
            GeneratedTestCandidate(
                test_id="TEST-001",
                name="test_app_status",
                description="Verifies the primary application status or module function",
                category="HAPPY_PATH",
                target_file="app/main.py",
                target_symbol="main",
                requirement_ids=[],
                architecture_component="CoreService",
                rationale="Ensures module functions return expected values",
                code="""def test_app_status():\n    assert 1 + 1 == 2""",
                expected_behavior="Assertions pass",
            )
        ],
    )

    from app.schemas.assistant import AssistantResponseSchema

    assistant_candidate = AssistantResponseSchema(
        message="TaskFlow is in progress. Development version 2 has been generated and verified, and is deployed across development, staging, and production environments.",
        suggested_action=None,
        referenced_entity_type="version",
        referenced_entity_id="d7b86288-577b-4975-9e74-57662ad97fc6",
    )

    for candidate in [
        req_candidate,
        arch_candidate,
        db_candidate,
        test_case_candidate,
        code_review_candidate,
        explainability_candidate,
        failure_candidate,
        remediation_candidate,
        ai_test_candidate,
        assistant_candidate,
    ]:
        provider.register_structured_response(candidate)

    return provider


def get_agent_executor() -> AgentExecutor:
    """Dependency injecting an AgentExecutor configured with platform defaults and resilient fallback."""
    from app.agents.providers.factory import get_llm_provider

    mock_provider = build_default_mock_provider()
    fallback_provider = None
    if settings.LLM_PROVIDER == "mock":
        primary_provider = mock_provider
    elif settings.LLM_PROVIDER == "gemini":
        primary_provider = get_llm_provider("gemini")
        if settings.GROQ_API_KEY:
            fallback_provider = get_llm_provider("groq")
    else:
        primary_provider = get_llm_provider("groq")
        if settings.GEMINI_API_KEY:
            fallback_provider = get_llm_provider("gemini")

    return AgentExecutor(
        provider=primary_provider,
        max_retries=settings.LLM_MAX_RETRIES,
        retry_delay_seconds=2.0,
        mock_provider=mock_provider,
        fallback_provider=fallback_provider,
    )




def get_workflow_coordinator(
    executor: AgentExecutor = Depends(get_agent_executor),
) -> WorkflowCoordinator:
    """Dependency injecting a WorkflowCoordinator instance."""
    from app.agents.registry import register_all_agents
    register_all_agents(agent_registry)
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


def get_sandbox_executor() -> "AbstractSandboxExecutor":
    """Dependency injecting the sandbox executor. Uses Docker runtime by default."""
    from app.sandbox.base import AbstractSandboxExecutor
    from app.sandbox.docker_executor import DockerSandboxExecutor

    return DockerSandboxExecutor()


async def get_sandbox_service(
    session: AsyncSession = Depends(get_db),
    workflow_service: WorkflowService = Depends(get_workflow_service),
    executor: "AbstractSandboxExecutor" = Depends(get_sandbox_executor),
) -> "SandboxService":
    """Dependency injecting SandboxService with active session, workflow service, and executor."""
    from app.sandbox.base import AbstractSandboxExecutor
    from app.sandbox.service import SandboxService

    return SandboxService(
        session=session,
        workflow_service=workflow_service,
        executor=executor,
    )


async def get_static_analysis_service(
    session: AsyncSession = Depends(get_db),
    workflow_service: WorkflowService = Depends(get_workflow_service),
    executor: "AbstractSandboxExecutor" = Depends(get_sandbox_executor),
) -> "StaticAnalysisService":
    """Dependency injecting StaticAnalysisService with active session, workflow service, and executor."""
    from app.sandbox.base import AbstractSandboxExecutor
    from app.sandbox.static_analysis.service import StaticAnalysisService

    return StaticAnalysisService(
        session=session,
        workflow_service=workflow_service,
        executor=executor,
    )


async def get_failure_analysis_service(
    session: AsyncSession = Depends(get_db),
    workflow_service: WorkflowService = Depends(get_workflow_service),
    executor: AgentExecutor = Depends(get_agent_executor),
) -> "FailureAnalysisService":
    """Dependency injecting FailureAnalysisService with active session, workflow service, and agent executor."""
    from app.agents.failure_analysis.service import FailureAnalysisService

    return FailureAnalysisService(
        session=session,
        workflow_service=workflow_service,
        executor=executor,
    )


async def get_remediation_service(
    session: AsyncSession = Depends(get_db),
    workflow_service: WorkflowService = Depends(get_workflow_service),
    executor: AgentExecutor = Depends(get_agent_executor),
    context_engine: ProjectContextEngine = Depends(get_context_engine),
    sandbox_executor: "AbstractSandboxExecutor" = Depends(get_sandbox_executor),
) -> "RemediationService":
    """Dependency injecting RemediationService with active session, workflow service, agent executor, and sandbox."""
    from app.agents.remediation.service import RemediationService

    return RemediationService(
        session=session,
        workflow_service=workflow_service,
        executor=executor,
        context_engine=context_engine,
        sandbox_executor=sandbox_executor,
    )


async def get_ai_test_service(
    session: AsyncSession = Depends(get_db),
    workflow_service: WorkflowService = Depends(get_workflow_service),
    executor: AgentExecutor = Depends(get_agent_executor),
    context_engine: ProjectContextEngine = Depends(get_context_engine),
    sandbox_executor: "AbstractSandboxExecutor" = Depends(get_sandbox_executor),
) -> "AITestService":
    """Dependency injecting AITestService with active session, workflow service, agent executor, and sandbox."""
    from app.agents.test_generation.service import AITestService

    return AITestService(
        session=session,
        workflow_service=workflow_service,
        executor=executor,
        context_engine=context_engine,
        sandbox_executor=sandbox_executor,
    )


async def get_development_version_service(
    session: AsyncSession = Depends(get_db),
) -> "DevelopmentVersionService":
    """Dependency injecting DevelopmentVersionService with active session."""
    from app.services.development_version_service import DevelopmentVersionService

    return DevelopmentVersionService(session=session)


async def get_browser_testing_service(
    session: AsyncSession = Depends(get_db),
) -> "BrowserTestingService":
    """Dependency injecting BrowserTestingService with active DB session."""
    from app.browser.browser_testing_service import BrowserTestingService

    return BrowserTestingService(session=session)


async def get_assistant_context_builder(
    session: AsyncSession = Depends(get_db),
    context_engine: ProjectContextEngine = Depends(get_context_engine),
    version_service: "DevelopmentVersionService" = Depends(get_development_version_service),
    requirement_service: RequirementService = Depends(get_requirement_service),
    remediation_service: Any = Depends(get_remediation_service),
    browser_testing_service: Any = Depends(get_browser_testing_service),
) -> "AssistantContextBuilder":
    """Dependency injecting AssistantContextBuilder."""
    from app.services.assistant_context_builder import AssistantContextBuilder

    return AssistantContextBuilder(
        session=session,
        context_engine=context_engine,
        version_service=version_service,
        requirement_service=requirement_service,
        remediation_service=remediation_service,
        browser_testing_service=browser_testing_service,
    )


def get_assistant_llm_provider() -> AbstractLLMProvider:
    """Dependency injecting AbstractLLMProvider for Intelli Assistant."""
    from app.agents.providers.factory import get_llm_provider

    if settings.LLM_PROVIDER == "mock":
        return build_default_mock_provider()
    return get_llm_provider()


async def get_assistant_reasoning_service(
    provider: AbstractLLMProvider = Depends(get_assistant_llm_provider),
) -> "AssistantReasoningService":
    """Dependency injecting AssistantReasoningService."""
    from app.services.assistant_reasoning_service import AssistantReasoningService

    return AssistantReasoningService(provider=provider)


async def get_browser_journey_service(
    session: AsyncSession = Depends(get_db),
    context_engine: ProjectContextEngine = Depends(get_context_engine),
    version_service: "DevelopmentVersionService" = Depends(get_development_version_service),
    browser_testing_service: Any = Depends(get_browser_testing_service),
    workflow_service: WorkflowService = Depends(get_workflow_service),
) -> "BrowserJourneyService":
    """Dependency injecting BrowserJourneyService."""
    from app.services.browser_journey_service import BrowserJourneyService

    return BrowserJourneyService(
        session=session,
        context_engine=context_engine,
        version_service=version_service,
        browser_testing_service=browser_testing_service,
        workflow_service=workflow_service,
    )


def get_unified_test_inventory_service() -> "UnifiedTestInventoryService":
    """Dependency injecting UnifiedTestInventoryService."""
    from app.testing.inventory.service import UnifiedTestInventoryService

    return UnifiedTestInventoryService()


def get_change_impact_service() -> "ChangeImpactService":
    """Dependency injecting ChangeImpactService."""
    from app.testing.impact.service import ChangeImpactService

    return ChangeImpactService()


def get_selective_regression_planner() -> "SelectiveRegressionPlanner":
    """Dependency injecting SelectiveRegressionPlanner."""
    from app.testing.regression.planner import SelectiveRegressionPlanner

    return SelectiveRegressionPlanner()


async def get_regression_execution_service(
    sandbox_executor: "AbstractSandboxExecutor" = Depends(get_sandbox_executor),
    browser_service: "BrowserTestingService" = Depends(get_browser_testing_service),
    ai_test_service: "AITestService" = Depends(get_ai_test_service),
    failure_analysis_service: "FailureAnalysisService" = Depends(get_failure_analysis_service),
) -> "RegressionExecutionService":
    """Dependency injecting RegressionExecutionService."""
    from app.services.verification_service import DevelopmentVerificationService
    from app.testing.regression.executor import RegressionExecutionService

    return RegressionExecutionService(
        sandbox_executor=sandbox_executor,
        browser_service=browser_service,
        ai_test_service=ai_test_service,
        failure_analysis_service=failure_analysis_service,
        verification_service=DevelopmentVerificationService(),
    )


async def get_environment_service(
    session: AsyncSession = Depends(get_db),
) -> "EnvironmentService":
    """Dependency injecting EnvironmentService with active session."""
    from app.services.environment_service import EnvironmentService

    return EnvironmentService(session=session)


async def get_engineering_action_service(
    session: AsyncSession = Depends(get_db),
    version_service: "DevelopmentVersionService" = Depends(get_development_version_service),
    requirement_service: RequirementService = Depends(get_requirement_service),
    context_engine: ProjectContextEngine = Depends(get_context_engine),
    workflow_service: WorkflowService = Depends(get_workflow_service),
    remediation_service: Any = Depends(get_remediation_service),
    static_analysis_service: Any = Depends(get_static_analysis_service),
    ai_test_service: Any = Depends(get_ai_test_service),
    failure_analysis_service: Any = Depends(get_failure_analysis_service),
    sandbox_service: Any = Depends(get_sandbox_service),
    browser_testing_service: Any = Depends(get_browser_testing_service),
    browser_journey_service: Any = Depends(get_browser_journey_service),
    inventory_service: Any = Depends(get_unified_test_inventory_service),
    impact_service: Any = Depends(get_change_impact_service),
    regression_planner: Any = Depends(get_selective_regression_planner),
    regression_executor: Any = Depends(get_regression_execution_service),
    environment_service: Any = Depends(get_environment_service),
) -> "EngineeringActionService":
    """Dependency injecting EngineeringActionService with all domain services."""
    from app.services.engineering_action_service import EngineeringActionService
    from app.services.environment_service import EnvironmentService
    from app.services.verification_service import DevelopmentVerificationService

    return EngineeringActionService(
        session=session,
        version_service=version_service,
        verification_service=DevelopmentVerificationService(),
        requirement_service=requirement_service,
        context_engine=context_engine,
        workflow_service=workflow_service,
        remediation_service=remediation_service,
        static_analysis_service=static_analysis_service,
        ai_test_service=ai_test_service,
        failure_analysis_service=failure_analysis_service,
        sandbox_service=sandbox_service,
        browser_testing_service=browser_testing_service,
        browser_journey_service=browser_journey_service,
        inventory_service=inventory_service,
        impact_service=impact_service,
        regression_planner=regression_planner,
        regression_executor=regression_executor,
        environment_service=environment_service,
    )









