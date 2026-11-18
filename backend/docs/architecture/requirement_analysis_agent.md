# Requirement Analysis Agent — Architecture Specification

## 1. Purpose
The **Requirement Analysis Agent** is the initial domain-specific AI agent of the SE IntelliPlatform. It inspects software engineering requirements assembled in canonical Project Context, identifies requirement ambiguities, flags logical contradictions/conflicts across requirement pairs, highlights missing engineering specifications, and provides advisory refinements and scope clarification questions.

## 2. Responsibilities
- **Ambiguity Detection**: Detect vague, non-verifiable, or underspecified requirements.
- **Conflict Identification**: Detect logical contradictions and mutual impossibilities between pairs of active requirements.
- **Specification Gap Detection**: Identify missing architectural, security, error-handling, or operational constraints.
- **Constructive Refinement**: Provide advisory improvement recommendations (e.g. clearer phrasing, suggested type/priority reclassification).
- **Scope Clarifications**: Formulate questions to clarify project boundaries with stakeholders.

## 3. Non-Responsibilities
- **No Database Mutation**: The agent is strictly read-only. Suggestions are advisory only (`Agent output == recommendation; Agent output != database mutation`). The agent NEVER creates, updates, deletes, or archives requirements.
- **No Autonomous Execution Loops**: The agent does not trigger follow-up execution or other agents.
- **No Direct LLM SDK Dependencies**: Operates exclusively through `AbstractLLMProvider`.
- **No Orchestration Ownership**: Execution lifecycle, retries, and auditing are owned exclusively by `AgentExecutor`.
- **No Authoritative Deterministic Metrics Calculation**: The LLM is strictly prohibited from generating authoritative completeness scores or requirement counts.

## 4. Input Contract
The agent strictly consumes the canonical `ProjectContextResponse` produced by the Phase 2 `ProjectContextEngine`.
It never queries the database, ORM entities, or raw tables directly:
```text
ProjectContextResponse
├── project: ProjectResponse
├── requirements: list[RequirementResponse] (active requirements only: DRAFT, APPROVED, IMPLEMENTED)
├── statistics: RequirementStatistics
│   ├── total_requirements: int
│   ├── active_requirements: int
│   ├── functional_count: int
│   ├── non_functional_count: int
│   ├── constraint_count: int
│   └── completion_percentage: float
├── context_version: int
└── generated_at: datetime
```

## 5. Output Contract
Emits the validated, strongly typed `RequirementAnalysisOutput` structured envelope:
- `summary: str` — High-level engineering assessment
- `ambiguities: list[RequirementAmbiguity]` — Ambiguity findings with requirement UUID, issue, explanation, suggested clarification, and severity
- `conflicts: list[RequirementConflict]` — Conflict findings with primary requirement UUID, related requirement UUID, issue, explanation, and severity
- `missing_information: list[MissingInformation]` — Specification gaps by area, description, reason, and severity
- `refinements: list[RequirementRefinement]` — Advisory suggestions with target UUID, suggestion, reason, and optional suggested type/priority
- `scope_clarifications: list[ScopeClarification]` — Boundary questions with topic, question, and rationale
- `completeness_score: float` — Authoritatively injected from `context.statistics.completion_percentage`
- `active_requirements_count: int` — Authoritatively injected from `context.statistics.active_requirements`
- `total_requirements_count: int` — Authoritatively injected from `context.statistics.total_requirements`

## 6. AI Responsibilities vs. Deterministic Responsibilities

| Responsibility | Handled By | Enforcement Mechanism |
|---|---|---|
| Ambiguity interpretation | LLM | Structured prompt + schema validation |
| Conflict reasoning | LLM | Structured prompt + schema validation |
| Missing information analysis | LLM | Structured prompt + schema validation |
| Refinement suggestions | LLM | Advisory schema (`RequirementRefinement`) |
| Requirement ID validity | Deterministic Backend | Domain validation against active context IDs |
| Conflict peer integrity | Deterministic Backend | Distinct ID verification & existence check |
| Enum compliance | Deterministic Backend | Pydantic & domain enum membership check |
| Completeness calculation | Deterministic Backend | Injected from `context.statistics.completion_percentage` |
| Active/Total counts | Deterministic Backend | Injected from `context.statistics.active_requirements` |

## 7. Validation Pipeline
Two-stage validation pipeline:
1. **Stage 1 — Schema Validation**: Verifies candidate output matches `RequirementAnalysisCandidate` / `RequirementAnalysisOutput`.
2. **Stage 2 — Deterministic Domain Validation Hook (`validate_requirement_analysis_output`)**:
   - Rejects any nonexistent requirement UUIDs.
   - Rejects self-referential conflicts (`requirement_id == related_requirement_id`).
   - Validates that `suggested_type` and `suggested_priority` match Phase 2 domain enums.
   - Verifies `completeness_score`, `active_requirements_count`, and `total_requirements_count` equal canonical context statistics.

## 8. Provider Abstraction
The agent interfaces with LLMs solely through `AbstractLLMProvider.generate_structured(...)`.
Zero vendor SDKs (such as OpenAI, Anthropic, or Google GenAI) are imported.
Testing is conducted completely offline, deterministically, and with zero cost using `MockLLMProvider`.

## 9. Execution Flow
```text
AgentExecutor.execute(agent, context, session, snapshot)
        ↓
RequirementAnalysisAgent.initialize()
        ↓
RequirementAnalysisAgent.analyze(context)
        ↓
RequirementAnalysisAgent.generate(analysis_data, provider)
        ↓ [Prompt + AbstractLLMProvider.generate_structured]
Candidate Output (RequirementAnalysisCandidate)
        ↓ [Deterministic Metric Injection]
Candidate Output + Context Statistics -> RequirementAnalysisOutput
        ↓
DeterministicValidator.run_pipeline(...)
        ↓ [Stage 1: Pydantic Schema Check]
        ↓ [Stage 2: Deterministic Domain Hook Check]
AgentResult[RequirementAnalysisOutput]
        ↓
AgentExecutionAudit Persistence (PENDING -> RUNNING -> VALIDATING -> COMPLETED)
```

## 10. Security Boundaries
- **No Arbitrary Public Execution**: The platform exposes only metadata discovery (`GET /api/v1/agents`). No public endpoint allows triggering arbitrary executions over HTTP.
- **Sanitized Audit Records**: Auditing records only high-level output summaries and error codes; no sensitive payloads or raw prompts are recorded.
- **Deterministic Guardrails**: Untrusted LLM output cannot fabricate requirement references or spoof project completion statistics.

## 11. Testing Strategy
- Unit tests verify metadata, canonical context consumption, ambiguity/conflict handling, reference validation, spoof rejection, and no database mutations using `MockLLMProvider`.
- Regression verification guarantees Phase 1, Phase 2, and Phase 3 suites continue to pass with 0 failures and >= 80% coverage.

## 12. Known Limitations & Future Evolution
- **Phase 4 Scope**: Read/analyze/suggest only.
- **Future Workflow (Phase 5+)**: Future phases may introduce human-in-the-loop review to accept or reject suggestions, as well as downstream architectural agents that consume verified requirement analysis.
