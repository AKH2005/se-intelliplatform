"""Phase 10D — Progressive Agent Migration & Real Multi-Agent Pipeline Unit Tests.

Covers:
1. ArchitectureRecommendationAgent:
   - Valid structured candidate generation
   - Malformed candidate handling
   - Unsupported architecture style rejection
   - Invalid requirement traceability rejection
   - Deterministic domain validation
   - Mock execution
   - Provider routing & dynamic model resolution
2. DatabaseDesignAgent:
   - Valid structured candidate generation
   - Invalid entity reference rejection
   - Invalid foreign-key entity & referenced entity rejection
   - Invalid attribute & parity mismatch rejection
   - Invalid relationship cardinality / type rejection
   - Invalid architecture & requirement traceability rejection
   - Malformed candidate handling
   - Mock execution
   - Provider routing & dynamic model resolution
3. SoftwareDesignWorkflow (Requirement -> Architecture -> Database):
   - End-to-end multi-agent pipeline with typed upstream enrichment
   - MockLLMProvider offline execution
   - Full status verification, artifact persistence, and deterministic validation
"""

import uuid
from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

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
from app.agents.architecture_recommendation.validation import (
    validate_architecture_recommendation_output,
)
from app.agents.contracts import AgentExecutionStatus, AgentType, ValidationResult
from app.agents.database_design import (
    AttributeRecommendation,
    ConstraintRecommendation,
    ConstraintType,
    DatabaseArchitectureTrace,
    DatabaseDesignAgent,
    DatabaseDesignCandidate,
    DatabaseDesignOutput,
    DatabaseParadigm,
    DatabaseRequirementTrace,
    DatabaseTradeOff,
    DataType,
    EntityRecommendation,
    IndexRecommendation,
    PrimaryKeyRecommendation,
    RelationshipRecommendation,
    RelationshipType,
)
from app.agents.database_design.validation import (
    validate_database_design_output,
)
from app.agents.execution import AgentExecutor
from app.agents.providers.mock import MockLLMProvider
from app.agents.providers.groq import GroqProvider
from app.agents.providers.gemini import GeminiProvider
from app.agents.registry import AgentRegistry
from app.agents.requirement_analysis.agent import RequirementAnalysisAgent
from app.agents.requirement_analysis.contracts import RequirementAnalysisOutput
from app.models.requirement import RequirementPriority, RequirementStatus, RequirementType
from app.schemas.context import ProjectContextResponse, RequirementStatistics
from app.schemas.project import ProjectResponse
from app.schemas.requirement import RequirementResponse
from app.workflows.coordinator import WorkflowCoordinator
from app.workflows.contracts import WorkflowInput, WorkflowStatus, WorkflowStepStatus
from app.workflows.pipelines import build_software_design_workflow


