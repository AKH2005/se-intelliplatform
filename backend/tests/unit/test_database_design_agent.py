"""Comprehensive Unit Tests for Phase 6 Database Design Agent."""

import uuid
from datetime import datetime, timezone
from unittest.mock import patch
import pytest
from httpx import AsyncClient
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.architecture_recommendation.agent import ArchitectureRecommendationAgent
from app.agents.architecture_recommendation.contracts import (
    ArchitectureRecommendationOutput,
    ArchitectureStyle,
    ArchitectureStyleRecommendation,
    ComponentRecommendation,
)
from app.agents.contracts import AgentExecutionStatus, AgentType
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
from app.agents.exceptions import ProviderError, TransientProviderError
from app.agents.execution import AgentExecutor
from app.agents.providers.groq import GroqProvider
from app.agents.providers.mock import MockLLMProvider
from app.agents.registry import AgentRegistry, register_default_agents
from app.agents.requirement_analysis.agent import RequirementAnalysisAgent
from app.agents.requirement_analysis.contracts import RequirementAnalysisOutput
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
def sample_db_context() -> tuple[ProjectContextResponse, uuid.UUID, uuid.UUID]:
    """Provide a canonical ProjectContextResponse with two active requirements."""
    project_id = uuid.uuid4()
    req1_id = uuid.uuid4()
    req2_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    req1 = RequirementResponse(
        id=req1_id,
        project_id=project_id,
        title="User Account Management",
        description="Users must be able to register with email, username, and hashed password.",
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
        title="Order Placement & History",
        description="Customers can place orders with items, tracking line-item pricing and status.",
        type=RequirementType.FUNCTIONAL,
        priority=RequirementPriority.HIGH,
        status=RequirementStatus.APPROVED,
        is_archived=False,
        created_at=now,
        updated_at=now,
    )

    stats = RequirementStatistics(
        total_requirements=2,
        active_requirements=2,
        functional_count=2,
        non_functional_count=0,
        constraint_count=0,
        by_priority={"CRITICAL": 1, "HIGH": 1},
        by_status={"APPROVED": 2},
        completion_percentage=0.0,
    )

    context = ProjectContextResponse(
        project=ProjectResponse(
            id=project_id,
            name="E-Commerce Platform",
            slug="ecom-platform",
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
def sample_phase4_output() -> RequirementAnalysisOutput:
    """Provide a validated Phase 4 RequirementAnalysisOutput."""
    return RequirementAnalysisOutput(
        summary="User accounts and orders require robust transactional consistency.",
        ambiguities=[],
        conflicts=[],
        missing_information=[],
        refinements=[],
        scope_clarifications=[],
        completeness_score=0.0,
        active_requirements_count=2,
        total_requirements_count=2,
    )


@pytest.fixture
def sample_phase5_output(sample_db_context) -> ArchitectureRecommendationOutput:
    """Provide a validated Phase 5 ArchitectureRecommendationOutput."""
    _, req1_id, req2_id = sample_db_context
    return ArchitectureRecommendationOutput(
        summary="Modular Monolith with User and Order domain modules.",
        architecture_styles=[
            ArchitectureStyleRecommendation(
                style=ArchitectureStyle.MODULAR_MONOLITH,
                rationale="Separates domain boundaries cleanly.",
                confidence=0.9,
            )
        ],
        components=[
            ComponentRecommendation(
                name="User Module",
                responsibility="Manages user profiles and authentication.",
                reason="Domain boundary for identity.",
                related_requirement_ids=[req1_id],
            ),
            ComponentRecommendation(
                name="Order Module",
                responsibility="Manages orders, line items, and fulfillment.",
                reason="Domain boundary for orders.",
                related_requirement_ids=[req2_id],
            ),
        ],
        data_flows=[],
        technologies=[],
        trade_offs=[],
        assumptions=[],
        constraints=[],
        unknowns=[],
        traceability_matrix=[],
    )


@pytest.fixture
def valid_db_candidate(sample_db_context) -> DatabaseDesignCandidate:
    """Provide a structurally valid DatabaseDesignCandidate."""
    _, req1_id, req2_id = sample_db_context
    return DatabaseDesignCandidate(
        summary="Relational database design modeling Users, Orders, and OrderItems.",
        database_paradigm=DatabaseParadigm.RELATIONAL,
        entities=[
            EntityRecommendation(
                name="User",
                description="Stores registered user identity and credentials.",
                purpose="User profile and login management.",
                attributes=[
                    AttributeRecommendation(
                        name="id",
                        data_type=DataType.UUID,
                        nullable=False,
                        description="Primary key UUID",
                        unique=True,
                    ),
                    AttributeRecommendation(
                        name="email",
                        data_type=DataType.STRING,
                        nullable=False,
                        description="User login email address",
                        unique=True,
                    ),
                    AttributeRecommendation(
                        name="created_at",
                        data_type=DataType.TIMESTAMP,
                        nullable=False,
                        description="Account creation timestamp",
                    ),
                ],
                primary_key=PrimaryKeyRecommendation(attributes=["id"], is_composite=False),
                related_requirement_ids=[req1_id],
            ),
            EntityRecommendation(
                name="Order",
                description="Represents a customer purchase order.",
                purpose="Order transaction record.",
                attributes=[
                    AttributeRecommendation(
                        name="id",
                        data_type=DataType.UUID,
                        nullable=False,
                        description="Order primary key UUID",
                        unique=True,
                    ),
                    AttributeRecommendation(
                        name="user_id",
                        data_type=DataType.UUID,
                        nullable=False,
                        description="Foreign key to User.id",
                    ),
                    AttributeRecommendation(
                        name="status",
                        data_type=DataType.STRING,
                        nullable=False,
                        description="Order status",
                    ),
                ],
                primary_key=PrimaryKeyRecommendation(attributes=["id"], is_composite=False),
                related_requirement_ids=[req2_id],
            ),
        ],
        relationships=[
            RelationshipRecommendation(
                source_entity="User",
                target_entity="Order",
                relationship_type=RelationshipType.ONE_TO_MANY,
                source_cardinality="1",
                target_cardinality="0..*",
                foreign_key_entity="Order",
                foreign_key_attributes=["user_id"],
                referenced_entity="User",
                referenced_attributes=["id"],
                description="A User places zero or more Orders.",
                related_requirement_ids=[req2_id],
            )
        ],
        indexes=[
            IndexRecommendation(
                entity="Order",
                index_name="idx_orders_user_id",
                attributes=["user_id"],
                unique=False,
                reason="Accelerates lookups of order history by customer.",
            )
        ],
        constraints=[
            ConstraintRecommendation(
                entity="User",
                constraint_type=ConstraintType.UNIQUE,
                attributes=["email"],
                reason="Prevents duplicate email registrations.",
            )
        ],
        trade_offs=[
            DatabaseTradeOff(
                decision_area="Relational vs Document Model",
                recommended_option="Relational Schema",
                rationale="Strong ACID transaction support needed for order integrity.",
                advantages=["Strict referential integrity", "Ad-hoc SQL querying"],
                disadvantages=["Schema migration overhead"],
                alternative="Document Store",
                alternative_tradeoff="Eventual consistency risks for order totals.",
            )
        ],
        assumptions=["Concurrent write rate is below 1,000 orders/sec."],
        constraints_notes=["Relational ACID guarantees required."],
        unknowns=["Long-term order archiving retention policy."],
        requirement_traceability=[
            DatabaseRequirementTrace(
                requirement_id=req1_id,
                entity_names=["User"],
                rationale="Stores user registration data.",
            ),
            DatabaseRequirementTrace(
                requirement_id=req2_id,
                entity_names=["Order"],
                rationale="Stores order placement and history.",
            ),
        ],
        architecture_traceability=[
            DatabaseArchitectureTrace(
                architecture_component="User Module",
                entity_names=["User"],
                rationale="Managed by User Module.",
            ),
            DatabaseArchitectureTrace(
                architecture_component="Order Module",
                entity_names=["Order"],
                rationale="Managed by Order Module.",
            ),
        ],
    )


# --------------------------------------------------------------------------
# 1. Metadata and Agent Identity
# --------------------------------------------------------------------------
def test_database_design_agent_metadata():
    agent = DatabaseDesignAgent()
    meta = agent.metadata
    assert meta.agent_id == "database-design"
    assert meta.name == "Database Design Agent"
    assert meta.version == "1.0.0"
    assert meta.agent_type == AgentType.RECOMMENDATION
    assert agent.output_schema == DatabaseDesignOutput


# --------------------------------------------------------------------------
# 2. Four Input Modes Supported
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_input_mode_a_standalone(sample_db_context, valid_db_candidate):
    """Mode A: ProjectContextResponse alone (architecture_traceability empty)."""
    context, _, _ = sample_db_context
    valid_db_candidate.architecture_traceability = []
    agent = DatabaseDesignAgent()
    provider = MockLLMProvider()
    provider.register_structured_response(valid_db_candidate)

    executor = AgentExecutor(provider=provider)
    result = await executor.execute(agent=agent, context=context)

    assert result.status == AgentExecutionStatus.COMPLETED
    assert result.output.database_paradigm == DatabaseParadigm.RELATIONAL
    assert len(result.output.entities) == 2


@pytest.mark.asyncio
async def test_input_mode_b_with_phase4(sample_db_context, sample_phase4_output, valid_db_candidate):
    """Mode B: ProjectContextResponse + RequirementAnalysisOutput."""
    context, _, _ = sample_db_context
    valid_db_candidate.architecture_traceability = []
    agent = DatabaseDesignAgent()
    provider = MockLLMProvider()
    provider.register_structured_response(valid_db_candidate)

    executor = AgentExecutor(provider=provider)
    result = await executor.execute(
        agent=agent,
        context=context,
        requirement_analysis=sample_phase4_output,
    )

    assert result.status == AgentExecutionStatus.COMPLETED
    assert result.output is not None


@pytest.mark.asyncio
async def test_input_mode_c_with_phase5(sample_db_context, sample_phase5_output, valid_db_candidate):
    """Mode C: ProjectContextResponse + ArchitectureRecommendationOutput."""
    context, _, _ = sample_db_context
    agent = DatabaseDesignAgent()
    provider = MockLLMProvider()
    provider.register_structured_response(valid_db_candidate)

    executor = AgentExecutor(provider=provider)
    result = await executor.execute(
        agent=agent,
        context=context,
        architecture_recommendation=sample_phase5_output,
    )

    assert result.status == AgentExecutionStatus.COMPLETED
    assert len(result.output.architecture_traceability) == 2


@pytest.mark.asyncio
async def test_input_mode_d_with_both_upstream_outputs(
    sample_db_context, sample_phase4_output, sample_phase5_output, valid_db_candidate
):
    """Mode D: ProjectContextResponse + RequirementAnalysisOutput + ArchitectureRecommendationOutput."""
    context, _, _ = sample_db_context
    agent = DatabaseDesignAgent()
    provider = MockLLMProvider()
    provider.register_structured_response(valid_db_candidate)

    executor = AgentExecutor(provider=provider)
    result = await executor.execute(
        agent=agent,
        context=context,
        requirement_analysis=sample_phase4_output,
        architecture_recommendation=sample_phase5_output,
    )

    assert result.status == AgentExecutionStatus.COMPLETED
    assert len(result.output.entities) == 2
    assert len(result.output.relationships) == 1
    assert result.output.database_paradigm == DatabaseParadigm.RELATIONAL


# --------------------------------------------------------------------------
# 3. Agent Isolation (Zero Internal Invocation of Upstream Agents)
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_database_design_agent_does_not_execute_upstream_agents_internally(
    sample_db_context, valid_db_candidate
):
    """Verify that DatabaseDesignAgent never calls upstream agent execute methods internally."""
    context, _, _ = sample_db_context
    valid_db_candidate.architecture_traceability = []
    agent = DatabaseDesignAgent()
    provider = MockLLMProvider()
    provider.register_structured_response(valid_db_candidate)

    with patch.object(RequirementAnalysisAgent, "execute") as mock_req_exec, \
         patch.object(ArchitectureRecommendationAgent, "execute") as mock_arch_exec:
        executor = AgentExecutor(provider=provider)
        result = await executor.execute(agent=agent, context=context)

        assert result.status == AgentExecutionStatus.COMPLETED
        assert not mock_req_exec.called
        assert not mock_arch_exec.called


# --------------------------------------------------------------------------
# 4. Explicit Foreign-Key Ownership Integrity Tests (CTO Correction 3)
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_rejects_unknown_foreign_key_entity(sample_db_context, valid_db_candidate):
    """Verify that relationship referencing an unknown foreign_key_entity is rejected."""
    context, _, _ = sample_db_context
    valid_db_candidate.architecture_traceability = []
    valid_db_candidate.relationships[0].foreign_key_entity = "PhantomEntity"
    agent = DatabaseDesignAgent()
    provider = MockLLMProvider()
    provider.register_structured_response(valid_db_candidate)

    executor = AgentExecutor(provider=provider)
    result = await executor.execute(agent=agent, context=context)

    assert result.status == AgentExecutionStatus.FAILED
    assert result.error.error_code == "VALIDATION_FAILED"
    assert any("unknown foreign_key_entity: 'PhantomEntity'" in err for err in result.validation.errors)


@pytest.mark.asyncio
async def test_rejects_unknown_foreign_key_attribute(sample_db_context, valid_db_candidate):
    """Verify that relationship referencing an unknown foreign_key_attribute is rejected."""
    context, _, _ = sample_db_context
    valid_db_candidate.architecture_traceability = []
    valid_db_candidate.relationships[0].foreign_key_attributes = ["non_existent_column"]
    agent = DatabaseDesignAgent()
    provider = MockLLMProvider()
    provider.register_structured_response(valid_db_candidate)

    executor = AgentExecutor(provider=provider)
    result = await executor.execute(agent=agent, context=context)

    assert result.status == AgentExecutionStatus.FAILED
    assert any("foreign_key_attribute 'non_existent_column' does not exist" in err for err in result.validation.errors)


@pytest.mark.asyncio
async def test_rejects_unknown_referenced_entity_and_attributes(sample_db_context, valid_db_candidate):
    """Verify that relationship referencing an unknown referenced_entity or attribute is rejected."""
    context, _, _ = sample_db_context
    valid_db_candidate.architecture_traceability = []
    valid_db_candidate.relationships[0].referenced_entity = "GhostUser"
    agent = DatabaseDesignAgent()
    provider = MockLLMProvider()
    provider.register_structured_response(valid_db_candidate)

    executor = AgentExecutor(provider=provider)
    result = await executor.execute(agent=agent, context=context)

    assert result.status == AgentExecutionStatus.FAILED
    assert any("unknown referenced_entity: 'GhostUser'" in err for err in result.validation.errors)


@pytest.mark.asyncio
async def test_rejects_invalid_foreign_key_ownership_non_peer(sample_db_context, valid_db_candidate):
    """Verify that assigning FK ownership to an unrelated entity outside relationship peers is rejected."""
    context, _, _ = sample_db_context
    valid_db_candidate.architecture_traceability = []
    # User and Order are peers. Setting foreign_key_entity to a third entity or invalid peer is rejected.
    valid_db_candidate.relationships[0].foreign_key_entity = "User"  # User does not have user_id attribute!
    agent = DatabaseDesignAgent()
    provider = MockLLMProvider()
    provider.register_structured_response(valid_db_candidate)

    executor = AgentExecutor(provider=provider)
    result = await executor.execute(agent=agent, context=context)

    assert result.status == AgentExecutionStatus.FAILED
    assert any("foreign_key_attribute 'user_id' does not exist in foreign_key_entity 'User'" in err for err in result.validation.errors)


@pytest.mark.asyncio
async def test_self_referential_relationship_validated_successfully(sample_db_context, valid_db_candidate):
    """Verify that self-referential relationships (e.g. Category parent/child) are structurally supported."""
    context, req1_id, _ = sample_db_context
    valid_db_candidate.architecture_traceability = []

    # Add parent_user_id to User entity
    valid_db_candidate.entities[0].attributes.append(
        AttributeRecommendation(
            name="parent_user_id",
            data_type=DataType.UUID,
            nullable=True,
            description="Self-referencing manager or parent account",
        )
    )
    # Add self-referential relationship
    valid_db_candidate.relationships.append(
        RelationshipRecommendation(
            source_entity="User",
            target_entity="User",
            relationship_type=RelationshipType.MANY_TO_ONE,
            source_cardinality="0..*",
            target_cardinality="0..1",
            foreign_key_entity="User",
            foreign_key_attributes=["parent_user_id"],
            referenced_entity="User",
            referenced_attributes=["id"],
            description="User optionally reports to a parent User.",
            related_requirement_ids=[req1_id],
        )
    )
    agent = DatabaseDesignAgent()
    provider = MockLLMProvider()
    provider.register_structured_response(valid_db_candidate)

    executor = AgentExecutor(provider=provider)
    result = await executor.execute(agent=agent, context=context)

    assert result.status == AgentExecutionStatus.COMPLETED
    assert len(result.output.relationships) == 2


# --------------------------------------------------------------------------
# 5. Entity & Attribute Uniqueness and Primary Key Consistency
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_rejects_duplicate_entity_names(sample_db_context, valid_db_candidate):
    """Verify duplicate entity names are rejected."""
    context, _, _ = sample_db_context
    valid_db_candidate.architecture_traceability = []
    # Create duplicate entity name
    dup_entity = valid_db_candidate.entities[0].model_copy()
    valid_db_candidate.entities.append(dup_entity)
    agent = DatabaseDesignAgent()
    provider = MockLLMProvider()
    provider.register_structured_response(valid_db_candidate)

    executor = AgentExecutor(provider=provider)
    result = await executor.execute(agent=agent, context=context)

    assert result.status == AgentExecutionStatus.FAILED
    assert any("duplicate name: 'User'" in err for err in result.validation.errors)


@pytest.mark.asyncio
async def test_rejects_duplicate_attribute_names_in_entity(sample_db_context, valid_db_candidate):
    """Verify duplicate attribute names within an entity are rejected."""
    context, _, _ = sample_db_context
    valid_db_candidate.architecture_traceability = []
    valid_db_candidate.entities[0].attributes.append(
        AttributeRecommendation(
            name="email",  # Duplicate!
            data_type=DataType.STRING,
            description="Duplicate email",
        )
    )
    agent = DatabaseDesignAgent()
    provider = MockLLMProvider()
    provider.register_structured_response(valid_db_candidate)

    executor = AgentExecutor(provider=provider)
    result = await executor.execute(agent=agent, context=context)

    assert result.status == AgentExecutionStatus.FAILED
    assert any("duplicate attribute" in err and "email" in err for err in result.validation.errors)


@pytest.mark.asyncio
async def test_rejects_primary_key_referencing_undeclared_attribute(sample_db_context, valid_db_candidate):
    """Verify primary key referencing an undeclared attribute is rejected."""
    context, _, _ = sample_db_context
    valid_db_candidate.architecture_traceability = []
    valid_db_candidate.entities[0].primary_key.attributes = ["non_existent_pk"]
    agent = DatabaseDesignAgent()
    provider = MockLLMProvider()
    provider.register_structured_response(valid_db_candidate)

    executor = AgentExecutor(provider=provider)
    result = await executor.execute(agent=agent, context=context)

    assert result.status == AgentExecutionStatus.FAILED
    assert any("primary_key references undeclared attribute: 'non_existent_pk'" in err for err in result.validation.errors)


# --------------------------------------------------------------------------
# 6. Constraint Non-Contradiction Tests (CTO Correction 5)
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_rejects_contradictory_primary_key_constraint(sample_db_context, valid_db_candidate):
    """Verify that an additional constraint declaring a contradictory PRIMARY_KEY is rejected."""
    context, _, _ = sample_db_context
    valid_db_candidate.architecture_traceability = []
    # Entity User has PK ["id"]. Additional constraint declares PK ["email"], which contradicts it.
    valid_db_candidate.constraints.append(
        ConstraintRecommendation(
            entity="User",
            constraint_type=ConstraintType.PRIMARY_KEY,
            attributes=["email"],
            reason="Contradictory PK definition",
        )
    )
    agent = DatabaseDesignAgent()
    provider = MockLLMProvider()
    provider.register_structured_response(valid_db_candidate)

    executor = AgentExecutor(provider=provider)
    result = await executor.execute(agent=agent, context=context)

    assert result.status == AgentExecutionStatus.FAILED
    assert any("defines contradictory PRIMARY_KEY" in err for err in result.validation.errors)


# --------------------------------------------------------------------------
# 7. Architecture Traceability Tests (CTO Correction 4)
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_rejects_unknown_architecture_component_in_traceability(
    sample_db_context, sample_phase5_output, valid_db_candidate
):
    """Verify that architecture traceability referencing an undeclared architecture component is rejected."""
    context, _, _ = sample_db_context
    valid_db_candidate.architecture_traceability = [
        DatabaseArchitectureTrace(
            architecture_component="InventedComponent",  # Not in Phase 5 output!
            entity_names=["User"],
            rationale="Testing",
        )
    ]
    agent = DatabaseDesignAgent()
    provider = MockLLMProvider()
    provider.register_structured_response(valid_db_candidate)

    executor = AgentExecutor(provider=provider)
    result = await executor.execute(
        agent=agent,
        context=context,
        architecture_recommendation=sample_phase5_output,
    )

    assert result.status == AgentExecutionStatus.FAILED
    assert any("references unknown component: 'InventedComponent'" in err for err in result.validation.errors)


@pytest.mark.asyncio
async def test_rejects_invented_architecture_traceability_when_phase5_absent(
    sample_db_context, valid_db_candidate
):
    """Verify that architecture traceability items are rejected when Phase 5 output was not supplied."""
    context, _, _ = sample_db_context
    # architecture_traceability has items, but architecture_recommendation is NOT supplied to execute()
    agent = DatabaseDesignAgent()
    provider = MockLLMProvider()
    provider.register_structured_response(valid_db_candidate)

    executor = AgentExecutor(provider=provider)
    result = await executor.execute(agent=agent, context=context)

    assert result.status == AgentExecutionStatus.FAILED
    assert any("Architecture traceability cannot reference architecture components" in err for err in result.validation.errors)


# --------------------------------------------------------------------------
# 8. Requirement Traceability & Hallucination Defense
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_rejects_hallucinated_requirement_id(sample_db_context, valid_db_candidate):
    """Verify that referencing an invented requirement UUID fails deterministic validation."""
    context, _, _ = sample_db_context
    valid_db_candidate.architecture_traceability = []
    fake_id = uuid.uuid4()
    valid_db_candidate.entities[0].related_requirement_ids = [fake_id]

    agent = DatabaseDesignAgent()
    provider = MockLLMProvider()
    provider.register_structured_response(valid_db_candidate)

    executor = AgentExecutor(provider=provider)
    result = await executor.execute(agent=agent, context=context)

    assert result.status == AgentExecutionStatus.FAILED
    assert any(str(fake_id) in err for err in result.validation.errors)


# --------------------------------------------------------------------------
# 9. Strict Read-Only Guarantee: Zero Database Mutation
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_database_design_never_mutates_database(db_session: AsyncSession, valid_db_candidate):
    """Verify that executing DatabaseDesignAgent leaves PostgreSQL database records completely untouched."""
    proj = Project(
        name="DB Guard Project",
        slug=f"db-guard-{uuid.uuid4().hex[:8]}",
        status=ProjectStatus.IN_PROGRESS,
    )
    db_session.add(proj)
    await db_session.commit()
    await db_session.refresh(proj)

    req = Requirement(
        project_id=proj.id,
        title="Schema Invariant",
        description="Immutable requirement text.",
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

    valid_db_candidate.architecture_traceability = []
    valid_db_candidate.entities[0].related_requirement_ids = [req.id]
    valid_db_candidate.entities[1].related_requirement_ids = [req.id]
    valid_db_candidate.relationships[0].related_requirement_ids = [req.id]
    valid_db_candidate.requirement_traceability = [
        DatabaseRequirementTrace(
            requirement_id=req.id,
            entity_names=["User", "Order"],
            rationale="Satisfies schema invariant.",
        )
    ]

    agent = DatabaseDesignAgent()
    provider = MockLLMProvider()
    provider.register_structured_response(valid_db_candidate)

    executor = AgentExecutor(provider=provider)
    result = await executor.execute(agent=agent, context=context, session=db_session)
    assert result.status == AgentExecutionStatus.COMPLETED

    # Verify requirement in database has NOT been mutated
    await db_session.refresh(req)
    assert req.title == "Schema Invariant"
    assert req.type == RequirementType.FUNCTIONAL
    assert req.status == RequirementStatus.APPROVED


# --------------------------------------------------------------------------
# 10. Transient Provider Failure Retry
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_database_design_transient_failure_retry(sample_db_context, valid_db_candidate):
    """Verify transient provider errors are transparently retried by AgentExecutor."""
    context, _, _ = sample_db_context
    valid_db_candidate.architecture_traceability = []
    agent = DatabaseDesignAgent()
    provider = MockLLMProvider()

    provider.simulate_transient_failures(1)
    provider.register_structured_response(valid_db_candidate)

    executor = AgentExecutor(provider=provider, max_retries=3)
    result = await executor.execute(agent=agent, context=context)

    assert result.status == AgentExecutionStatus.COMPLETED
    assert result.metadata.get("attempts") == 2


# --------------------------------------------------------------------------
# 11. Registry Discovery & Idempotent Registration
# --------------------------------------------------------------------------
def test_register_default_agents_idempotent_includes_database_design():
    """Verify register_default_agents registers all three agents idempotently."""
    test_reg = AgentRegistry()
    register_default_agents(registry=test_reg)
    assert test_reg.has("requirement-analysis")
    assert test_reg.has("architecture-recommendation")
    assert test_reg.has("database-design")

    # Repeat call must succeed cleanly without raising ConflictError
    register_default_agents(registry=test_reg)
    assert len(test_reg.list_agents()) == 9


@pytest.mark.asyncio
async def test_database_design_agent_discovery_via_api(client: AsyncClient):
    """Verify that DatabaseDesignAgent is discoverable via GET /api/v1/agents."""
    register_default_agents()
    res = await client.get("/api/v1/agents")
    assert res.status_code == 200
    agents = res.json()
    agent_ids = [a["agent_id"] for a in agents]
    assert "database-design" in agent_ids

    target = next(a for a in agents if a["agent_id"] == "database-design")
    assert target["name"] == "Database Design Agent"
    assert target["version"] == "1.0.0"
    assert target["agent_type"] == "RECOMMENDATION"


# --------------------------------------------------------------------------
# 12. Regression Tests: Empty Defaults, Empty Entity Lists & AI Output Parsing
# --------------------------------------------------------------------------
def test_attribute_recommendation_empty_default_value_normalized_to_none():
    """Verify empty or whitespace default_value is safely normalized to None without inventing defaults."""
    # Empty string should normalize to None
    attr_empty = AttributeRecommendation(
        name="test_col",
        data_type=DataType.STRING,
        description="A test column",
        default_value="",
    )
    assert attr_empty.default_value is None

    # Whitespace-only string should normalize to None
    attr_whitespace = AttributeRecommendation(
        name="test_col",
        data_type=DataType.INTEGER,
        description="A test integer column",
        default_value="   ",
    )
    assert attr_whitespace.default_value is None

    # Explicit None remains None
    attr_none = AttributeRecommendation(
        name="test_col",
        data_type=DataType.BOOLEAN,
        description="A test boolean column",
        default_value=None,
    )
    assert attr_none.default_value is None


def test_attribute_recommendation_valid_default_value_preserved():
    """Verify non-empty default values are preserved exactly as declared."""
    attr_zero = AttributeRecommendation(
        name="count",
        data_type=DataType.INTEGER,
        description="Counter initialized to zero",
        default_value="0",
    )
    assert attr_zero.default_value == "0"

    attr_uuid = AttributeRecommendation(
        name="id",
        data_type=DataType.UUID,
        description="Unique identifier",
        default_value="uuid_generate_v4()",
    )
    assert attr_uuid.default_value == "uuid_generate_v4()"


def test_architecture_traceability_empty_entity_names_raises_validation_error():
    """Verify that an empty entity_names list strictly raises ValidationError (never silently allowed)."""
    # Empty list must fail schema validation (min_length=1)
    with pytest.raises(ValidationError) as exc_info:
        DatabaseArchitectureTrace(
            architecture_component="AuthService",
            entity_names=[],
            rationale="Authenticates users",
        )
    assert "entity_names" in str(exc_info.value)

    # Whitespace-only items also fail schema validation after normalization
    with pytest.raises(ValidationError) as exc_info:
        DatabaseArchitectureTrace(
            architecture_component="AuthService",
            entity_names=["   "],
            rationale="Authenticates users",
        )
    assert "entity_names" in str(exc_info.value)


def test_architecture_traceability_normalization_and_valid_cases():
    """Verify entity_names normalization handles comma-separated strings and valid lists."""
    # Valid list
    trace_list = DatabaseArchitectureTrace(
        architecture_component="AuthService",
        entity_names=["User", "Session"],
        rationale="Persists user credentials and active sessions",
    )
    assert trace_list.entity_names == ["User", "Session"]

    # Comma-separated string normalization
    trace_str = DatabaseArchitectureTrace(
        architecture_component="AuthService",
        entity_names="User, Session",
        rationale="Persists user credentials and active sessions",
    )
    assert trace_str.entity_names == ["User", "Session"]


def test_requirement_traceability_empty_entity_names_raises_validation_error():
    """Verify requirement_traceability with empty entity_names strictly raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        DatabaseRequirementTrace(
            requirement_id=uuid.uuid4(),
            entity_names=[],
            rationale="Satisfies canonical requirement",
        )
    assert "entity_names" in str(exc_info.value)


def test_database_design_candidate_with_empty_default_and_valid_traceability(valid_db_candidate):
    """Verify a full DatabaseDesignCandidate with empty default_value normalizes cleanly."""
    candidate_dict = valid_db_candidate.model_dump()
    # Emulate LLM returning empty string default_value for an attribute
    candidate_dict["entities"][0]["attributes"][0]["default_value"] = ""

    parsed = DatabaseDesignCandidate.model_validate(candidate_dict)
    assert parsed.entities[0].attributes[0].default_value is None
    assert len(parsed.entities) > 0


def test_groq_provider_parse_and_validate_empty_default_as_none():
    """Verify GroqProvider._parse_and_validate correctly parses AI output with empty default_value."""
    provider = GroqProvider(api_key="gsk_dummy_test_key_for_unit_tests")
    raw_ai_json = """
    {
        "summary": "Valid logical schema for testing normalization",
        "database_paradigm": "RELATIONAL",
        "entities": [
            {
                "name": "User",
                "description": "User entity with empty default value",
                "purpose": "Stores registered user credentials",
                "attributes": [
                    {
                        "name": "user_id",
                        "data_type": "UUID",
                        "nullable": false,
                        "description": "Primary key identifier",
                        "default_value": "",
                        "unique": true
                    }
                ],
                "primary_key": {
                    "attributes": ["user_id"],
                    "is_composite": false
                }
            }
        ],
        "relationships": [],
        "indexes": [],
        "constraints": [],
        "trade_offs": [],
        "assumptions": [],
        "constraints_notes": [],
        "unknowns": [],
        "requirement_traceability": [],
        "architecture_traceability": []
    }
    """
    candidate = provider._parse_and_validate(raw_ai_json, DatabaseDesignCandidate)
    assert candidate.entities[0].attributes[0].default_value is None
    assert candidate.entities[0].name == "User"


def test_groq_provider_raises_provider_error_on_empty_entity_names():
    """Verify GroqProvider raises ProviderError with clear error when entity_names is empty."""
    provider = GroqProvider(api_key="gsk_dummy_test_key_for_unit_tests")
    raw_ai_json = """
    {
        "summary": "Schema with invalid empty entity_names",
        "database_paradigm": "RELATIONAL",
        "entities": [
            {
                "name": "User",
                "description": "User entity",
                "purpose": "Stores user credentials",
                "attributes": [
                    {
                        "name": "user_id",
                        "data_type": "UUID",
                        "nullable": false,
                        "description": "Primary key identifier",
                        "default_value": null,
                        "unique": true
                    }
                ],
                "primary_key": {
                    "attributes": ["user_id"],
                    "is_composite": false
                }
            }
        ],
        "relationships": [],
        "indexes": [],
        "constraints": [],
        "trade_offs": [],
        "assumptions": [],
        "constraints_notes": [],
        "unknowns": [],
        "requirement_traceability": [],
        "architecture_traceability": [
            {
                "architecture_component": "FrontendUI",
                "entity_names": [],
                "rationale": "Non-persistent frontend component"
            }
        ]
    }
    """
    with pytest.raises(ProviderError) as exc_info:
        provider._parse_and_validate(raw_ai_json, DatabaseDesignCandidate)

    err = exc_info.value
    assert err.transient is False
    assert "Groq structured output failed Pydantic schema validation for DatabaseDesignCandidate" in err.message
    assert "entity_names" in err.message


def test_groq_provider_raises_provider_error_on_malformed_json():
    """Verify GroqProvider raises ProviderError with clear error on malformed JSON."""
    provider = GroqProvider(api_key="gsk_dummy_test_key_for_unit_tests")
    malformed_json = "```json\n{\"summary\": \"Truncated output without closing bracket...\n```"

    with pytest.raises(ProviderError) as exc_info:
        provider._parse_and_validate(malformed_json, DatabaseDesignCandidate)

    err = exc_info.value
    assert err.transient is False
    assert "Groq output was not valid JSON" in err.message


@pytest.mark.asyncio
async def test_database_design_agent_controlled_retry_on_schema_failure(sample_db_context, valid_db_candidate):
    """Verify DatabaseDesignAgent retries when candidate generation encounters a schema validation failure."""
    context, _, _ = sample_db_context
    valid_db_candidate.architecture_traceability = []
    agent = DatabaseDesignAgent()

    # Create mock provider simulating schema validation failure on attempt 1, success on attempt 2
    provider = MockLLMProvider()
    provider.simulate_permanent_failure(
        ProviderError(
            message="Groq structured output failed Pydantic schema validation for DatabaseDesignCandidate: 1 validation error",
            provider_name="groq",
            transient=False,
        )
    )

    # Calling with max_generate_attempts=1 must fail
    analysis_data = await agent.analyze(context)
    with pytest.raises(ProviderError) as exc_info:
        await agent.generate(analysis_data, provider, max_generate_attempts=1)
    assert "schema validation for DatabaseDesignCandidate" in str(exc_info.value)

    # Calling with fallback where attempt 2 succeeds:
    class RetryingMockProvider(MockLLMProvider):
        def __init__(self, candidate):
            super().__init__()
            self.attempt = 0
            self.candidate = candidate

        async def generate_structured(self, request, response_model):
            self.attempt += 1
            if self.attempt == 1:
                raise ProviderError(
                    message="Groq structured output failed Pydantic schema validation for DatabaseDesignCandidate: entity_names empty",
                    provider_name="groq",
                    transient=False,
                )
            return self.candidate

    retrying_provider = RetryingMockProvider(valid_db_candidate)
    output = await agent.generate(analysis_data, retrying_provider, max_generate_attempts=2)
    assert output is not None
    assert retrying_provider.attempt == 2
