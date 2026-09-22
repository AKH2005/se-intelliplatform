"""Database Design Agent Package."""

from app.agents.database_design.agent import DatabaseDesignAgent
from app.agents.database_design.contracts import (
    AttributeRecommendation,
    ConstraintRecommendation,
    ConstraintType,
    DatabaseArchitectureTrace,
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

__all__ = [
    "DatabaseDesignAgent",
    "DatabaseParadigm",
    "DataType",
    "RelationshipType",
    "ConstraintType",
    "AttributeRecommendation",
    "PrimaryKeyRecommendation",
    "EntityRecommendation",
    "RelationshipRecommendation",
    "IndexRecommendation",
    "ConstraintRecommendation",
    "DatabaseRequirementTrace",
    "DatabaseArchitectureTrace",
    "DatabaseTradeOff",
    "DatabaseDesignCandidate",
    "DatabaseDesignOutput",
    "validate_database_design_output",
]
