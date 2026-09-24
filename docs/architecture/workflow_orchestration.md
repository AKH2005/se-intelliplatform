# Multi-Agent Workflow Orchestration Architecture

**Status:** Approved & Implemented (Phase 8.3)
**Version:** 1.0.0
**Authors:** Implementation Engineering Team, SE IntelliPlatform

---

## 1. System Architecture & Hierarchy

The SE IntelliPlatform Workflow Orchestration layer provides deterministic, strongly typed multi-agent pipeline coordination across the platform's intelligence agents.

The orchestration architecture maintains a strict, unidirectional execution hierarchy:

```text
                  ┌────────────────────────────────────────┐
                  │          API / Service Layer           │
                  └───────────────────┬────────────────────┘
                                      │
                                      ▼
                  ┌────────────────────────────────────────┐
                  │          WorkflowCoordinator           │
                  │   - Deterministic Step Evaluation      │
                  │   - Predefined Pipeline Resolution     │
                  │   - In-Memory Artifact Routing         │
                  │   - Failure Propagation & Status Rules │
                  └───────────────────┬────────────────────┘
                                      │
                                      ▼ (Invokes per step)
                  ┌────────────────────────────────────────┐
                  │             AgentExecutor              │
                  │   - Sole Single-Agent Authority        │
                  │   - Lifecycle Transitions              │
                  │   - Transient Provider Retries         │
                  │   - Two-Stage Validation Gate          │
                  │   - Audit Log Persistence              │
                  └───────────────────┬────────────────────┘
                                      │
                                      ▼ (Lifecycle hooks)
                  ┌────────────────────────────────────────┐
                  │           AbstractBaseAgent            │
                  │   - initialize()                       │
                  │   - analyze(context, **kwargs)         │
                  │   - generate(analysis, provider)       │
                  │   - validate_output(output, context)   │
                  └────────────────────────────────────────┘
```

### Prohibited Execution Patterns
- **FORBIDDEN:** `Agent -> Agent` (Agents never import, instantiate, or invoke other agents).
- **FORBIDDEN:** `Agent -> WorkflowCoordinator` (Agents are completely unaware of workflows).
- **FORBIDDEN:** `Agent -> AgentExecutor` (No nested execution engines within an agent lifecycle).
- **FORBIDDEN:** `AgentExecutor -> AgentExecutor` (AgentExecutor executes exactly one agent at a time).

---

## 2. Core Coordinator Responsibilities

The `WorkflowCoordinator` (`app.workflows.coordinator.py`) operates strictly as an orchestration and routing engine:

1. **Declarative Step Resolution:** Iterates sequentially through `WorkflowStep` entries defined in a `WorkflowDefinition`.
2. **Deterministic Dependency Gating:** Checks prerequisite step statuses before executing a step. If a required dependency failed or was skipped, the dependent step is automatically marked `SKIPPED`.
3. **Explicit Artifact Routing:** Calls predefined pipeline adapters (`pipelines.py:resolve_step_kwargs`) to map upstream typed agent outputs into target agent keyword arguments.
4. **Sole Reliance on AgentExecutor:** Dispatches each step exclusively through `AgentExecutor.execute()`, preserving the single-agent execution authority.
5. **In-Memory Artifact Preservation:** Caches typed domain outputs (`AgentResult.output`) in an in-memory dictionary keyed by `step_id` and `agent_id`.
6. **Deterministic Workflow Status Calculation:** Computes the terminal `WorkflowStatus` based on required vs. optional step outcomes.

### Epistemic & Domain Boundaries
The `WorkflowCoordinator` is strictly **domain-agnostic**:
- It never parses, alters, or synthesizes claims.
- It never alters numerical risk scores or duration estimates.
- It never modifies database designs or requirement texts.
- It never uses an LLM to decide workflow execution order, retries, or success criteria.

---

## 3. The AgentExecutor Boundary

`AgentExecutor` remains the frozen, authoritative single-agent execution engine:
- **Inner Retry Loop:** `AgentExecutor` owns retries for transient provider failures (`TransientProviderError`, up to 3 attempts). The `WorkflowCoordinator` **never** retries steps at the workflow level.
- **Validation Rejection:** Deterministic validation rejections (`AgentValidationError`) are immediately terminal in `AgentExecutor` and marked as `FAILED` in the workflow step result.
- **Audit Persistence:** `AgentExecutor` persists each agent execution to `agent_execution_audits`. The workflow coordinator does not create duplicate audit records.

---

## 4. Artifact Routing & Adapters

Cross-agent data passing is performed deterministically through explicit adapter functions in `app/workflows/pipelines.py`:

```text
[Step: requirement-analysis]
             │
             ▼ RequirementAnalysisOutput
[Step: architecture-recommendation] (enriched by requirement_analysis)
             │
             ▼ ArchitectureRecommendationOutput
[Step: database-design] (enriched by requirement_analysis & architecture_recommendation)
             │
             ▼ All Completed Outputs
[Step: explainability-insights] (consumes ExplainabilityInput with all available outputs)
```

