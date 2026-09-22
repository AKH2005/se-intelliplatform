"""Data Contracts and Structured Output Models for Database Design Agent."""

import enum
import uuid
from pydantic import BaseModel, ConfigDict, Field


class DatabaseParadigm(str, enum.Enum):
    """Target logical database paradigm recommended for the project application."""
    RELATIONAL = "RELATIONAL"
    DOCUMENT = "DOCUMENT"
    KEY_VALUE = "KEY_VALUE"
    GRAPH = "GRAPH"
    SEARCH = "SEARCH"


class DataType(str, enum.Enum):
    """Vendor-neutral logical attribute data types."""
    STRING = "STRING"
    INTEGER = "INTEGER"
    DECIMAL = "DECIMAL"
    BOOLEAN = "BOOLEAN"
    DATE = "DATE"
    DATETIME = "DATETIME"
    TIMESTAMP = "TIMESTAMP"
    UUID = "UUID"
    JSON = "JSON"
    TEXT = "TEXT"
    BINARY = "BINARY"


class RelationshipType(str, enum.Enum):
    """Logical entity relationship cardinality types."""
    ONE_TO_ONE = "ONE_TO_ONE"
    ONE_TO_MANY = "ONE_TO_MANY"
    MANY_TO_ONE = "MANY_TO_ONE"
    MANY_TO_MANY = "MANY_TO_MANY"


class ConstraintType(str, enum.Enum):
    """Database integrity and validation constraint classifications."""
    UNIQUE = "UNIQUE"
    NOT_NULL = "NOT_NULL"
    CHECK = "CHECK"
    PRIMARY_KEY = "PRIMARY_KEY"
    FOREIGN_KEY = "FOREIGN_KEY"


