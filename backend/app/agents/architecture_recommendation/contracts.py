"""Data Contracts and Structured Output Models for Architecture Recommendation Agent."""

import enum
import uuid
from pydantic import BaseModel, ConfigDict, Field


class ArchitectureStyle(str, enum.Enum):
    """Supported canonical architecture styles."""
    MONOLITH = "MONOLITH"
    MODULAR_MONOLITH = "MODULAR_MONOLITH"
    LAYERED = "LAYERED"
    CLEAN_ARCHITECTURE = "CLEAN_ARCHITECTURE"
    HEXAGONAL = "HEXAGONAL"
    MICROSERVICES = "MICROSERVICES"
    EVENT_DRIVEN = "EVENT_DRIVEN"
    SERVERLESS = "SERVERLESS"


class TechnologyCategory(str, enum.Enum):
    """Categorization of proposed technology components."""
    FRONTEND = "FRONTEND"
    BACKEND = "BACKEND"
    DATABASE = "DATABASE"
    CACHE = "CACHE"
    MESSAGING = "MESSAGING"
    DEPLOYMENT = "DEPLOYMENT"
    OBSERVABILITY = "OBSERVABILITY"
    AUTHENTICATION = "AUTHENTICATION"


class ArchitectureStyleRecommendation(BaseModel):
    """Proposed architecture style with rationale and qualitative confidence assessment."""

    style: ArchitectureStyle = Field(
        ...,
        description="Recommended architecture structural pattern",
    )
    rationale: str = Field(
        ...,
        min_length=5,
        description="Justification explaining why this style fits the supplied requirements",
    )
    confidence: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Qualitative AI confidence assessment (0.0 to 1.0; not an objective score)",
    )


class ComponentRecommendation(BaseModel):
    """Major logical component recommended for system organization."""

    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Unique identifier/name for this logical component (e.g. 'API Gateway', 'Order Service')",
    )
    responsibility: str = Field(
        ...,
        min_length=5,
        description="Primary functional or domain responsibility of this component",
    )
    reason: str = Field(
        ...,
        min_length=5,
        description="Why this component is needed based on project requirements",
    )
    related_requirement_ids: list[uuid.UUID] = Field(
        default_factory=list,
        description="UUIDs of requirements in canonical context satisfied by this component",
    )


class DataFlowRecommendation(BaseModel):
    """Interaction pattern and communication path between two logical components."""

    source_component: str = Field(
        ...,
        min_length=2,
        description="Name of the initiating component (must exist in components list)",
    )
    target_component: str = Field(
        ...,
        min_length=2,
        description="Name of the receiving component (must exist in components list)",
    )
    interaction: str = Field(
        ...,
        min_length=3,
        description="Mechanism or protocol (e.g. 'REST/JSON over HTTPS', 'gRPC', 'Async Event')",
    )
    reason: str = Field(
        ...,
        min_length=5,
        description="Justification for this interaction and coupling level",
    )


class TechnologyRecommendation(BaseModel):
    """Advisory candidate technology suggestion."""

    technology: str = Field(
        ...,
        min_length=2,
        description="Candidate technology or framework (e.g. 'PostgreSQL', 'FastAPI', 'Redis')",
    )
    category: TechnologyCategory = Field(
        ...,
        description="Infrastructure or platform layer classification",
    )
    reason: str = Field(
        ...,
        min_length=5,
        description="Why this technology fits the project requirements and constraints",
    )
    trade_off: str = Field(
        ...,
        min_length=5,
        description="Notable operational, learning, or architectural trade-off to consider",
    )


class TradeOffAnalysis(BaseModel):
    """Comparative trade-off evaluation for key architectural decisions."""

    decision_area: str = Field(
        ...,
        min_length=3,
        description="Domain or architecture decision scope (e.g. 'Monolith vs Microservices')",
    )
    recommended_option: str = Field(
        ...,
        min_length=3,
        description="Option favored by the agent for current context",
    )
    advantages: list[str] = Field(
        ...,
        min_length=1,
        description="Key engineering benefits of the recommended option",
    )
    disadvantages: list[str] = Field(
        ...,
        min_length=1,
        description="Key risks or limitations of the recommended option",
    )
    alternative: str = Field(
        ...,
        min_length=3,
        description="Viable alternative architecture path",
    )
    alternative_tradeoff: str = Field(
        ...,
        min_length=5,
        description="Compromise or overhead required if selecting the alternative",
    )


