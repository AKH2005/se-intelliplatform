# Architecture Recommendation Agent — Architecture Specification

## 1. Purpose
The **Architecture Recommendation Agent** is the platform's second domain-specific AI agent. It evaluates the project's software requirements and validated requirement analysis findings to propose modular, sustainable, explainable, and context-appropriate software architectures.

## 2. Scope
- Analyzes canonical project context (`ProjectContextResponse`) and optional validated Phase 4 findings (`RequirementAnalysisOutput`).
- Proposes candidate architecture styles, components, communication paths, technology stacks, and trade-off analyses.
- Maps architecture components back to canonical requirements for end-to-end traceability.
- Completely read-only: generates proposals for human engineers and does not execute or deploy architecture.

## 3. Responsibilities
- **Context Synthesis**: Extract requirements and constraints to inform architectural decisions.
- **Proportional Architecture Selection**: Recommend architectures suited to known scale and operational needs (e.g. favoring modular monoliths when complexity is modest over premature microservices).
- **Component Decomposition**: Identify logical sub-systems and clear single-responsibility boundaries.
- **Interaction Modeling**: Define inter-component communication patterns and protocols.
- **Technology Evaluation**: Suggest candidate technology options with explicit trade-offs.
- **Trade-off Analysis**: Formulate structured pros, cons, and alternatives for major design decisions.
- **Traceability Verification**: Connect components directly to canonical requirement UUIDs.

## 4. Non-Responsibilities
- **No Database Mutation**: Zero modifications to requirements, projects, or settings.
- **No Direct Execution / Code Generation**: Does not generate implementation code, Dockerfiles, or CI/CD scripts.
- **No Schema Generation**: Does not write SQL DDL or entity models (reserved for future specialized agents).
- **No Pseudo-Quality Scoring**: Prohibits inventing arbitrary numeric quality ratings (e.g. `architecture_score = 94%`).
- **No Workflow Orchestration**: Does not internally execute Phase 4 agents; inputs are injected by the caller.

## 5. Input Contract
Consumes:
1. Canonical Phase 2 `ProjectContextResponse`: Contains project metadata, active requirements (`DRAFT`, `APPROVED`, `IMPLEMENTED`), and deterministic statistics.
2. Optional Phase 4 `RequirementAnalysisOutput`: Injected directly via `kwargs` (`requirement_analysis`), containing ambiguities, conflicts, and gaps.

## 6. Requirement Analysis Dependency
- The agent does NOT internally instantiate or execute `RequirementAnalysisAgent`.
- Operates in two distinct, valid modes:
  - **With Phase 4 Findings**: Enhanced context incorporating detected requirement conflicts and gaps.
  - **Standalone Mode**: Operates directly on `ProjectContextResponse` when Phase 4 findings are absent.

## 7. Output Contract
Emits `ArchitectureRecommendationOutput`:
- `summary: str`
- `architecture_styles: list[ArchitectureStyleRecommendation]`
- `components: list[ComponentRecommendation]`
- `data_flows: list[DataFlowRecommendation]`
- `technologies: list[TechnologyRecommendation]`
- `trade_offs: list[TradeOffAnalysis]`
- `assumptions: list[str]`
- `constraints: list[str]`
- `unknowns: list[str]`
- `traceability_matrix: list[ArchitectureRequirementTrace]`

## 8. Architecture Styles
Supported styles (`ArchitectureStyle` enum):
- `MONOLITH`
- `MODULAR_MONOLITH`
- `LAYERED`
- `CLEAN_ARCHITECTURE`
- `HEXAGONAL`
- `MICROSERVICES`
- `EVENT_DRIVEN`
- `SERVERLESS`

Each recommendation includes a rationale and an AI confidence assessment (0.0 to 1.0).

## 9. Component Recommendations
Each component includes:
- `name: str` (enforced unique across the recommendation)
- `responsibility: str`
- `reason: str`
- `related_requirement_ids: list[UUID]` (validated against active canonical requirements)

## 10. Data Flows
Each flow specifies:
- `source_component: str` (validated against declared components)
- `target_component: str` (validated against declared components)
- `interaction: str` (protocol/mechanism)
- `reason: str`

## 11. Technology Recommendations
Categories (`TechnologyCategory` enum):
- `FRONTEND`, `BACKEND`, `DATABASE`, `CACHE`, `MESSAGING`, `DEPLOYMENT`, `OBSERVABILITY`, `AUTHENTICATION`.
Each technology recommendation specifies candidate stack, justification, and notable trade-off.

## 12. Trade-Offs
Explicit comparison structure:
- `decision_area`: Scope of decision
- `recommended_option`: Favored architecture path
- `advantages`: List of engineering benefits
- `disadvantages`: List of engineering costs or risks
- `alternative`: Viable alternative pattern
- `alternative_tradeoff`: Compromises of the alternative

## 13. Assumptions and Unknowns
- **Assumptions**: Explicit hypotheses regarding unstated traffic, volume, or team organization.
- **Constraints**: Facts from requirements limiting design choices.
- **Unknowns**: Open questions requiring stakeholder answers.

## 14. Requirement Traceability
Bidirectional traceability:
- Components reference `related_requirement_ids`.
- The `traceability_matrix` explicitly maps each canonical requirement UUID to one or more components with rationale.
- All requirement references must exist in the canonical context.

## 15. Deterministic Validation Pipeline
Implemented in `validate_architecture_recommendation_output`:
1. **Requirement ID Validity**: Rejects any non-existent requirement UUIDs.
2. **Component Name Uniqueness**: Rejects duplicate component names.
3. **Data Flow Integrity**: Rejects flows referencing undeclared components or self-referential loops.
4. **Traceability Integrity**: Rejects references to undeclared components.
5. **Enum Adherence**: Validates `ArchitectureStyle` and `TechnologyCategory`.
6. **Trade-Off Completeness**: Requires non-empty advantages and disadvantages.

## 16. Provider Independence
- Interacts strictly with `AbstractLLMProvider`.
- Tested offline, deterministically, and with zero external cost using `MockLLMProvider`.
- Zero proprietary vendor SDKs imported into the agent package.

## 17. Security
- Read-only operations.
- No code execution or infrastructure deployment.
- Sanitized audit logging via Phase 3 `AgentExecutionAudit`.

## 18. Human Review Boundary
All architecture recommendations are advisory only (`Agent output == recommendation; Agent output != database mutation`). Human software architects must review, adjust, and approve architectural paths.

## 19. Known Limitations
- Does not persist architecture decisions to database tables (reserved for future phases).
- Does not generate ERDs, database schemas, or API endpoint specifications directly.

## 20. Future Evolution
- Future Phase 6+ may introduce Database Design Agent and Risk Prediction Agent consuming architecture recommendations.
- Interactive human-in-the-loop architecture approval workflows.
