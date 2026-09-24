"""Unit and Integration tests for Predefined Workflow Pipelines.

Tests SoftwareDesignWorkflow, ProjectEstimationWorkflow, and ComprehensiveAuditWorkflow.
"""

import uuid
from datetime import datetime, timezone
import pytest

from app.agents.architecture_recommendation.contracts import (
    ArchitectureRecommendationCandidate,
    ArchitectureStyle,
    ArchitectureStyleRecommendation,
    ComponentRecommendation,
)
from app.agents.code_review.contracts import (
    CodeFile,
    CodeReviewCandidate,
    CodeReviewFinding,
    CodeReviewInput,
    FindingCategory,
    FindingSeverity,
    FindingSource,
)
from app.agents.database_design.contracts import (
    AttributeRecommendation,
    DatabaseDesignCandidate,
    DatabaseParadigm,
    DataType,
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
from app.agents.registry import AgentRegistry, register_default_agents
from app.agents.requirement_analysis.contracts import RequirementAnalysisCandidate
from app.agents.test_case_generation.contracts import (
    TestCase,
    TestCaseGenerationCandidate,
    TestPriority,
    TestStep,
    TestType,
)
from app.schemas.context import ProjectContextResponse, RequirementStatistics
from app.schemas.project import ProjectResponse
from app.schemas.requirement import RequirementPriority, RequirementResponse, RequirementStatus, RequirementType
from app.workflows.contracts import (
    WorkflowInput,
    WorkflowResult,
    WorkflowStatus,
    WorkflowStepStatus,
)
from app.workflows.coordinator import WorkflowCoordinator
from app.workflows.pipelines import (
    WORKFLOW_COMPREHENSIVE_AUDIT_ID,
    WORKFLOW_PROJECT_ESTIMATION_ID,
    WORKFLOW_SOFTWARE_DESIGN_ID,
    build_comprehensive_audit_workflow,
    build_project_estimation_workflow,
    build_software_design_workflow,
)


@pytest.fixture
def sample_context() -> ProjectContextResponse:
    project_id = uuid.uuid4()
    req_id = uuid.uuid4()
    return ProjectContextResponse(
        project=ProjectResponse(
            id=project_id,
            name="SE Workflow Core",
            slug="se-workflow-core",
            description="Testing enterprise workflows",
            settings={
                "ml_risk_inputs": {
                    "project_size": "Medium",
                    "team_experience_level": "High",
                    "estimated_effort_hours": 950.0,
                    "complexity_level": "High",
                    "requirement_stability": "Moderate",
                },
                "ml_timeline_inputs": {
                    "afp": 480.0,
                    "input_count": 55.0,
                    "output_count": 40.0,
                    "enquiry_count": 30.0,
                    "file_count": 25.0,
                    "interface_count": 15.0,
                    "resource_level": 2,
                },
                "ml_bug_inputs": {
                    "loc": 45.0,
                    "v(g)": 7.0,
                    "ev(g)": 3.0,
                    "iv(g)": 4.0,
                    "n": 120.0,
                    "v": 650.0,
                    "l": 0.05,
                    "d": 20.0,
                    "i": 32.5,
                    "e": 13000.0,
                    "b": 0.22,
                    "t": 722.0,
                    "lOCode": 35.0,
                    "lOComment": 5.0,
                    "lOBlank": 5.0,
                    "locCodeAndComment": 2.0,
                    "uniq_Op": 18.0,
                    "uniq_Opnd": 25.0,
                    "total_Op": 70.0,
                    "total_Opnd": 50.0,
                    "branchCount": 13.0,
                },
            },
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        ),
        requirements=[
            RequirementResponse(
                id=req_id,
                project_id=project_id,
                title="User Authentication",
                description="The system shall authenticate users via OAuth2 credentials.",
                type=RequirementType.FUNCTIONAL,
                priority=RequirementPriority.HIGH,
                status=RequirementStatus.APPROVED,
                is_archived=False,
                version=1,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        ],
        statistics=RequirementStatistics(
            total_requirements=1,
            active_requirements=1,
            functional_count=1,
            non_functional_count=0,
            constraint_count=0,
            completion_percentage=0.0,
        ),
        context_version=1,
        generated_at=datetime.now(timezone.utc),
    )


def create_realistic_mock_provider(
    req_id: uuid.UUID, include_code_review: bool = True
) -> MockLLMProvider:
    """Creates a MockLLMProvider configured with valid schema outputs for all LLM agents."""
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
                name="AuthService",
                responsibility="Manage user authentication and tokens.",
                reason="Satisfies OAuth2 requirement.",
                related_requirement_ids=[req_id],
            )
        ],
        data_flows=[],
        technologies=[],
        trade_offs=[],
        assumptions=["Low scale initial deployment"],
        constraints=["Python 3.12+"],
        unknowns=[],
        traceability_matrix=[],
    )

    db_candidate = DatabaseDesignCandidate(
        summary="Relational database design modeling Users.",
        database_paradigm=DatabaseParadigm.RELATIONAL,
        entities=[
            EntityRecommendation(
                name="User",
                description="User account records",
                purpose="User identity",
                attributes=[
                    AttributeRecommendation(
                        name="id",
                        data_type=DataType.UUID,
                        nullable=False,
                        description="User ID",
                        unique=True,
                    ),
                    AttributeRecommendation(
                        name="email",
                        data_type=DataType.STRING,
                        nullable=False,
                        description="Email",
                        unique=True,
                    ),
                ],
                primary_key=PrimaryKeyRecommendation(attributes=["id"], is_composite=False),
                related_requirement_ids=[req_id],
            )
        ],
        relationships=[],
        indexes=[],
        constraints=[],
        assumptions=[],
        trade_offs=[],
    )

    test_case_candidate = TestCaseGenerationCandidate(
        summary="Generated comprehensive test cases.",
        test_cases=[
            TestCase(
                test_case_id="TC-001",
                title="OAuth2 Login Success",
                description="Verify successful login with valid OAuth2 credentials",
                test_type=TestType.FUNCTIONAL,
                priority=TestPriority.HIGH,
                preconditions=[],
                steps=[
                    TestStep(
                        step_number=1,
                        action="Submit valid OAuth token",
                        expected_behavior="Returns 200 OK and JWT session",
                    )
                ],
                expected_result="Returns 200 OK and JWT session",
                requirement_ids=[str(req_id)],
            )
        ],
    )

    code_review_candidate = CodeReviewCandidate(
        summary="AI code review findings summary.",
        findings=[
            CodeReviewFinding(
                finding_id="CR-001",
                file_path="main.py",
                line_start=1,
                line_end=1,
                severity=FindingSeverity.INFO,
                category=FindingCategory.READABILITY,
                source=FindingSource.AI_REVIEW,
                title="Code structure",
                description="Clean modular code structure.",
                evidence="def login():",
                recommendation="Add function docstring.",
            )
        ],
    )

    explainability_candidate = ExplainabilityCandidate(
        summary="Engineering synthesis across architecture and database design.",
        insights=[
            EngineeringInsight(
                insight_id="INSIGHT-001",
                category=InsightCategory.CROSS_CUTTING,
                title="Modular Architecture Alignment",
                summary="Architecture aligns with requirements.",
                explanation="The AuthService component cleanly supports OAuth2 authentication.",
                source_references=[
                    SourceReference(
                        agent_id="requirement-analysis",
                        source_entity_id=str(req_id),
                        source_field="summary",
                        claim_type=ClaimType.FACT,
                    )
                ],
                suggested_actions=["Implement OAuth2 token verification middleware in FastAPI."],
            )
        ],
    )

    provider = MockLLMProvider()
    candidates = [req_candidate, arch_candidate, db_candidate, test_case_candidate]
    if include_code_review:
        candidates.append(code_review_candidate)
    candidates.append(explainability_candidate)

    for candidate in candidates:
        provider.register_structured_response(candidate)
    return provider