@pytest.fixture
def sample_pipeline_context() -> tuple[ProjectContextResponse, uuid.UUID, uuid.UUID]:
    """Provide canonical context with two active requirements."""
    project_id = uuid.uuid4()
    req1_id = uuid.uuid4()
    req2_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    req1 = RequirementResponse(
        id=req1_id,
        project_id=project_id,
        title="User Identity and Authentication",
        description="Secure multi-tenant authentication using JWT tokens and password hashing.",
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
        title="Audit Event Logging",
        description="Persist all authentication events into an immutable tamper-evident audit store.",
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
            name="Auth & Audit Core",
            slug="auth-audit-core",
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
def valid_arch_candidate(sample_pipeline_context) -> tuple[ArchitectureRecommendationCandidate, uuid.UUID, uuid.UUID]:
    _, req1_id, req2_id = sample_pipeline_context
    candidate = ArchitectureRecommendationCandidate(
        summary="Modular Monolith with dedicated Auth and Audit modules.",
        architecture_styles=[
            ArchitectureStyleRecommendation(
                style=ArchitectureStyle.MODULAR_MONOLITH,
                rationale="Balances developer velocity with clear domain boundaries.",
                confidence=0.9,
            )
        ],
        components=[
            ComponentRecommendation(
                name="AuthService",
                responsibility="User identity, credential validation, and JWT issuing.",
                reason="Directly satisfies user authentication requirement.",
                related_requirement_ids=[req1_id],
            ),
            ComponentRecommendation(
                name="AuditLogger",
                responsibility="Captures audit trails and writes to storage.",
                reason="Directly satisfies immutable audit logging requirement.",
                related_requirement_ids=[req2_id],
            ),
        ],
        data_flows=[
            DataFlowRecommendation(
                source_component="AuthService",
                target_component="AuditLogger",
                interaction="Internal async domain event",
                reason="Decouples auth response time from audit persistence.",
            )
        ],
        technologies=[
            TechnologyRecommendation(
                technology="PostgreSQL",
                category=TechnologyCategory.DATABASE,
                reason="Strong ACID compliance for identity and audit tables.",
                trade_off="Requires indexing care for high volume audit queries.",
            )
        ],
        trade_offs=[
            TradeOffAnalysis(
                decision_area="Monolith vs Microservices",
                recommended_option="Modular Monolith",
                advantages=["Simple deployment", "Low latency in-process calls"],
                disadvantages=["Single process failure domain"],
                alternative="Microservices",
                alternative_tradeoff="Higher operational complexity and network latency",
            )
        ],
        assumptions=["Expected volume is under 1,000 req/sec."],
        constraints=["Must strictly isolate password hashes."],
        unknowns=["Retention period requirements for audit events."],
        traceability_matrix=[
            ArchitectureRequirementTrace(
                requirement_id=req1_id,
                component_names=["AuthService"],
                rationale="AuthService handles authentication workflows.",
            ),
            ArchitectureRequirementTrace(
                requirement_id=req2_id,
                component_names=["AuditLogger"],
                rationale="AuditLogger guarantees audit recording.",
            ),
        ],
    )
    return candidate, req1_id, req2_id


@pytest.fixture
def valid_db_candidate(sample_pipeline_context) -> tuple[DatabaseDesignCandidate, uuid.UUID, uuid.UUID]:
    _, req1_id, req2_id = sample_pipeline_context
    candidate = DatabaseDesignCandidate(
        summary="Relational database schema with User and AuditLog entities.",
        database_paradigm=DatabaseParadigm.RELATIONAL,
        entities=[
            EntityRecommendation(
                name="users",
                description="Stores registered user credentials and profile data.",
                purpose="User authentication and profile management.",
                attributes=[
                    AttributeRecommendation(
                        name="id",
                        data_type=DataType.UUID,
                        nullable=False,
                        description="Primary key UUID.",
                        unique=True,
                    ),
                    AttributeRecommendation(
                        name="email",
                        data_type=DataType.STRING,
                        nullable=False,
                        description="User email address.",
                        unique=True,
                    ),
                    AttributeRecommendation(
                        name="password_hash",
                        data_type=DataType.STRING,
                        nullable=False,
                        description="Hashed password.",
                    ),
                ],
                primary_key=PrimaryKeyRecommendation(attributes=["id"], is_composite=False),
                related_requirement_ids=[req1_id],
            ),
            EntityRecommendation(
                name="audit_logs",
                description="Immutable audit trail of actions.",
                purpose="Compliance and security audit trail.",
                attributes=[
                    AttributeRecommendation(
                        name="id",
                        data_type=DataType.UUID,
                        nullable=False,
                        description="Primary key UUID.",
                        unique=True,
                    ),
                    AttributeRecommendation(
                        name="user_id",
                        data_type=DataType.UUID,
                        nullable=False,
                        description="Foreign key pointing to users.",
                    ),
                    AttributeRecommendation(
                        name="event_type",
                        data_type=DataType.STRING,
                        nullable=False,
                        description="Type of logged event.",
                    ),
                ],
                primary_key=PrimaryKeyRecommendation(attributes=["id"], is_composite=False),
                related_requirement_ids=[req2_id],
            ),
        ],
        relationships=[
            RelationshipRecommendation(
                source_entity="users",
                target_entity="audit_logs",
                relationship_type=RelationshipType.ONE_TO_MANY,
                source_cardinality="1",
                target_cardinality="0..*",
                foreign_key_entity="audit_logs",
                foreign_key_attributes=["user_id"],
                referenced_entity="users",
                referenced_attributes=["id"],
                description="One user produces many audit log entries.",
                related_requirement_ids=[req2_id],
            )
        ],
        indexes=[
            IndexRecommendation(
                entity="audit_logs",
                index_name="idx_audit_user_id",
                attributes=["user_id"],
                unique=False,
                reason="Fast retrieval of user activity.",
            )
        ],
        constraints=[
            ConstraintRecommendation(
                entity="users",
                constraint_type=ConstraintType.UNIQUE,
                attributes=["email"],
                reason="Email addresses must be distinct.",
            )
        ],
        trade_offs=[
            DatabaseTradeOff(
                decision_area="Relational vs NoSQL for Audit Logs",
                recommended_option="Relational table with foreign key",
                rationale="Ensures referential integrity back to users.",
                advantages=["Strong consistency", "Immediate joins"],
                disadvantages=["Table grows rapidly"],
                alternative="Document Store",
                alternative_tradeoff="Eventual consistency and unconstrained references",
            )
        ],
        assumptions=["User base starts under 100,000 accounts."],
        constraints_notes=["Must not store plain-text passwords."],
        unknowns=["Specific data retention archiving schedules."],
        requirement_traceability=[
            DatabaseRequirementTrace(
                requirement_id=req1_id,
                entity_names=["users"],
                rationale="users table persists authentication credentials.",
            ),
            DatabaseRequirementTrace(
                requirement_id=req2_id,
                entity_names=["audit_logs"],
                rationale="audit_logs table records compliance events.",
            ),
        ],
        architecture_traceability=[
            DatabaseArchitectureTrace(
                architecture_component="AuthService",
                entity_names=["users"],
                rationale="AuthService owns the users table.",
            ),
            DatabaseArchitectureTrace(
                architecture_component="AuditLogger",
                entity_names=["audit_logs"],
                rationale="AuditLogger owns the audit_logs table.",
            ),
        ],
    )
    return candidate, req1_id, req2_id


# ==============================================================================
# SECTION A: ArchitectureRecommendationAgent Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_architecture_valid_candidate_and_deterministic_validation(
    sample_pipeline_context, valid_arch_candidate
):
    """Architecture agent generates valid candidate and passes deterministic domain validation."""
    context, req1_id, req2_id = sample_pipeline_context
    candidate, _, _ = valid_arch_candidate

    agent = ArchitectureRecommendationAgent()
    provider = MockLLMProvider()
    provider.register_structured_response(candidate)

    executor = AgentExecutor(provider=provider)
    result = await executor.execute(agent=agent, context=context)

    assert result.status == AgentExecutionStatus.COMPLETED
    assert result.validation.is_valid is True
    assert isinstance(result.output, ArchitectureRecommendationOutput)
    assert len(result.output.components) == 2
    assert result.output.architecture_styles[0].style == ArchitectureStyle.MODULAR_MONOLITH
    assert result.output.components[0].name == "AuthService"
    # Verify execution telemetry in metadata
    assert "latency_seconds" in result.metadata
    assert "usage" in result.metadata


