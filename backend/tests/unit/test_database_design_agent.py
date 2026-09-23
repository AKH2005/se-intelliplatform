"""Comprehensive Unit Tests for Phase 6 Database Design Agent."""

import uuid
from datetime import datetime, timezone
from unittest.mock import patch
import pytest
from httpx import AsyncClient
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
from app.agents.execution import AgentExecutor
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
    assert len(test_reg.list_agents()) == 8


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