class TestSoftwareDesignWorkflow:
    def test_workflow_definition_structure(self) -> None:
        wf = build_software_design_workflow()
        assert wf.workflow_id == WORKFLOW_SOFTWARE_DESIGN_ID
        assert len(wf.steps) == 3
        assert wf.steps[0].step_id == "requirement-analysis"
        assert wf.steps[0].required is True
        assert wf.steps[1].step_id == "architecture-recommendation"
        assert wf.steps[1].required is False
        assert wf.steps[2].step_id == "database-design"
        assert wf.steps[2].required is True

    @pytest.mark.asyncio
    async def test_software_design_workflow_normal_success(
        self, sample_context: ProjectContextResponse
    ) -> None:
        req_id = sample_context.requirements[0].id
        provider = create_realistic_mock_provider(req_id)
        executor = AgentExecutor(provider=provider)

        registry = AgentRegistry()
        register_default_agents(registry)

        coordinator = WorkflowCoordinator(executor=executor, registry=registry)
        workflow = build_software_design_workflow()
        wf_input = WorkflowInput(context=sample_context)

        result: WorkflowResult = await coordinator.execute(workflow, wf_input)

        assert result.status == WorkflowStatus.COMPLETED
        assert len(result.step_results) == 3
        assert result.step_results[0].status == WorkflowStepStatus.COMPLETED
        assert result.step_results[1].status == WorkflowStepStatus.COMPLETED
        assert result.step_results[2].status == WorkflowStepStatus.COMPLETED

        # Verify artifacts were preserved in memory
        assert "requirement-analysis" in result.artifacts
        assert "architecture-recommendation" in result.artifacts
        assert "database-design" in result.artifacts