class AttributeRecommendation(BaseModel):
    """Specification for an attribute/column within an entity."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Attribute name (e.g. 'user_id', 'created_at')",
    )
    data_type: DataType = Field(
        ...,
        description="Vendor-neutral logical data type",
    )
    nullable: bool = Field(
        default=False,
        description="True if attribute allows NULL values",
    )
    description: str = Field(
        ...,
        min_length=3,
        description="Engineering description of data held by this attribute",
    )
    default_value: str | None = Field(
        default=None,
        description="Optional default value or generator expression (e.g. 'uuid_generate_v4()', '0')",
    )
    unique: bool = Field(
        default=False,
        description="True if individual attribute uniqueness is required",
    )


class PrimaryKeyRecommendation(BaseModel):
    """Authoritative primary key declaration for an entity."""

    attributes: list[str] = Field(
        ...,
        min_length=1,
        description="Ordered list of attribute names that form the primary key",
    )
    is_composite: bool = Field(
        default=False,
        description="True if primary key is composed of more than one attribute",
    )


class EntityRecommendation(BaseModel):
    """Logical entity/table recommended for persistent data modeling."""

    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Unique name of the logical entity (e.g. 'User', 'PaymentTransaction')",
    )
    description: str = Field(
        ...,
        min_length=5,
        description="Engineering description of what this entity models",
    )
    purpose: str = Field(
        ...,
        min_length=5,
        description="Core business/domain purpose of persisting this entity",
    )
    attributes: list[AttributeRecommendation] = Field(
        ...,
        min_length=1,
        description="List of declared attributes belonging to this entity",
    )
    primary_key: PrimaryKeyRecommendation = Field(
        ...,
        description="Authoritative primary key definition for this entity",
    )
    related_requirement_ids: list[uuid.UUID] = Field(
        default_factory=list,
        description="UUIDs of active requirements in canonical context satisfied by this entity",
    )


class RelationshipRecommendation(BaseModel):
    """Explicit relationship mapping between two entities with unambiguous foreign-key ownership."""

    source_entity: str = Field(
        ...,
        min_length=2,
        description="Initiating or parent entity in the relationship",
    )
    target_entity: str = Field(
        ...,
        min_length=2,
        description="Target or child entity in the relationship",
    )
    relationship_type: RelationshipType = Field(
        ...,
        description="Cardinality classification",
    )
    source_cardinality: str = Field(
        ...,
        min_length=1,
        description="Multiplicity at source (e.g. '1', '0..1', '1..*')",
    )
    target_cardinality: str = Field(
        ...,
        min_length=1,
        description="Multiplicity at target (e.g. '1', '0..1', '0..*')",
    )
    foreign_key_entity: str = Field(
        ...,
        min_length=2,
        description="Entity that actually contains the foreign key attribute(s)",
    )
    foreign_key_attributes: list[str] = Field(
        ...,
        min_length=1,
        description="Attribute name(s) in foreign_key_entity holding foreign key references",
    )
    referenced_entity: str = Field(
        ...,
        min_length=2,
        description="Entity being pointed to by the foreign key (typically holds PK)",
    )
    referenced_attributes: list[str] = Field(
        ...,
        min_length=1,
        description="Attribute name(s) in referenced_entity referenced by the foreign key",
    )
    junction_entity: str | None = Field(
        default=None,
        description="Optional associative/junction entity name for many-to-many relationships",
    )
    description: str = Field(
        ...,
        min_length=5,
        description="Business justification explaining the relationship",
    )
    related_requirement_ids: list[uuid.UUID] = Field(
        default_factory=list,
        description="UUIDs of requirements driving this relationship",
    )


class IndexRecommendation(BaseModel):
    """Performance or uniqueness index recommendation."""

    entity: str = Field(
        ...,
        min_length=2,
        description="Target entity on which index is placed",
    )
    index_name: str = Field(
        ...,
        min_length=3,
        description="Unique identifier/name for this index (e.g. 'idx_users_email')",
    )
    attributes: list[str] = Field(
        ...,
        min_length=1,
        description="Ordered list of attributes included in the index key",
    )
    unique: bool = Field(
        default=False,
        description="True if index enforces uniqueness",
    )
    reason: str = Field(
        ...,
        min_length=5,
        description="Performance or lookup rationale justifying this index",
    )


class ConstraintRecommendation(BaseModel):
    """Additional integrity or domain business rule constraint."""

    entity: str = Field(
        ...,
        min_length=2,
        description="Target entity for this constraint",
    )
    constraint_type: ConstraintType = Field(
        ...,
        description="Constraint type classification",
    )
    attributes: list[str] = Field(
        default_factory=list,
        description="Attributes covered by this constraint",
    )
    expression_or_reference: str | None = Field(
        default=None,
        description="Check expression or target reference (e.g. 'amount > 0')",
    )
    reason: str = Field(
        ...,
        min_length=5,
        description="Engineering justification for this integrity rule",
    )


class DatabaseRequirementTrace(BaseModel):
    """Traceability link connecting canonical requirements to database entities."""

    requirement_id: uuid.UUID = Field(
        ...,
        description="UUID of requirement present in canonical context",
    )
    entity_names: list[str] = Field(
        ...,
        min_length=1,
        description="Declared entity names that store or realize this requirement",
    )
    rationale: str = Field(
        ...,
        min_length=5,
        description="Explanation of how the entity data model satisfies the requirement",
    )


class DatabaseArchitectureTrace(BaseModel):
    """Traceability link connecting architecture components to database entities."""

    architecture_component: str = Field(
        ...,
        min_length=2,
        description="Name of architecture component present in supplied Phase 5 recommendations",
    )
    entity_names: list[str] = Field(
        ...,
        min_length=1,
        description="Declared entity names used or managed by this architecture component",
    )
    rationale: str = Field(
        ...,
        min_length=5,
        description="Explanation of data responsibility and persistence coupling",
    )


class DatabaseTradeOff(BaseModel):
    """Qualitative trade-off analysis evaluating data modeling decisions."""

    decision_area: str = Field(
        ...,
        min_length=3,
        description="Database modeling decision scope (e.g. 'Normalization vs Denormalization')",
    )
    recommended_option: str = Field(
        ...,
        min_length=3,
        description="Design choice recommended by the agent",
    )
    rationale: str = Field(
        ...,
        min_length=5,
        description="Justification for selecting this option",
    )
    advantages: list[str] = Field(
        ...,
        min_length=1,
        description="Engineering benefits of this option",
    )
    disadvantages: list[str] = Field(
        ...,
        min_length=1,
        description="Trade-offs or operational complexities of this option",
    )
    alternative: str = Field(
        ...,
        min_length=3,
        description="Viable alternative data modeling approach",
    )
    alternative_tradeoff: str = Field(
        ...,
        min_length=5,
        description="Compromises required by the alternative",
    )


class DatabaseDesignCandidate(BaseModel):
    """Raw candidate structured model emitted by LLM provider."""

    model_config = ConfigDict(extra="ignore")

    summary: str = Field(
        ...,
        min_length=5,
        description="High-level engineering overview of the recommended database schema",
    )
    database_paradigm: DatabaseParadigm = Field(
        default=DatabaseParadigm.RELATIONAL,
        description="Recommended logical database paradigm",
    )
    entities: list[EntityRecommendation] = Field(
        default_factory=list,
        description="Proposed database entities/tables",
    )
    relationships: list[RelationshipRecommendation] = Field(
        default_factory=list,
        description="Explicit entity relationships with foreign key ownership",
    )
    indexes: list[IndexRecommendation] = Field(
        default_factory=list,
        description="Proposed performance and uniqueness indexes",
    )
    constraints: list[ConstraintRecommendation] = Field(
        default_factory=list,
        description="Additional integrity and check constraints",
    )
    trade_offs: list[DatabaseTradeOff] = Field(
        default_factory=list,
        description="Qualitative trade-off analyses of data modeling decisions",
    )
    assumptions: list[str] = Field(
        default_factory=list,
        description="Explicit assumptions regarding volume, concurrency, or access patterns",
    )
    constraints_notes: list[str] = Field(
        default_factory=list,
        description="Identified technical and storage constraints",
    )
    unknowns: list[str] = Field(
        default_factory=list,
        description="Open unknowns or retention questions requiring stakeholder clarification",
    )
    requirement_traceability: list[DatabaseRequirementTrace] = Field(
        default_factory=list,
        description="Requirement-to-entity traceability mappings",
    )
    architecture_traceability: list[DatabaseArchitectureTrace] = Field(
        default_factory=list,
        description="Architecture-component-to-entity traceability mappings",
    )


class DatabaseDesignOutput(BaseModel):
    """Authoritative structured output envelope for Database Design Agent.
    
    CRITICAL ARCHITECTURAL GUARANTEE:
    Recommendations are advisory only (Agent output == recommendation; Agent output != database mutation).
    The platform does NOT create tables, execute DDL, or generate Alembic migrations.
    """

    summary: str = Field(
        ...,
        min_length=5,
        description="High-level engineering overview of the recommended database schema",
    )
    database_paradigm: DatabaseParadigm = Field(
        ...,
        description="Recommended logical database paradigm",
    )
    entities: list[EntityRecommendation] = Field(
        default_factory=list,
        description="Proposed database entities/tables",
    )
    relationships: list[RelationshipRecommendation] = Field(
        default_factory=list,
        description="Explicit entity relationships with foreign key ownership",
    )
    indexes: list[IndexRecommendation] = Field(
        default_factory=list,
        description="Proposed performance and uniqueness indexes",
    )
    constraints: list[ConstraintRecommendation] = Field(
        default_factory=list,
        description="Additional integrity and check constraints",
    )
    trade_offs: list[DatabaseTradeOff] = Field(
        default_factory=list,
        description="Qualitative trade-off analyses of data modeling decisions",
    )
    assumptions: list[str] = Field(
        default_factory=list,
        description="Explicit assumptions regarding volume, concurrency, or access patterns",
    )
    constraints_notes: list[str] = Field(
        default_factory=list,
        description="Identified technical and storage constraints",
    )
    unknowns: list[str] = Field(
        default_factory=list,
        description="Open unknowns or retention questions requiring stakeholder clarification",
    )
    requirement_traceability: list[DatabaseRequirementTrace] = Field(
        default_factory=list,
        description="Requirement-to-entity traceability mappings",
    )
    architecture_traceability: list[DatabaseArchitectureTrace] = Field(
        default_factory=list,
        description="Architecture-component-to-entity traceability mappings",
    )