### Precondition & Skip Rules
- **Code Review:** `CodeReviewAgent` requires external source files (`CodeReviewInput`). If `workflow_input.code_review_input` is `None`, the coordinator marks the step `SKIPPED` with an explicit reason, permitting the rest of the workflow to continue.
- **Explainability Insights:** Requires at least one successful upstream output. If no upstream outputs are available, the step is marked `SKIPPED` with an explicit reason. The coordinator **never** fabricates fallback insights.

---

## 5. Workflow States & Transition Lifecycle

```text
    PENDING ──► RUNNING ──► COMPLETED
                   │            ▲
                   ▼            │
                 FAILED    PARTIAL_SUCCESS
```

### Terminal Status Determinism
1. **`COMPLETED`:** Every step in the workflow executed and completed with `AgentExecutionStatus.COMPLETED`.
2. **`PARTIAL_SUCCESS`:** All required steps completed successfully, but one or more optional steps failed or were skipped (with at least one successful step overall).
3. **`FAILED`:** Any required step failed or was skipped due to a prerequisite failure, or zero steps succeeded in the entire workflow.

---

## 6. Failure Semantics & Error Recovery

| Failure Mode | Level | Behavior | Workflow Outcome |
| :--- | :--- | :--- | :--- |
| **Transient Provider Error** | Agent | Retried up to 3 times by `AgentExecutor`. | If exhausted, step marks `FAILED`. |
| **Deterministic Validation Error** | Agent | Immediately terminal; zero retries. | Step marks `FAILED`. |
| **Mandatory Step Failure** | Workflow | Halts dependent steps; marks them `SKIPPED`. | Workflow marks `FAILED`. |
| **Optional Step Failure** | Workflow | Preserves error; downstream steps fallback to base context. | Workflow marks `PARTIAL_SUCCESS`. |
| **Independent Step Failure** | Workflow | Other independent steps continue executing. | Workflow marks `PARTIAL_SUCCESS`. |

---

## 7. Provenance & Correlation

Multi-agent execution guarantees unbroken traceability:
1. **Identical Context Guarantee:** Every step in a single workflow run receives the exact same `ProjectContextResponse` instance.
2. **Snapshot Consistency:** If execution is snapshot-backed, all steps receive the identical `context_snapshot_id` and `context_version`.
3. **Workflow Execution ID:** Every workflow execution generates a unique `workflow_execution_id: uuid.UUID` which is forwarded to `AgentExecutor.execute(**kwargs)`.
4. **Step-to-Agent Traceability:** Each `WorkflowStepResult` records the agent's unique `execution_id` alongside the step status and error diagnostics.

---

## 8. Predefined Pipelines

### 1. Software Design Workflow (`software-design-workflow`)
- **Step 1:** `requirement-analysis` (`required=True`)
- **Step 2:** `architecture-recommendation` (`required=False`, `depends_on=["requirement-analysis"]`)
- **Step 3:** `database-design` (`required=True`, `depends_on=["requirement-analysis", "architecture-recommendation"]`)

### 2. Project Estimation Workflow (`project-estimation-workflow`)
- **Step 1:** `risk-prediction` (`required=False`, independent supervised Ridge regression)
- **Step 2:** `timeline-prediction` (`required=False`, independent supervised RandomForest)
- **Step 3:** `bug-prediction` (`required=False`, independent supervised Logistic Regression)

### 3. Comprehensive Audit Workflow (`comprehensive-audit-workflow`)
- **Steps 1–7:** Requirements, Architecture, Database, Risk, Timeline, Bug, Test Cases
- **Step 8:** `code-review` (optional, executed if `code_review_input` is provided)
- **Step 9:** `explainability-insights` (terminal grounded explanation synthesizing all available upstream outputs)

---

## 9. Security & Privacy Safeguards

- **Credential Redaction:** The workflow coordinator never interferes with `CodeReviewAgent`'s secret scanning and pre-LLM redaction.
- **Source Code Privacy:** Source code files are routed strictly to `CodeReviewAgent`. Downstream synthesis receives only structured findings.
- **No Sensitive Metadata:** `WorkflowResult.metadata` records only aggregate counters and project identifiers; no prompts, raw inputs, or credentials.
- **Static Analysis Only:** No dynamic execution of user-supplied or AI-generated code.

---

## 10. Explicitly Deferred Features

The following capabilities are deliberately excluded from Phase 8.3:
1. Autonomous LLM-driven planning or dynamic agent selection.
2. Unrestricted multi-agent conversational debates.
3. Persistent workflow execution database tables or Alembic migrations.
4. Distributed task queues (Celery, Redis, RabbitMQ, Kafka).
5. Public workflow REST endpoints.
6. Vector database / RAG search infrastructure.
7. Runtime code execution / sandboxing.