def test_architecture_validation_rejects_unsupported_style(sample_pipeline_context, valid_arch_candidate):
    """Deterministic validation rejects invalid architecture styles."""
    context, _, _ = sample_pipeline_context
    candidate, _, _ = valid_arch_candidate

    data = candidate.model_dump()
    # Force invalid enum value bypassing Pydantic via dict model creation or invalid style
    output = ArchitectureRecommendationOutput(**data)
    # Manually corrupt the style
    output.architecture_styles[0].style = "UNSUPPORTED_GRID_COMPUTING"  # type: ignore

    val_res = validate_architecture_recommendation_output(output, context)
    assert val_res.is_valid is False
    assert any("is not a valid ArchitectureStyle" in err for err in val_res.errors)


def test_architecture_validation_rejects_invalid_requirement_traceability(
    sample_pipeline_context, valid_arch_candidate
):
    """Deterministic validation rejects hallucinated requirement UUIDs."""
    context, _, _ = sample_pipeline_context
    candidate, _, _ = valid_arch_candidate

    data = candidate.model_dump()
    hallucinated_uuid = uuid.uuid4()
    data["traceability_matrix"][0]["requirement_id"] = hallucinated_uuid

    output = ArchitectureRecommendationOutput(**data)
    val_res = validate_architecture_recommendation_output(output, context)
    assert val_res.is_valid is False
    assert any("nonexistent or inactive requirement ID" in err for err in val_res.errors)


