"""Unit tests for Phase 8.2 Explainability & Engineering Insights Agent."""

from datetime import datetime, timezone
import uuid
import pytest

from app.agents.contracts import AgentType
from app.agents.exceptions import AgentValidationError
from app.agents.explainability.agent import ExplainabilityAgent
from app.agents.explainability.contracts import (
    ClaimType,
    EngineeringInsight,
    ExplainabilityCandidate,
    ExplainabilityInput,
    ExplainabilityOutput,
    InsightCategory,
    SourceReference,
)
from app.agents.providers.mock import MockLLMProvider
from app.agents.registry import AgentRegistry, register_default_agents
from app.agents.risk_prediction.contracts import (
    RiskLevel,
    RiskModelProvenance,
    RiskPredictionOutput,
)
from app.agents.code_review.contracts import (
    CodeReviewFinding,
    CodeReviewOutput,
    CodeReviewSummary,
    FindingCategory,
    FindingSeverity,
    FindingSource,
)
from app.schemas.context import ProjectContextResponse, RequirementStatistics
from app.schemas.project import ProjectResponse
from app.schemas.requirement import RequirementResponse


@pytest.fixture
def mock_context():
    project_id = uuid.uuid4()
    req_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    project = ProjectResponse(
        id=project_id,
        name="PlatformInsights",
        slug="platforminsights",
        description="Smart platform for explainability",
        created_at=now,
        updated_at=now,
    )
    req = RequirementResponse(
        id=req_id,
        project_id=project_id,
        title="Secure Data Handling",
        description="Data must be encrypted at rest and in transit.",
        type="FUNCTIONAL",
        priority="HIGH",
        status="APPROVED",
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


@pytest.fixture
def sample_risk_output():
    return RiskPredictionOutput(
        predicted_risk_score=7.4,
        risk_level=RiskLevel.HIGH,
        feature_summary={"active_requirements_count": 10},
        model_provenance=RiskModelProvenance(
            model_name="risk_ridge_v1",
            model_version="1.0.0",
            algorithm="Ridge",
            training_dataset="risk_data.csv",
            feature_schema_version="1.0.0",
            artifact_checksum="abc123checksum",
        ),
        summary="High delivery risk predicted based on requirements scale.",
        limitations=["Empirical model trained on 585 historical projects."],
    )


@pytest.fixture
def sample_code_review_output():
    return CodeReviewOutput(
        agent_id="code-review",
        agent_version="1.0.0",
        summary="Code review flagged critical vulnerability and credential issue.",
        files_reviewed=["auth.py"],
        findings=[
            CodeReviewFinding(
                finding_id="CR-001",
                file_path="auth.py",
                line_start=10,
                line_end=10,
                severity=FindingSeverity.CRITICAL,
                category=FindingCategory.SECURITY,
                source=FindingSource.STATIC_ANALYSIS,
                title="Hardcoded API Credential",
                description="Hardcoded credential discovered.",
                evidence="API_KEY = '***REDACTED_SECRET***'",
                recommendation="Extract credentials into environment secrets.",
                rule_id="SECRET-DETECTION",
            )
        ],
        metrics=CodeReviewSummary(
            files_analyzed_count=1,
            total_findings=1,
            findings_by_severity={"CRITICAL": 1, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0},
            findings_by_category={"SECURITY": 1, "CORRECTNESS": 0, "COMPLEXITY": 0, "ALIGNMENT": 0, "READABILITY": 0},
            static_findings_count=1,
            ai_findings_count=0,
        ),
        limitations=["Static review scoped only to analyzed files."],
    )


# =========================================================================
# 1. Metadata and Initialization
# =========================================================================

def test_agent_metadata():
    agent = ExplainabilityAgent()
    meta = agent.metadata
    assert meta.agent_id == "explainability-insights"
    assert meta.name == "Explainability & Engineering Insights Agent"
    assert meta.version == "1.0.0"
    assert meta.agent_type == AgentType.ANALYSIS
    assert agent.output_schema == ExplainabilityOutput


@pytest.mark.asyncio
async def test_agent_initialize():
    agent = ExplainabilityAgent()
    agent._source_index = {"dummy": "data"}
    await agent.initialize()
    assert agent._source_index == {}


# =========================================================================
# 2. Analyze & Input Validation
# =========================================================================

@pytest.mark.asyncio
async def test_analyze_missing_input_raises(mock_context):
    agent = ExplainabilityAgent()
    with pytest.raises(AgentValidationError, match="requires 'explainability_input'"):
        await agent.analyze(mock_context)


@pytest.mark.asyncio
async def test_analyze_empty_input_raises(mock_context):
    agent = ExplainabilityAgent()
    with pytest.raises(AgentValidationError):
        await agent.analyze(mock_context, explainability_input={})


@pytest.mark.asyncio
async def test_analyze_builds_source_index(mock_context, sample_risk_output):
    agent = ExplainabilityAgent()
    inp = ExplainabilityInput(risk_prediction=sample_risk_output)
    res = await agent.analyze(mock_context, explainability_input=inp)

    assert "source_index" in res
    assert "risk-prediction" in res["source_index"]["available_agents"]
    assert "risk_ridge_v1" in res["source_index"]["valid_entities_by_agent"]["risk-prediction"]


# =========================================================================
# 3. Generate End-to-End & Output Validation
# =========================================================================

@pytest.mark.asyncio
async def test_generate_single_upstream_output(mock_context, sample_risk_output):
    agent = ExplainabilityAgent()
    provider = MockLLMProvider()

    candidate = ExplainabilityCandidate(
        summary="Risk prediction explanation: score 7.4 indicates high project uncertainty.",
        insights=[
            EngineeringInsight(
                insight_id="RAW-001",
                category=InsightCategory.RISK,
                title="Scope Complexity Driving Risk Score",
                summary="The Ridge regression model predicted a high risk level.",
                explanation="Requirements metrics correlate with historical delays in similar projects.",
                source_references=[
                    SourceReference(
                        agent_id="risk-prediction",
                        source_entity_id="risk_ridge_v1",
                        source_field="predicted_risk_score",
                        claim_type=ClaimType.FACT,
                    )
                ],
                suggested_actions=["Perform architectural review and break into smaller sprints."],
            )
        ],
    )
    provider.register_structured_response(candidate)

    inp = ExplainabilityInput(risk_prediction=sample_risk_output)
    analysis = await agent.analyze(mock_context, explainability_input=inp)
    output = await agent.generate(analysis, provider)

    assert isinstance(output, ExplainabilityOutput)
    assert output.agent_id == "explainability-insights"
    assert len(output.insights) == 1
    # ID Normalized sequentially
    assert output.insights[0].insight_id == "INSIGHT-001"
    assert output.metrics.total_insights == 1
    assert output.metrics.analyzed_agents == ["risk-prediction"]
    assert output.metrics.insights_by_category["RISK"] == 1
    assert output.metrics.claims_count_by_type["FACT"] == 1

    # Validate output hook passes
    res = agent.validate_output(output, mock_context)
    assert res.is_valid is True


@pytest.mark.asyncio
async def test_generate_cross_domain_synthesis(
    mock_context, sample_risk_output, sample_code_review_output
):
    agent = ExplainabilityAgent()
    provider = MockLLMProvider()

    candidate = ExplainabilityCandidate(
        summary="Cross-domain synthesis across risk prediction and code review.",
        insights=[
            EngineeringInsight(
                insight_id="RAW-A",
                category=InsightCategory.CROSS_CUTTING,
                title="Security Risk Compounding Project Uncertainty",
                summary="Static analysis credential leak increases risk posture.",
                explanation="The model's high risk score aligns with architectural and security vulnerabilities found in code review.",
                source_references=[
                    SourceReference(
                        agent_id="risk-prediction",
                        source_entity_id="risk_ridge_v1",
                        source_field="predicted_risk_score",
                        claim_type=ClaimType.FACT,
                    ),
                    SourceReference(
                        agent_id="code-review",
                        source_entity_id="CR-001",
                        source_field="severity",
                        claim_type=ClaimType.FACT,
                    ),
                ],
                suggested_actions=["Rotate hardcoded secret immediately and review risk model feature inputs."],
            )
        ],
    )
    provider.register_structured_response(candidate)

    inp = ExplainabilityInput(
        risk_prediction=sample_risk_output,
        code_review=sample_code_review_output,
        target_scope="Authentication Module",
        user_query="How do code findings impact project risk?",
    )
    analysis = await agent.analyze(mock_context, explainability_input=inp)
    output = await agent.generate(analysis, provider)

    assert len(output.insights) == 1
    assert output.insights[0].insight_id == "INSIGHT-001"
    assert output.insights[0].category == InsightCategory.CROSS_CUTTING
    assert len(output.insights[0].source_references) == 2
    assert output.metrics.analyzed_agents == ["code-review", "risk-prediction"]

    val_res = agent.validate_output(output, mock_context)
    assert val_res.is_valid is True


@pytest.mark.asyncio
async def test_generate_filters_phantom_citations(mock_context, sample_risk_output):
    agent = ExplainabilityAgent()
    provider = MockLLMProvider()

    # Candidate contains valid reference AND phantom reference
    candidate = ExplainabilityCandidate(
        summary="Explainability synthesis.",
        insights=[
            EngineeringInsight(
                insight_id="CAND-01",
                category=InsightCategory.RISK,
                title="Valid and Phantom Reference Insight",
                summary="Insight containing both real and fake references.",
                explanation="The LLM attempted to cite an unsupplied agent alongside a real one.",
                source_references=[
                    SourceReference(
                        agent_id="risk-prediction",
                        source_entity_id="risk_ridge_v1",
                        source_field="predicted_risk_score",
                        claim_type=ClaimType.FACT,
                    ),
                    SourceReference(
                        agent_id="code-review",  # Phantom: code-review was NOT provided!
                        source_entity_id="CR-999",
                        source_field="severity",
                        claim_type=ClaimType.FACT,
                    ),
                ],
            )
        ],
    )
    provider.register_structured_response(candidate)

    inp = ExplainabilityInput(risk_prediction=sample_risk_output)
    analysis = await agent.analyze(mock_context, explainability_input=inp)
    output = await agent.generate(analysis, provider)

    # Invariant: phantom reference must be stripped deterministically
    assert len(output.insights) == 1
    refs = output.insights[0].source_references
    assert len(refs) == 1
    assert refs[0].agent_id == "risk-prediction"
    assert not any(r.agent_id == "code-review" for r in refs)

    val_res = agent.validate_output(output, mock_context)
    assert val_res.is_valid is True


@pytest.mark.asyncio
async def test_generate_all_phantom_sources_fails_validation(mock_context, sample_risk_output):
    """Verify that candidate containing only phantom references deterministically fails validation."""
    agent = ExplainabilityAgent()
    provider = MockLLMProvider()

    # Candidate contains ONLY phantom references to unsupplied agent
    candidate = ExplainabilityCandidate(
        summary="Explainability synthesis.",
        insights=[
            EngineeringInsight(
                insight_id="CAND-PHANTOM",
                category=InsightCategory.CODE_REVIEW,
                title="Pure Phantom Insight",
                summary="All references are fake.",
                explanation="References unsupplied agents only.",
                source_references=[
                    SourceReference(
                        agent_id="test-case-generation",  # Not supplied!
                        source_entity_id="TC-999",
                        source_field="test_cases",
                        claim_type=ClaimType.FACT,
                    )
                ],
            )
        ],
    )
    provider.register_structured_response(candidate)

    inp = ExplainabilityInput(risk_prediction=sample_risk_output)
    analysis = await agent.analyze(mock_context, explainability_input=inp)

    # Invariant: Must fail with AgentValidationError, never manufacture a fallback insight
    with pytest.raises(AgentValidationError) as exc_info:
        await agent.generate(analysis, provider)

    assert "All candidate insights failed deterministic source validation" in str(exc_info.value)


@pytest.mark.asyncio
async def test_generate_all_invalid_candidate_fails_validation(mock_context, sample_risk_output):
    """Verify that candidate with empty or invalid insights deterministically fails validation."""
    agent = ExplainabilityAgent()
    provider = MockLLMProvider()

    # Candidate with empty insights
    candidate = ExplainabilityCandidate(
        summary="Candidate with no insights.",
        insights=[],
    )
    provider.register_structured_response(candidate)

    inp = ExplainabilityInput(risk_prediction=sample_risk_output)
    analysis = await agent.analyze(mock_context, explainability_input=inp)

    with pytest.raises(AgentValidationError):
        await agent.generate(analysis, provider)


@pytest.mark.asyncio
async def test_preserves_secret_redaction(mock_context, sample_code_review_output):
    agent = ExplainabilityAgent()
    provider = MockLLMProvider()

    candidate = ExplainabilityCandidate(
        summary="Security review highlights API secret redaction.",
        insights=[
            EngineeringInsight(
                insight_id="INS-01",
                category=InsightCategory.CODE_REVIEW,
                title="Credential Redaction Preserved",
                summary="Static analysis detected hardcoded credential.",
                explanation="Evidence confirms token was masked as ***REDACTED_SECRET*** in upstream review.",
                source_references=[
                    SourceReference(
                        agent_id="code-review",
                        source_entity_id="CR-001",
                        source_field="evidence",
                        claim_type=ClaimType.FACT,
                    )
                ],
                suggested_actions=["Use environment variables."],
            )
        ],
    )
    provider.register_structured_response(candidate)

    inp = ExplainabilityInput(code_review=sample_code_review_output)
    analysis = await agent.analyze(mock_context, explainability_input=inp)
    output = await agent.generate(analysis, provider)

    assert len(output.insights) == 1
    assert "***REDACTED_SECRET***" in output.insights[0].explanation


# =========================================================================
# 4. Registry Integration
# =========================================================================

def test_registry_integration():
    registry = AgentRegistry()
    register_default_agents(registry)

    assert registry.has("explainability-insights")
    agent = registry.get("explainability-insights")
    assert isinstance(agent, ExplainabilityAgent)
    assert agent.metadata.agent_id == "explainability-insights"
    assert len(registry.list_agents()) == 9

    # Idempotent registration check
    register_default_agents(registry)
    assert len(registry.list_agents()) == 9


# =========================================================================
# 5. Full Platform 8-Agent Synthesis & Edge Cases
# =========================================================================

from app.agents.requirement_analysis.contracts import (
    RequirementAnalysisOutput,
    RequirementAmbiguity,
    RequirementConflict,
    MissingInformation,
    RequirementRefinement,
    ScopeClarification,
    AnalysisSeverity,
)
from app.agents.architecture_recommendation.contracts import (
    ArchitectureRecommendationOutput,
    ArchitectureStyleRecommendation,
    ArchitectureStyle,
    ComponentRecommendation,
    DataFlowRecommendation,
    TechnologyRecommendation,
    TechnologyCategory,
    TradeOffAnalysis,
)
from app.agents.database_design.contracts import (
    DatabaseDesignOutput,
    DatabaseParadigm,
    EntityRecommendation,
    AttributeRecommendation,
    DataType,
    PrimaryKeyRecommendation,
)
from app.agents.timeline_prediction.contracts import (
    TimelinePredictionOutput,
    TimelineModelProvenance,
)
from app.agents.bug_prediction.contracts import (
    BugPredictionOutput,
    BugModelProvenance,
    DefectPredictionLabel,
)
from app.agents.test_case_generation.contracts import (
    TestCaseGenerationOutput,
    TestCase,
    TestCaseCoverage,
    TestType,
    TestPriority,
    TestStep,
)


@pytest.fixture
def full_platform_input(sample_risk_output, sample_code_review_output):
    req_uuid1 = uuid.uuid4()
    req_uuid2 = uuid.uuid4()

    ra = RequirementAnalysisOutput(
        summary="Requirement analysis completed.",
        completeness_score=85.0,
        active_requirements_count=2,
        total_requirements_count=2,
        ambiguities=[
            RequirementAmbiguity(
                requirement_id=req_uuid1,
                issue="Vague throughput requirement",
                explanation="Does not specify requests per second.",
                suggested_clarification="Specify target RPS.",
                severity=AnalysisSeverity.MEDIUM,
            )
        ],
        conflicts=[
            RequirementConflict(
                requirement_id=req_uuid1,
                related_requirement_id=req_uuid2,
                issue="Security vs Speed",
                explanation="Conflicting requirements",
                severity=AnalysisSeverity.HIGH,
            )
        ],
        missing_information=[
            MissingInformation(
                area="Rate Limiting",
                description="No rate limit defined.",
                reason="Needed to prevent DDoS.",
                severity=AnalysisSeverity.MEDIUM,
            )
        ],
        refinements=[
            RequirementRefinement(
                requirement_id=req_uuid1,
                suggestion="Handle 1000 RPS peak load",
                reason="Needed to define performance tests",
            )
        ],
        scope_clarifications=[
            ScopeClarification(
                topic="Rate Limiting Scope",
                question="Apply globally or per user?",
                rationale="Affects gateway architecture",
            )
        ],
        assumptions=[],
        constraints_identified=[],
        next_steps=[],
    )

    arch = ArchitectureRecommendationOutput(
        summary="Architecture recommendation: event-driven modular design.",
        architecture_styles=[
            ArchitectureStyleRecommendation(
                style=ArchitectureStyle.EVENT_DRIVEN,
                rationale="High throughput decoupling",
            )
        ],
        components=[
            ComponentRecommendation(
                name="GatewayService",
                responsibility="Ingress routing and validation",
                reason="Single entry point",
                related_requirement_ids=[req_uuid1],
            )
        ],
        data_flows=[
            DataFlowRecommendation(
                source_component="GatewayService",
                target_component="ProcessingService",
                interaction="gRPC",
                reason="Low latency IPC",
            )
        ],
        technologies=[
            TechnologyRecommendation(
                technology="FastAPI",
                category=TechnologyCategory.BACKEND,
                reason="Async high throughput",
                trade_off="Python GIL for compute tasks",
            )
        ],
        trade_offs=[
            TradeOffAnalysis(
                decision_area="Data Ingestion",
                recommended_option="Event Stream",
                advantages=["Decoupled", "Scalable"],
                disadvantages=["Eventual consistency"],
                alternative="Synchronous REST",
                alternative_tradeoff="Simpler but tight coupling",
            )
        ],
        assumptions=[],
        constraints=[],
        unknowns=[],
        traceability_matrix=[],
    )

    db = DatabaseDesignOutput(
        summary="Relational database schema with audit tables.",
        database_paradigm=DatabaseParadigm.RELATIONAL,
        entities=[
            EntityRecommendation(
                name="accounts",
                description="User account profiles",
                purpose="Identity management",
                attributes=[
                    AttributeRecommendation(
                        name="id",
                        data_type=DataType.UUID,
                        description="Account identifier",
                    )
                ],
                primary_key=PrimaryKeyRecommendation(attributes=["id"]),
            )
        ],
        relationships=[],
        indexes=[],
        constraints=[],
        trade_offs=[],
        assumptions=[],
        constraints_notes=[],
        unknowns=[],
        requirement_traceability=[],
        architecture_traceability=[],
    )

    tp = TimelinePredictionOutput(
        summary="Estimated delivery: 4.0 months.",
        predicted_duration_months=4.0,
        estimated_duration_months=4.0,
        target="duration_months",
        target_unit="months",
        feature_names=["function_points"],
        feature_summary={"function_points": 250.0},
        model_provenance=TimelineModelProvenance(
            model_name="timeline_rf_v1",
            model_version="1.0.0",
            algorithm="RandomForestRegressor",
            training_dataset="timeline_data.csv",
            feature_schema_version="1.0.0",
            artifact_checksum="checksum_tp",
        ),
        limitations=["Timeline RF trained on historical waterfall/agile hybrid data."],
    )

    bp = BugPredictionOutput(
        summary="Gateway component classified as low defect risk.",
        prediction_label=DefectPredictionLabel.NON_DEFECTIVE,
        predicted_probability=0.22,
        target="is_bug_prone",
        feature_names=["loc", "cyclomatic_complexity"],
        feature_summary={"loc": 450, "cyclomatic_complexity": 8},
        model_provenance=BugModelProvenance(
            model_name="bug_logreg_v1",
            model_version="1.0.0",
            algorithm="LogisticRegression",
            training_dataset="bug_data.csv",
            feature_schema_version="1.0.0",
            artifact_checksum="checksum_bp",
        ),
        limitations=["Bug classification uses static complexity features."],
    )

    tc = TestCaseGenerationOutput(
        summary="Comprehensive test cases generated across unit and integration.",
        test_cases=[
            TestCase(
                test_case_id="TC-001",
                title="Verify Gateway Ingress Validation",
                description="Ensure invalid payloads are rejected with 400 Bad Request.",
                test_type=TestType.INTEGRATION,
                priority=TestPriority.HIGH,
                preconditions=["Gateway running"],
                steps=[
                    TestStep(
                        step_number=1,
                        action="Send malformed payload",
                        expected_behavior="400 Bad Request",
                    )
                ],
                expected_result="Immediate rejection",
                requirement_ids=[str(req_uuid1)],
            )
        ],
        total_test_cases=1,
        coverage=TestCaseCoverage(
            total_active_requirements=1,
            requirements_with_tests=1,
            requirements_without_tests=0,
            coverage_percentage=100.0,
            uncovered_requirement_ids=[],
        ),
        limitations=["Test cases generated without dynamic runtime execution."],
    )

    return ExplainabilityInput(
        requirement_analysis=ra,
        architecture_recommendation=arch,
        database_design=db,
        risk_prediction=sample_risk_output,
        timeline_prediction=tp,
        bug_prediction=bp,
        test_case_generation=tc,
        code_review=sample_code_review_output,
        target_scope="Core Banking Ingress",
        user_query="Synthesize architectural feasibility against predicted delivery timeline and risk.",
    )


@pytest.mark.asyncio
async def test_generate_all_eight_agents_synthesis(mock_context, full_platform_input):
    """Verify ExplainabilityAgent synthesizes findings across all 8 upstream agents."""
    agent = ExplainabilityAgent()
    provider = MockLLMProvider()

    candidate = ExplainabilityCandidate(
        summary="Full spectrum cross-agent synthesis across all 8 platform agents.",
        insights=[
            EngineeringInsight(
                insight_id="SYNTH-01",
                category=InsightCategory.CROSS_CUTTING,
                title="End-to-End Delivery & Architecture Feasibility",
                summary="Event-driven architecture and thorough test suite balance predicted risk score.",
                explanation=(
                    "The timeline model predicts 4.0 months duration while the risk prediction model "
                    "identifies elevated risk (7.4 score). Concurrently, code review detected a hardcoded secret in auth.py "
                    "which must be remediated to ensure alignment with active requirements."
                ),
                source_references=[
                    SourceReference(
                        agent_id="requirement-analysis",
                        source_entity_id=None,
                        source_field="completeness_score",
                        claim_type=ClaimType.FACT,
                    ),
                    SourceReference(
                        agent_id="architecture-recommendation",
                        source_entity_id="GatewayService",
                        source_field="components",
                        claim_type=ClaimType.FACT,
                    ),
                    SourceReference(
                        agent_id="database-design",
                        source_entity_id="accounts",
                        source_field="entities",
                        claim_type=ClaimType.FACT,
                    ),
                    SourceReference(
                        agent_id="risk-prediction",
                        source_entity_id="risk_ridge_v1",
                        source_field="predicted_risk_score",
                        claim_type=ClaimType.FACT,
                    ),
                    SourceReference(
                        agent_id="timeline-prediction",
                        source_entity_id="timeline_rf_v1",
                        source_field="predicted_duration_months",
                        claim_type=ClaimType.FACT,
                    ),
                    SourceReference(
                        agent_id="bug-prediction",
                        source_entity_id="bug_logreg_v1",
                        source_field="prediction_label",
                        claim_type=ClaimType.FACT,
                    ),
                    SourceReference(
                        agent_id="test-case-generation",
                        source_entity_id="TC-001",
                        source_field="test_cases",
                        claim_type=ClaimType.FACT,
                    ),
                    SourceReference(
                        agent_id="code-review",
                        source_entity_id="CR-001",
                        source_field="severity",
                        claim_type=ClaimType.FACT,
                    ),
                ],
                suggested_actions=[
                    "Resolve hardcoded credential immediately.",
                    "Review timeline assumptions in light of risk model predictions.",
                ],
            )
        ],
    )
    provider.register_structured_response(candidate)

    analysis = await agent.analyze(mock_context, explainability_input=full_platform_input)
    assert len(analysis["source_index"]["available_agents"]) == 8

    output = await agent.generate(analysis, provider)

    assert len(output.insights) == 1
    assert output.insights[0].insight_id == "INSIGHT-001"
    assert len(output.insights[0].source_references) == 8
    assert output.metrics.total_insights == 1
    assert len(output.metrics.analyzed_agents) == 8
    assert len(output.limitations) >= 4

    val_res = agent.validate_output(output, mock_context)
    assert val_res.is_valid is True


@pytest.mark.asyncio
async def test_analyze_with_raw_dict_and_invalid_type(mock_context, sample_risk_output):
    """Verify analyze handles raw dictionary and rejects unsupported types."""
    agent = ExplainabilityAgent()

    # 1. Valid raw dict input
    raw_dict = {"risk_prediction": sample_risk_output.model_dump()}
    analysis = await agent.analyze(mock_context, explainability_input=raw_dict)
    assert "risk-prediction" in analysis["source_index"]["available_agents"]

    # 2. Invalid dict that fails Pydantic validation
    with pytest.raises(AgentValidationError, match="Invalid ExplainabilityInput payload"):
        await agent.analyze(mock_context, explainability_input={"invalid_key": "bad"})

    # 3. Invalid input type (not dict, not ExplainabilityInput)
    with pytest.raises(AgentValidationError, match="must be an ExplainabilityInput instance or valid dictionary"):
        await agent.analyze(mock_context, explainability_input=12345)


@pytest.mark.asyncio
async def test_generate_handles_dict_candidate_and_filters_invalid_insights(
    mock_context, sample_risk_output
):
    """Verify generate handles raw dict candidates, filters invalid insights, and drops duplicate/blank items."""
    agent = ExplainabilityAgent()
    provider = MockLLMProvider()

    raw_dict_candidate = {
        "summary": "Raw dict candidate summary.",
        "insights": [
            # 1. Valid insight
            {
                "insight_id": "RAW-01",
                "category": "RISK",
                "title": "Valid Risk Insight",
                "summary": "Valid summary.",
                "explanation": "Valid detailed explanation.",
                "source_references": [
                    {
                        "agent_id": "risk-prediction",
                        "source_entity_id": "risk_ridge_v1",
                        "source_field": "predicted_risk_score",
                        "claim_type": "FACT",
                    }
                ],
                "suggested_actions": ["Action 1"],
            },
            # 2. Blank title (must be discarded)
            {
                "insight_id": "RAW-02",
                "category": "RISK",
                "title": "   ",
                "summary": "Summary",
                "explanation": "Explanation",
                "source_references": [
                    {
                        "agent_id": "risk-prediction",
                        "claim_type": "FACT",
                    }
                ],
            },
            # 3. Duplicate fingerprint (same category and title, must be discarded)
            {
                "insight_id": "RAW-03",
                "category": "RISK",
                "title": "Valid Risk Insight",
                "summary": "Duplicate summary",
                "explanation": "Duplicate explanation",
                "source_references": [
                    {
                        "agent_id": "risk-prediction",
                        "claim_type": "FACT",
                    }
                ],
            },
            # 4. Insight referencing non-existent entity and field
            {
                "insight_id": "RAW-04",
                "category": "RISK",
                "title": "Invalid Entity and Field Insight",
                "summary": "Summary",
                "explanation": "Explanation",
                "source_references": [
                    {
                        "agent_id": "risk-prediction",
                        "source_entity_id": "NON_EXISTENT_ENTITY",
                        "source_field": "predicted_risk_score",
                        "claim_type": "FACT",
                    },
                    {
                        "agent_id": "risk-prediction",
                        "source_entity_id": "risk_ridge_v1",
                        "source_field": "NON_EXISTENT_FIELD",
                        "claim_type": "FACT",
                    },
                ],
            },
        ],
    }
    from unittest.mock import AsyncMock
    provider.generate_structured = AsyncMock(return_value=raw_dict_candidate)

    inp = ExplainabilityInput(risk_prediction=sample_risk_output)
    analysis = await agent.analyze(mock_context, explainability_input=inp)
    output = await agent.generate(analysis, provider)

    # Only insight 1 should survive!
    assert len(output.insights) == 1
    assert output.insights[0].insight_id == "INSIGHT-001"
    assert output.insights[0].title == "Valid Risk Insight"

    val_res = agent.validate_output(output, mock_context)
    assert val_res.is_valid is True