class ArchitectureRequirementTrace(BaseModel):
    """Traceability mapping linking canonical requirements to recommended components."""

    requirement_id: uuid.UUID = Field(
        ...,
        description="UUID of the requirement present in canonical context",
    )
    component_names: list[str] = Field(
        ...,
        min_length=1,
        description="Declared component names that realize or address this requirement",
    )
    rationale: str = Field(
        ...,
        min_length=5,
        description="Explanation of how the assigned components satisfy the requirement",
    )


class ArchitectureRecommendationCandidate(BaseModel):
    """Raw candidate structured model emitted by LLM provider.
    
    Contains solely qualitative proposals. Spurious numeric quality scores are ignored.
    """

    model_config = ConfigDict(extra="ignore")

    summary: str = Field(
        ...,
        min_length=5,
        description="High-level engineering overview of the recommended architecture",
    )
    architecture_styles: list[ArchitectureStyleRecommendation] = Field(
        default_factory=list,
        description="Recommended architecture styles with justifications",
    )
    components: list[ComponentRecommendation] = Field(
        default_factory=list,
        description="Proposed major logical components",
    )
    data_flows: list[DataFlowRecommendation] = Field(
        default_factory=list,
        description="Interactions and data flows between components",
    )
    technologies: list[TechnologyRecommendation] = Field(
        default_factory=list,
        description="Candidate technology stack recommendations",
    )
    trade_offs: list[TradeOffAnalysis] = Field(
        default_factory=list,
        description="Trade-off analyses for key design choices",
    )
    assumptions: list[str] = Field(
        default_factory=list,
        description="Explicit assumptions made regarding unstated scale, traffic, or team structure",
    )
    constraints: list[str] = Field(
        default_factory=list,
        description="Project and technical constraints identified from context",
    )
    unknowns: list[str] = Field(
        default_factory=list,
        description="Important engineering unknowns requiring stakeholder clarification",
    )
    traceability_matrix: list[ArchitectureRequirementTrace] = Field(
        default_factory=list,
        description="Requirement-to-component traceability mappings",
    )


class ArchitectureRecommendationOutput(BaseModel):
    """Authoritative structured output envelope for Architecture Recommendation Agent.
    
    CRITICAL ARCHITECTURAL GUARANTEE:
    Recommendations are advisory only (Agent output == recommendation; Agent output != database mutation).
    The platform does NOT create schemas, commit code, or deploy infrastructure.
    """

    summary: str = Field(
        ...,
        min_length=5,
        description="High-level engineering overview of the recommended architecture",
    )
    architecture_styles: list[ArchitectureStyleRecommendation] = Field(
        default_factory=list,
        description="Recommended architecture styles with justifications",
    )
    components: list[ComponentRecommendation] = Field(
        default_factory=list,
        description="Proposed major logical components",
    )
    data_flows: list[DataFlowRecommendation] = Field(
        default_factory=list,
        description="Interactions and data flows between components",
    )
    technologies: list[TechnologyRecommendation] = Field(
        default_factory=list,
        description="Candidate technology stack recommendations",
    )
    trade_offs: list[TradeOffAnalysis] = Field(
        default_factory=list,
        description="Trade-off analyses for key design choices",
    )
    assumptions: list[str] = Field(
        default_factory=list,
        description="Explicit assumptions made regarding unstated scale, traffic, or team structure",
    )
    constraints: list[str] = Field(
        default_factory=list,
        description="Project and technical constraints identified from context",
    )
    unknowns: list[str] = Field(
        default_factory=list,
        description="Important engineering unknowns requiring stakeholder clarification",
    )
    traceability_matrix: list[ArchitectureRequirementTrace] = Field(
        default_factory=list,
        description="Requirement-to-component traceability mappings",
    )