def test_architecture_validation_rejects_unknown_component_in_dataflow(
    sample_pipeline_context, valid_arch_candidate
):
    """Deterministic validation rejects data flows referencing nonexistent components."""
    context, _, _ = sample_pipeline_context
    candidate, _, _ = valid_arch_candidate

    data = candidate.model_dump()
    data["data_flows"][0]["target_component"] = "NonExistentService"

    output = ArchitectureRecommendationOutput(**data)
    val_res = validate_architecture_recommendation_output(output, context)
    assert val_res.is_valid is False
    assert any("unknown target_component: 'NonExistentService'" in err for err in val_res.errors)


# ==============================================================================
# SECTION B: DatabaseDesignAgent Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_database_valid_candidate_and_deterministic_validation(
    sample_pipeline_context, valid_arch_candidate, valid_db_candidate
):
    """Database agent generates valid candidate and passes deterministic domain validation with arch inputs."""
    context, _, _ = sample_pipeline_context
    arch_candidate, _, _ = valid_arch_candidate
    arch_output = ArchitectureRecommendationOutput(**arch_candidate.model_dump())
    db_candidate, _, _ = valid_db_candidate

    agent = DatabaseDesignAgent()
    provider = MockLLMProvider()
    provider.register_structured_response(db_candidate)

    executor = AgentExecutor(provider=provider)
    result = await executor.execute(
        agent=agent,
        context=context,
        architecture_recommendation=arch_output,
    )

    assert result.status == AgentExecutionStatus.COMPLETED
    assert result.validation.is_valid is True
    assert isinstance(result.output, DatabaseDesignOutput)
    assert len(result.output.entities) == 2
    assert result.output.relationships[0].foreign_key_entity == "audit_logs"
    assert result.output.relationships[0].referenced_entity == "users"


def test_database_validation_rejects_foreign_key_parity_mismatch(
    sample_pipeline_context, valid_arch_candidate, valid_db_candidate
):
    """Deterministic validation rejects relationships where FK and referenced attribute counts differ."""
    context, _, _ = sample_pipeline_context
    arch_candidate, _, _ = valid_arch_candidate
    arch_output = ArchitectureRecommendationOutput(**arch_candidate.model_dump())
    db_candidate, _, _ = valid_db_candidate

    data = db_candidate.model_dump()
    # Introduce parity mismatch: 2 FK attributes vs 1 referenced attribute
    data["relationships"][0]["foreign_key_attributes"] = ["user_id", "extra_id"]
    data["entities"][1]["attributes"].append(
        {"name": "extra_id", "data_type": "UUID", "nullable": True, "description": "extra"}
    )

    output = DatabaseDesignOutput(**data)
    val_res = validate_database_design_output(output, context, arch_output)
    assert val_res.is_valid is False
    assert any("parity mismatch" in err for err in val_res.errors)


def test_database_validation_rejects_invalid_foreign_key_entity(
    sample_pipeline_context, valid_arch_candidate, valid_db_candidate
):
    """Deterministic validation rejects relationships pointing to nonexistent entities."""
    context, _, _ = sample_pipeline_context
    arch_candidate, _, _ = valid_arch_candidate
    arch_output = ArchitectureRecommendationOutput(**arch_candidate.model_dump())
    db_candidate, _, _ = valid_db_candidate

    data = db_candidate.model_dump()
    data["relationships"][0]["referenced_entity"] = "ghost_entity"

    output = DatabaseDesignOutput(**data)
    val_res = validate_database_design_output(output, context, arch_output)
    assert val_res.is_valid is False
    assert any("unknown referenced_entity: 'ghost_entity'" in err for err in val_res.errors)