class TestProjectEstimationWorkflow:
    def test_workflow_definition_structure(self) -> None:
        wf = build_project_estimation_workflow()
        assert wf.workflow_id == WORKFLOW_PROJECT_ESTIMATION_ID
        assert len(wf.steps) == 3
        assert wf.steps[0].step_id == "risk-prediction"
        assert wf.steps[1].step_id == "timeline-prediction"
        assert wf.steps[2].step_id == "bug-prediction"

    @pytest.mark.asyncio
    async def test_project_estimation_workflow_all_success(
        self, sample_context: ProjectContextResponse
    ) -> None:
        provider = MockLLMProvider()
        executor = AgentExecutor(provider=provider)

        registry = AgentRegistry()
        register_default_agents(registry)

        coordinator = WorkflowCoordinator(executor=executor, registry=registry)
        workflow = build_project_estimation_workflow()
        wf_input = WorkflowInput(context=sample_context)

        result: WorkflowResult = await coordinator.execute(workflow, wf_input)

        assert result.status == WorkflowStatus.COMPLETED
        assert len(result.step_results) == 3
        assert result.step_results[0].status == WorkflowStepStatus.COMPLETED
        assert result.step_results[1].status == WorkflowStepStatus.COMPLETED
        assert result.step_results[2].status == WorkflowStepStatus.COMPLETED

        assert "risk-prediction" in result.artifacts
        assert "timeline-prediction" in result.artifacts
        assert "bug-prediction" in result.artifacts


