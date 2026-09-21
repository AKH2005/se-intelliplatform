# SE IntelliPlatform — Abstract Agent Framework & AI Infrastructure Specification

**Status:** Approved Baseline (Phase 3 Implemented)  
**Version:** 0.3.0  
**Phase:** Phase 3 — Abstract Agent Framework & AI Infrastructure Foundation  
**Authors:** SE IntelliPlatform Core Engineering Team  

---

## 1. System Architecture & Core Principles

The SE IntelliPlatform Agent Framework provides the foundational contracts, lifecycle state machine, validation pipelines, and provider abstractions for future SDLC intelligence agents.

```text
               PostgreSQL Database (Canonical Store)
                               │
                               ▼
               ProjectContextEngine (Deterministic)
                               │
                               ▼
                  Canonical ProjectContext
                               │
                               ▼
                     AbstractBaseAgent
                     (Typed Contracts)
                               │
                     ┌─────────┴─────────┐
                     ▼                   ▼
           AbstractLLMProvider    DeterministicValidator
            (Strategy Pattern)      (Two-Stage Gate)
                     │                   │
                     └─────────┬─────────┘
                               ▼
                       AgentResult[OutputT]
                               │
                               ▼
                      AgentExecutionAudit
                   (Context Version Tracking)
```

### Core Principles

1. **Canonical Context Consumption:** All future agents consume the canonical `ProjectContextResponse` emitted by `ProjectContextEngine`. Agents never execute ad-hoc SQL queries or reconstruct state independently.
2. **AI Proposes, Deterministic Validates:** External model outputs are strictly untrusted proposals until verified through structural schema parsing (Pydantic) and deterministic domain validation hooks.
3. **Vendor Independence:** The platform couples exclusively to the `AbstractLLMProvider` interface, not to any proprietary vendor SDK.
4. **Structured Results Envelope:** Every agent emits an `AgentResult[OutputT]` containing execution UUID, status, output, validation details, and exact context version.
5. **Traceability & Auditability:** Every execution is audited via `AgentExecutionAudit`, capturing start/completion timestamps, status, consumed context version, and error diagnostics.

---

## 2. Agent Lifecycle

Every agent execution progresses through a deterministic lifecycle state machine:

```text
    PENDING ──► RUNNING ──► VALIDATING ──► COMPLETED
                   │            │
                   ▼            ▼
                 FAILED ◄───────┘
```

1. **`initialize()`:** Pre-execution preparation (prompt template assembly, tool configurations).
2. **`analyze(context)`:** Pure deterministic feature extraction from the canonical `ProjectContextResponse`.
3. **`generate(analysis_result, provider)`:** Invokes the active `AbstractLLMProvider` to produce a structured proposal adhering to `output_schema`.
4. **`validate(output, context)`:** Two-stage verification:
   * **Stage 1 (Structural):** Pydantic type constraints, required fields, and format regex.
   * **Stage 2 (Deterministic):** Agent's `validate_output()` hook enforcing domain business invariants.
5. **`complete / failed`:** Final status emitted in `AgentResult[OutputT]` and recorded in `AgentExecutionAudit`.

---

## 3. Two-Stage Validation Pipeline

```text
Raw Model Output
       │
       ▼
[Stage 1: Pydantic Schema Validation]
       │
       ├── Failed ──► Rejection: AgentValidationError (Schema Invariant Violated)
       │
       ▼ (Passed)
[Stage 2: Deterministic Business Hook]
       │
       ├── Failed ──► Rejection: AgentValidationError (Domain Rule Violated)
       │
       ▼ (Passed)
Authoritative Accepted Output
```

* **No LLM in the Loop for Validation:** Deterministic business invariants (e.g. valid IDs, budget ceilings, dependency ordering) are strictly verified by deterministic Python code.

---

## 4. LLM Provider Abstraction & Strategy Pattern

Agents invoke models via `AbstractLLMProvider`:

```python
class AbstractLLMProvider(ABC):
    @property
    def provider_name(self) -> str: ...
    async def generate(self, request: LLMRequest) -> LLMResponse: ...
    async def generate_structured(self, request: LLMRequest, response_model: type[T]) -> T: ...
```

### Implemented vs. Planned Adapters