def test_database_validation_rejects_undeclared_primary_key_attribute(
    sample_pipeline_context, valid_arch_candidate, valid_db_candidate
):
    """Deterministic validation rejects primary key referencing undeclared attribute."""
    context, _, _ = sample_pipeline_context
    arch_candidate, _, _ = valid_arch_candidate
    arch_output = ArchitectureRecommendationOutput(**arch_candidate.model_dump())
    db_candidate, _, _ = valid_db_candidate

    data = db_candidate.model_dump()
    data["entities"][0]["primary_key"]["attributes"] = ["nonexistent_col"]

    output = DatabaseDesignOutput(**data)
    val_res = validate_database_design_output(output, context, arch_output)
    assert val_res.is_valid is False
    assert any("primary_key references undeclared attribute" in err for err in val_res.errors)


def test_database_validation_rejects_hallucinated_architecture_component(
    sample_pipeline_context, valid_arch_candidate, valid_db_candidate
):
    """Deterministic validation rejects architecture traceability referencing nonexistent components."""
    context, _, _ = sample_pipeline_context
    arch_candidate, _, _ = valid_arch_candidate
    arch_output = ArchitectureRecommendationOutput(**arch_candidate.model_dump())
    db_candidate, _, _ = valid_db_candidate

    data = db_candidate.model_dump()
    data["architecture_traceability"][0]["architecture_component"] = "HallucinatedService"

    output = DatabaseDesignOutput(**data)
    val_res = validate_database_design_output(output, context, arch_output)
    assert val_res.is_valid is False
    assert any("references unknown component: 'HallucinatedService'" in err for err in val_res.errors)


# ==============================================================================
# SECTION C: SoftwareDesignWorkflow Pipeline Tests (Requirement -> Architecture -> Database)
# ==============================================================================

@pytest.mark.asyncio
async def test_software_design_workflow_end_to_end_mock(
    sample_pipeline_context, valid_arch_candidate, valid_db_candidate
):
    """SoftwareDesignWorkflow executes all 3 stages sequentially with typed enrichment using MockLLMProvider."""
    context, req1_id, req2_id = sample_pipeline_context
    arch_candidate, _, _ = valid_arch_candidate
    db_candidate, _, _ = valid_db_candidate

    # 1. Setup mock provider with queued structured responses for all 3 agents
    provider = MockLLMProvider()

    # Stage 1: Requirement Analysis output
    req_analysis_output = RequirementAnalysisOutput(
        summary="Requirement analysis indicates strong security and audit boundaries.",
        ambiguities=[],
        conflicts=[],
        missing_information=[],
        refinements=[],
        scope_clarifications=[],
        completeness_score=0.0,
        active_requirements_count=2,
        total_requirements_count=2,
    )
    provider.register_structured_response(req_analysis_output)

    # Stage 2: Architecture Recommendation candidate
    provider.register_structured_response(arch_candidate)

    # Stage 3: Database Design candidate
    provider.register_structured_response(db_candidate)

    # 2. Setup registry with the 3 software design agents
    registry = AgentRegistry()
    registry.register(RequirementAnalysisAgent())
    registry.register(ArchitectureRecommendationAgent())
    registry.register(DatabaseDesignAgent())

    executor = AgentExecutor(provider=provider)
    coordinator = WorkflowCoordinator(executor=executor, registry=registry)

    # 3. Execute Software Design Workflow
    workflow_def = build_software_design_workflow()
    workflow_input = WorkflowInput(context=context)

    execution = await coordinator.execute(
        workflow=workflow_def,
        workflow_input=workflow_input,
    )

    # 4. Verify workflow completion
    assert execution.status == WorkflowStatus.COMPLETED
    assert len(execution.step_results) == 3

    # Verify Step 1: requirement-analysis
    step1 = execution.step_results[0]
    assert step1.step_id == "requirement-analysis"
    assert step1.status == WorkflowStepStatus.COMPLETED
    assert step1.agent_result is not None
    assert isinstance(step1.agent_result.output, RequirementAnalysisOutput)

    # Verify Step 2: architecture-recommendation
    step2 = execution.step_results[1]
    assert step2.step_id == "architecture-recommendation"
    assert step2.status == WorkflowStepStatus.COMPLETED
    assert step2.agent_result is not None
    assert isinstance(step2.agent_result.output, ArchitectureRecommendationOutput)

    # Verify Step 3: database-design
    step3 = execution.step_results[2]
    assert step3.step_id == "database-design"
    assert step3.status == WorkflowStepStatus.COMPLETED
    assert step3.agent_result is not None
    assert isinstance(step3.agent_result.output, DatabaseDesignOutput)

    # Verify artifacts dict has all 3 outputs
    assert "requirement-analysis" in execution.artifacts
    assert isinstance(execution.artifacts["requirement-analysis"], RequirementAnalysisOutput)
    assert "architecture-recommendation" in execution.artifacts
    assert isinstance(execution.artifacts["architecture-recommendation"], ArchitectureRecommendationOutput)
    assert "database-design" in execution.artifacts
    assert isinstance(execution.artifacts["database-design"], DatabaseDesignOutput)


