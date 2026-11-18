# Database Design Agent — Architecture Specification

## 1. Purpose
The **Database Design Agent** is the platform's third domain-specific AI agent. It evaluates software engineering requirements from canonical Project Context, optional requirement analysis findings (Phase 4), and optional architecture recommendations (Phase 5) to propose structured, modular, explainable, and traceably validated logical database designs for the target application.

## 2. Scope
- Analyzes canonical project context (`ProjectContextResponse`), optional requirement analysis (`RequirementAnalysisOutput`), and optional architecture recommendations (`ArchitectureRecommendationOutput`).
- Proposes logical entities/tables, attributes with data types, primary keys, relationships with explicit foreign-key ownership, performance/uniqueness indexes, integrity constraints, and trade-off analyses.
- Maps database entities back to canonical requirements and architecture components for full end-to-end SDLC traceability.
- Completely read-only: generates proposals for human engineers and does NOT create tables, execute DDL, or run migrations.

## 3. What the Agent Does NOT Do
- **No Database Mutation**: Zero modifications to requirements, projects, or application databases (`Agent output == recommendation; Agent output != database mutation`).
- **No SQL / DDL Execution**: Does not execute `CREATE TABLE`, `ALTER TABLE`, or SQL commands.
- **No Migration Generation**: Does not generate Alembic or Flyway migrations.
- **No Pseudo-Quality Scoring**: Prohibits inventing arbitrary numeric ratings (e.g. `database_quality = 94%`).
- **No Workflow Orchestration**: Does not execute Phase 4 or Phase 5 agents internally; all inputs are injected by the caller.

## 4. Input Contract
Supports four valid operational modes:
- **Mode A (Standalone)**: `ProjectContextResponse` alone.
- **Mode B**: `ProjectContextResponse` + `RequirementAnalysisOutput`.
- **Mode C**: `ProjectContextResponse` + `ArchitectureRecommendationOutput`.
- **Mode D (Full Context)**: `ProjectContextResponse` + `RequirementAnalysisOutput` + `ArchitectureRecommendationOutput`.

## 5. Output Contract
Emits `DatabaseDesignOutput`:
- `summary: str`: High-level data model overview.
- `database_paradigm: DatabaseParadigm`: Target paradigm (`RELATIONAL`, `DOCUMENT`, `KEY_VALUE`, `GRAPH`, `SEARCH`).
- `entities: list[EntityRecommendation]`: Entities with attributes and primary keys.
- `relationships: list[RelationshipRecommendation]`: Explicit foreign-key relationships.
- `indexes: list[IndexRecommendation]`: Proposed performance/uniqueness indexes.
- `constraints: list[ConstraintRecommendation]`: Additional domain/check constraints.
- `trade_offs: list[DatabaseTradeOff]`: Qualitative modeling trade-offs.
- `assumptions: list[str]`: Explicit volume/access pattern hypotheses.
- `constraints_notes: list[str]`: Technical storage constraints.
- `unknowns: list[str]`: Missing information requiring stakeholder clarification.
- `requirement_traceability: list[DatabaseRequirementTrace]`: Requirement-to-entity mappings.
- `architecture_traceability: list[DatabaseArchitectureTrace]`: Component-to-entity mappings.

## 6. Entity & Primary Key Model
Each entity defines:
- `name: str` (unique across entities)
- `description: str` & `purpose: str`
- `attributes: list[AttributeRecommendation]` (`name`, `data_type`, `nullable`, `description`, `default_value`, `unique`)
- `primary_key: PrimaryKeyRecommendation` (`attributes: list[str]`, `is_composite: bool`)
- `related_requirement_ids: list[UUID]`

## 7. Relationship Model & Explicit Foreign-Key Ownership
Every relationship captures explicit foreign-key ownership:
```text
source_entity: str
target_entity: str
relationship_type: RelationshipType (ONE_TO_ONE, ONE_TO_MANY, MANY_TO_ONE, MANY_TO_MANY)
source_cardinality: str (e.g. '1', '0..1', '1..*')
target_cardinality: str (e.g. '1', '0..1', '0..*')
foreign_key_entity: str (entity holding the FK column)
foreign_key_attributes: list[str] (column name(s) in foreign_key_entity)
referenced_entity: str (entity pointed to by the FK)
referenced_attributes: list[str] (column name(s) in referenced_entity)
junction_entity: str | None
description: str
```
Self-referential relationships (`source_entity == target_entity`) are supported and structurally validated.

## 8. Deterministic Validation Pipeline
Implemented in `validate_database_design_output`:
1. **Entity Name Uniqueness**: Rejects duplicate entity names.
2. **Attribute Uniqueness**: Rejects duplicate attribute names within an entity.
3. **Primary Key Consistency**: Rejects empty primary keys or primary keys referencing undeclared attributes.
4. **Foreign-Key Ownership Integrity**:
   - `foreign_key_entity` and `referenced_entity` must exist.
   - `foreign_key_attributes` must exist in `foreign_key_entity`.
   - `referenced_attributes` must exist in `referenced_entity`.
   - Parity in column counts between foreign keys and referenced keys.
5. **Index Integrity**: Target entity must exist; attributes must exist; index names must be unique.
6. **Constraint Non-Contradiction**:
   - Additional `PRIMARY_KEY` constraints must not contradict `entity.primary_key`.
   - Additional `FOREIGN_KEY` constraints must not contradict declared relationships.
7. **Requirement Traceability**: All requirement UUIDs must exist in active context.
8. **Architecture Traceability**: When Phase 5 input is present, components must exist in the recommendation. When absent, architecture components cannot be invented.

## 9. Provider Independence
- Interacts strictly with `AbstractLLMProvider`.
- Tested offline, deterministically, and with zero external cost using `MockLLMProvider`.
- Zero proprietary vendor SDKs (Google GenAI, OpenAI, Anthropic) imported into the agent package.

## 10. Security & Read-Only Guarantees
- Read-only operations.
- No DDL or SQL execution.
- No database tables created in PostgreSQL.
- Sanitized audit logging via Phase 3 `AgentExecutionAudit`.

## 11. Known Limitations & Future Evolution
- Does not automatically execute migrations against a live database (by design).
- Future Phase 7+ may introduce automated SQL/migration generation as a separate, human-approved downstream step.