* **MockLLMProvider [IMPLEMENTED]:** Deterministic, zero-cost mock provider for unit tests, automated CI/CD, and offline verification. Supports canned text, structured models, and transient error simulation.
* **Google Gemini Adapter [PLANNED - Phase 4+]:** Provider adapter for Gemini 1.5 Pro / Flash.
* **OpenAI Adapter [PLANNED - Phase 4+]:** Provider adapter for GPT-4o / o1.
* **Anthropic Adapter [PLANNED - Phase 4+]:** Provider adapter for Claude 3.5 Sonnet.
* **Local / Open-Source Adapter [PLANNED - Phase 4+]:** Provider adapter for Ollama / vLLM.

---

## 5. Controlled Retry Boundary

To maximize platform resilience against transient network anomalies without entering unbounded loops:

* **Eligible for Retry:**
  * `TransientProviderError` (e.g. HTTP 429 rate limits, socket timeouts, temporary network blips).
  * Retried up to `LLM_MAX_RETRIES` (default: 3) with configurable backoff.
* **NOT Eligible for Retry (Fail-Fast):**
  * `AgentValidationError` (schema violations or deterministic business rule failures).
  * `AgentConfigurationError` (missing parameters or bad setup).
  * Authentication/Authorization failures.
  * Deterministic semantic errors.

---

## 6. Execution Audit & Context Versioning

The `AgentExecutionAudit` entity guarantees complete provenance:

| Column | Type | Description |
|---|---|---|
| `id` | UUID | Primary key |
| `execution_id` | UUID | Unique correlation UUID per execution |
| `project_id` | UUID | Foreign key to `projects.id` (`ON DELETE CASCADE`) |
| `agent_id` | VARCHAR(100) | Unique identifier (e.g. `'requirement-analysis'`) |
| `agent_version` | VARCHAR(32) | Semantic version of agent (e.g. `'1.0.0'`) |
| `status` | VARCHAR(32) | Lifecycle terminal status |
| `context_version` | INTEGER | Exact `ProjectContext.context_version` consumed |
| `started_at` | TIMESTAMPTZ | Execution start time (UTC) |
| `completed_at` | TIMESTAMPTZ | Execution end time (UTC) |
| `output_summary` | TEXT | High-level sanitized summary (no secrets or prompts) |
| `error_code` | VARCHAR(64) | Machine-readable error code if failed |
| `error_message` | TEXT | Descriptive failure diagnostic if failed |
| `metadata` | JSONB | Telemetry, provider name, latency metrics |

---

## 7. Agent Registry & API Discovery

Agents are registered on startup into `AgentRegistry`:
* `register(agent: AbstractBaseAgent)`: Enforces unique `agent_id`.
* `get(agent_id: str)`: Retrieves registered instance or raises `AgentNotFoundError`.
* `list_agents()`: Returns list of `AgentMetadata`.

### API Exposure
* `GET /api/v1/agents`: Public read-only discovery endpoint listing registered agent metadata.
* **Security Restriction:** Model execution is strictly restricted to internal backend services; no arbitrary `POST /agents/run` endpoint is exposed over HTTP.

---

## 8. Implementation Scope & Planned Roadmap

| Component | Status | Target Phase |
|---|---|---|
| Abstract Agent Contracts (`base`, `contracts`, `exceptions`) | **IMPLEMENTED** | Phase 3 |
| Two-Stage Validation Pipeline (`DeterministicValidator`) | **IMPLEMENTED** | Phase 3 |
| LLM Provider Interface & Mock Provider | **IMPLEMENTED** | Phase 3 |
| Controlled Retry Boundary (`AgentExecutor`) | **IMPLEMENTED** | Phase 3 |
| Execution Audit Model & Migration 0003 | **IMPLEMENTED** | Phase 3 |
| Agent Registry & Discovery Endpoint | **IMPLEMENTED** | Phase 3 |
| Requirement Analysis Agent | **PLANNED** | Phase 4 |
| Architecture Recommendation Agent | **PLANNED** | Phase 5 |
| Database Design Agent | **PLANNED** | Phase 5 |
| Code Generation & Review Agents | **PLANNED** | Phase 6 |
| Automated Test Generation Agent | **PLANNED** | Phase 6 |
| Production LLM Provider Adapters (Gemini, OpenAI) | **PLANNED** | Phase 4+ |
| RAG & Vector Database (FAISS, pgvector) | **PLANNED** | Phase 5+ |
| Multi-Agent Orchestration & Workflow Engine | **PLANNED** | Phase 7 |