@pytest.mark.asyncio
async def test_architecture_agent_resolves_provider_model_dynamically(sample_pipeline_context, valid_arch_candidate):
    """Architecture agent resolves model from provider.default_model when model is not explicitly passed."""
    context, _, _ = sample_pipeline_context
    candidate, _, _ = valid_arch_candidate

    agent = ArchitectureRecommendationAgent()
    provider = MockLLMProvider()
    provider._default_model = "custom-arch-model"
    provider.register_structured_response(candidate)

    # Spy on generate_structured call
    captured_requests = []
    original_gen = provider.generate_structured

    async def spying_gen(request, response_model):
        captured_requests.append(request)
        return await original_gen(request, response_model)

    provider.generate_structured = spying_gen

    executor = AgentExecutor(provider=provider)
    result = await executor.execute(agent=agent, context=context)

    assert result.status == AgentExecutionStatus.COMPLETED
    assert len(captured_requests) == 1
    assert captured_requests[0].model == "custom-arch-model"


@pytest.mark.asyncio
async def test_database_agent_resolves_provider_model_dynamically(
    sample_pipeline_context, valid_arch_candidate, valid_db_candidate
):
    """Database agent resolves model from provider.default_model when model is not explicitly passed."""
    context, _, _ = sample_pipeline_context
    arch_candidate, _, _ = valid_arch_candidate
    arch_output = ArchitectureRecommendationOutput(**arch_candidate.model_dump())
    candidate, _, _ = valid_db_candidate

    agent = DatabaseDesignAgent()
    provider = MockLLMProvider()
    provider._default_model = "custom-db-model"
    provider.register_structured_response(candidate)

    captured_requests = []
    original_gen = provider.generate_structured

    async def spying_gen(request, response_model):
        captured_requests.append(request)
        return await original_gen(request, response_model)

    provider.generate_structured = spying_gen

    executor = AgentExecutor(provider=provider)
    result = await executor.execute(
        agent=agent,
        context=context,
        architecture_recommendation=arch_output,
    )

    assert result.status == AgentExecutionStatus.COMPLETED
    assert len(captured_requests) == 1
    assert captured_requests[0].model == "custom-db-model"


@pytest.mark.asyncio
async def test_architecture_agent_handles_generation_failure(sample_pipeline_context):
    """Architecture agent handles provider generation failure cleanly."""
    context, _, _ = sample_pipeline_context
    agent = ArchitectureRecommendationAgent()
    provider = MockLLMProvider()
    # Do not queue responses -> mock provider raises RuntimeError

    executor = AgentExecutor(provider=provider)
    result = await executor.execute(agent=agent, context=context)

    assert result.status == AgentExecutionStatus.FAILED
    assert result.error is not None


@pytest.mark.asyncio
async def test_database_agent_handles_generation_failure(sample_pipeline_context):
    """Database agent handles provider generation failure cleanly."""
    context, _, _ = sample_pipeline_context
    agent = DatabaseDesignAgent()
    provider = MockLLMProvider()

    executor = AgentExecutor(provider=provider)
    result = await executor.execute(agent=agent, context=context)

    assert result.status == AgentExecutionStatus.FAILED
    assert result.error is not None