class TestComprehensiveAuditWorkflow:
    def test_workflow_definition_structure(self) -> None:
        wf = build_comprehensive_audit_workflow()
        assert wf.workflow_id == WORKFLOW_COMPREHENSIVE_AUDIT_ID
        assert len(wf.steps) == 9

    @pytest.mark.asyncio
    async def test_comprehensive_audit_workflow_missing_code_review_skips_cleanly(
        self, sample_context: ProjectContextResponse
    ) -> None:
        req_id = sample_context.requirements[0].id
        provider = create_realistic_mock_provider(req_id, include_code_review=False)
        executor = AgentExecutor(provider=provider)

        registry = AgentRegistry()
        register_default_agents(registry)

        coordinator = WorkflowCoordinator(executor=executor, registry=registry)
        workflow = build_comprehensive_audit_workflow()

        # No code_review_input provided
        wf_input = WorkflowInput(context=sample_context, code_review_input=None)

        result: WorkflowResult = await coordinator.execute(workflow, wf_input)

        # Since code-review was optional and skipped, but other steps completed, status is PARTIAL_SUCCESS
        assert result.status == WorkflowStatus.PARTIAL_SUCCESS

        step_map = {s.step_id: s for s in result.step_results}
        assert step_map["code-review"].status == WorkflowStepStatus.SKIPPED
        assert "CodeReviewInput was not provided" in (step_map["code-review"].skip_reason or "")

        # Explainability still ran successfully using the remaining available outputs!
        assert step_map["explainability-insights"].status == WorkflowStepStatus.COMPLETED
        assert "explainability-insights" in result.artifacts

    @pytest.mark.asyncio
    async def test_comprehensive_audit_workflow_with_code_review_completes_all(
        self, sample_context: ProjectContextResponse
    ) -> None:
        req_id = sample_context.requirements[0].id
        provider = create_realistic_mock_provider(req_id)
        executor = AgentExecutor(provider=provider)

        registry = AgentRegistry()
        register_default_agents(registry)

        coordinator = WorkflowCoordinator(executor=executor, registry=registry)
        workflow = build_comprehensive_audit_workflow()

        # Provide valid code_review_input
        code_input = CodeReviewInput(
            files=[
                CodeFile(
                    file_path="main.py",
                    language="python",
                    content="def login():\n    pass\n",
                )
            ]
        )
        wf_input = WorkflowInput(context=sample_context, code_review_input=code_input)

        result: WorkflowResult = await coordinator.execute(workflow, wf_input)

        assert result.status == WorkflowStatus.COMPLETED
        for step in result.step_results:
            assert step.status == WorkflowStepStatus.COMPLETED, f"Step {step.step_id} failed"

    @pytest.mark.asyncio
    async def test_software_design_workflow_requirement_failure_halts_downstream(
        self, sample_context: ProjectContextResponse
    ) -> None:
        provider = MockLLMProvider()
        provider.simulate_permanent_failure(RuntimeError("LLM quota exceeded for requirements"))
        executor = AgentExecutor(provider=provider)

        registry = AgentRegistry()
        register_default_agents(registry)

        coordinator = WorkflowCoordinator(executor=executor, registry=registry)
        workflow = build_software_design_workflow()
        wf_input = WorkflowInput(context=sample_context)

        result: WorkflowResult = await coordinator.execute(workflow, wf_input)

        assert result.status == WorkflowStatus.FAILED
        step_map = {s.step_id: s for s in result.step_results}
        assert step_map["requirement-analysis"].status == WorkflowStepStatus.FAILED
        assert step_map["architecture-recommendation"].status == WorkflowStepStatus.SKIPPED
        assert step_map["database-design"].status == WorkflowStepStatus.SKIPPED

    @pytest.mark.asyncio
    async def test_software_design_workflow_architecture_failure_allows_database_fallback(
        self, sample_context: ProjectContextResponse
    ) -> None:
        req_id = sample_context.requirements[0].id
        req_candidate = RequirementAnalysisCandidate(
            summary="Verified requirement analysis summary.",
            ambiguities=[],
            conflicts=[],
            missing_information=[],
            refinements=[],
            scope_clarifications=[],
        )
        db_candidate = DatabaseDesignCandidate(
            summary="Relational database design modeling Users.",
            database_paradigm=DatabaseParadigm.RELATIONAL,
            entities=[
                EntityRecommendation(
                    name="User",
                    description="User account records",
                    purpose="User identity",
                    attributes=[
                        AttributeRecommendation(
                            name="id",
                            data_type=DataType.UUID,
                            nullable=False,
                            description="User ID",
                            unique=True,
                        ),
                    ],
                    primary_key=PrimaryKeyRecommendation(attributes=["id"], is_composite=False),
                    related_requirement_ids=[req_id],
                )
            ],
            relationships=[],
            indexes=[],
            constraints=[],
            assumptions=[],
            trade_offs=[],
        )

        import json

        provider = MockLLMProvider()
        # Step 1: requirement-analysis succeeds
        provider.register_response(json.dumps(req_candidate.model_dump(mode="json")))
        # Step 2: architecture-recommendation fails with invalid response string
        provider.register_response("INVALID_NOT_JSON")
        # Step 3: database-design succeeds
        provider.register_response(json.dumps(db_candidate.model_dump(mode="json")))

        executor = AgentExecutor(provider=provider)
        registry = AgentRegistry()
        register_default_agents(registry)

        coordinator = WorkflowCoordinator(executor=executor, registry=registry)
        workflow = build_software_design_workflow()
        wf_input = WorkflowInput(context=sample_context)

        result: WorkflowResult = await coordinator.execute(workflow, wf_input)

        # Requirement (required) succeeded, Architecture (optional) failed, Database (required) succeeded -> PARTIAL_SUCCESS
        assert result.status == WorkflowStatus.PARTIAL_SUCCESS
        step_map = {s.step_id: s for s in result.step_results}
        assert step_map["requirement-analysis"].status == WorkflowStepStatus.COMPLETED
        assert step_map["architecture-recommendation"].status == WorkflowStepStatus.FAILED
        assert step_map["database-design"].status == WorkflowStepStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_project_estimation_workflow_single_failure_yields_partial_success(
        self, sample_context: ProjectContextResponse
    ) -> None:
        # Context without ml_risk_inputs will cause risk-prediction to fail, while timeline and bug succeed
        broken_settings = dict(sample_context.project.settings)
        del broken_settings["ml_risk_inputs"]
        sample_context.project.settings = broken_settings

        provider = MockLLMProvider()
        executor = AgentExecutor(provider=provider)

        registry = AgentRegistry()
        register_default_agents(registry)

        coordinator = WorkflowCoordinator(executor=executor, registry=registry)
        workflow = build_project_estimation_workflow()
        wf_input = WorkflowInput(context=sample_context)

        result: WorkflowResult = await coordinator.execute(workflow, wf_input)

        assert result.status == WorkflowStatus.PARTIAL_SUCCESS
        step_map = {s.step_id: s for s in result.step_results}
        assert step_map["risk-prediction"].status == WorkflowStepStatus.FAILED
        assert step_map["timeline-prediction"].status == WorkflowStepStatus.COMPLETED
        assert step_map["bug-prediction"].status == WorkflowStepStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_project_estimation_workflow_all_failures_yields_failed(
        self, sample_context: ProjectContextResponse
    ) -> None:
        # Context without any ML inputs will cause all 3 prediction agents to fail
        sample_context.project.settings = {}

        provider = MockLLMProvider()
        executor = AgentExecutor(provider=provider)

        registry = AgentRegistry()
        register_default_agents(registry)

        coordinator = WorkflowCoordinator(executor=executor, registry=registry)
        workflow = build_project_estimation_workflow()
        wf_input = WorkflowInput(context=sample_context)

        result: WorkflowResult = await coordinator.execute(workflow, wf_input)

        assert result.status == WorkflowStatus.FAILED
        for step in result.step_results:
            assert step.status == WorkflowStepStatus.FAILED

    @pytest.mark.asyncio
    async def test_comprehensive_audit_workflow_no_upstream_success_skips_explainability(
        self, sample_context: ProjectContextResponse
    ) -> None:
        # Simulate failure for all LLM agents and clear settings for ML agents
        sample_context.project.settings = {}
        provider = MockLLMProvider()
        provider.simulate_permanent_failure(RuntimeError("Universal LLM failure"))
        executor = AgentExecutor(provider=provider)

        registry = AgentRegistry()
        register_default_agents(registry)

        coordinator = WorkflowCoordinator(executor=executor, registry=registry)
        workflow = build_comprehensive_audit_workflow()
        wf_input = WorkflowInput(context=sample_context, code_review_input=None)

        result: WorkflowResult = await coordinator.execute(workflow, wf_input)

        assert result.status == WorkflowStatus.FAILED
        step_map = {s.step_id: s for s in result.step_results}
        assert step_map["explainability-insights"].status == WorkflowStepStatus.SKIPPED
        assert "No upstream agent outputs available" in (step_map["explainability-insights"].skip_reason or "")
