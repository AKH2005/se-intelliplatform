# SE IntelliPlatform — Phase 8.5 Architecture Specification
## Workflow Execution Persistence & Run History

**Status:** Implementation Complete (Awaiting CTO Authorization)  
**Date:** September 2026  
**Author:** Implementation Engineering Team, SE IntelliPlatform  
**Baseline Git Commit:** `df4e736778e1d43128e871ca0905f9b01c4c540c` (`df4e736`)  
**Verified Baseline:** 433/433 Tests Passing (100%) | 0 Failures | Clean Working Tree  

---

## 1. Executive Summary & Problem Definition

In Phase 8.4 (`df4e736`), the multi-agent workflow engine was exposed via REST API endpoints (`POST /api/v1/workflows/{id}/execute`). While execution was fully deterministic and returned the authoritative `WorkflowResult` envelope directly to the client, the workflow execution run itself was strictly in-memory and request-scoped. Once the HTTP response completed, the workflow execution instance ceased to exist in persistent storage (only individual steps persisted audit rows via `AgentExecutionAudit` without parent grouping).

### Identified Architectural Problem
1. **Lack of Run History:** Clients and future user interfaces could not query past workflow runs or inspect prior execution outcomes.
2. **Ephemeral Artifacts:** If a client lost connection or refreshed the browser after execution, all synthesized artifacts were lost from memory.
3. **Missing Workflow-Level Provenance:** Individual agent executions in `agent_execution_audits` were not linked to a parent workflow execution run.

Phase 8.5 solves this by introducing durable, queryable workflow execution records in PostgreSQL while strictly maintaining the pure domain boundary of `WorkflowCoordinator`.

---

## 2. Architectural Hierarchy & Invariants

```
HTTP API (/api/v1/workflows, /api/v1/projects/{id}/workflows)
    │
    ▼
WorkflowService (Persistence Boundary & Session Owner)
    │
    ├──► PostgreSQL 16 Store (WorkflowExecution Table)
    │
    ├──► ProjectContextEngine (Canonical Context & Snapshot Resolution)
    │
    ▼
WorkflowCoordinator (Pure Domain Orchestration Engine — DB Unaware)
    │
    ▼
AgentExecutor (Step-Level Execution, Retry & AgentExecutionAudit Persistence)
    │
    ▼
Platform Agents (9 Domain Intelligence Agents)
```

### Invariants Maintained
1. **`WorkflowCoordinator` Remains Database-Unaware:** Zero database models, ORM entities, SQL queries, or session dependencies inside `backend/app/workflows/`.
2. **Service Layer Boundary:** `WorkflowService` owns the persistence lifecycle (initial record creation, state updates, artifact serialization, error capture).
3. **Backward Compatibility:** Existing Phase 8.4 execution endpoints continue to return `WorkflowResultResponse` with identical schemas.
4. **Step-Level Audit Integrity:** `AgentExecutionAudit` remains the authoritative record for single-agent execution telemetry.
5. **Synchronous Execution:** Workflows execute synchronously within the request lifespan; no distributed background workers or queues.

---

## 3. WorkflowExecution Persistence Model

Created in `backend/app/models/workflow_execution.py`:

```python
class WorkflowExecution(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "workflow_executions"

    id: Mapped[uuid.UUID]                               # PK (UUIDPrimaryKeyMixin)
    workflow_execution_id: Mapped[uuid.UUID]            # Unique indexed correlation UUID
    project_id: Mapped[uuid.UUID]                       # FK -> projects.id (CASCADE)
    workflow_id: Mapped[str]                            # String(100), indexed
    workflow_version: Mapped[str]                       # String(32)
    status: Mapped[WorkflowStatus]                      # Enum(WorkflowStatus, native_enum=False)
    context_snapshot_id: Mapped[uuid.UUID | None]       # FK -> project_context_snapshots.id (SET NULL)
    context_version: Mapped[int | None]                 # Integer, nullable
    started_at: Mapped[datetime]                        # DateTime(timezone=True)
    completed_at: Mapped[datetime | None]               # DateTime(timezone=True), nullable
    step_count: Mapped[int]                             # Total pipeline steps
    completed_steps: Mapped[int]                        # Steps completed successfully
    failed_steps: Mapped[int]                           # Steps that failed
    skipped_steps: Mapped[int]                          # Steps that were skipped
    artifacts: Mapped[dict[str, Any]]                   # JSONB dictionary of step artifacts
    errors: Mapped[list[str]]                           # JSONB list of error messages
    warnings: Mapped[list[str]]                         # JSONB list of warnings
    metadata_payload: Mapped[dict[str, Any]]            # JSONB column "metadata" (telemetry, options)
```

### Database Table Arguments & Indexes
- `ix_workflow_executions_workflow_execution_id`: Unique index for execution lookups.
- `ix_workflow_executions_project_id`: Index for project scoping.
- `ix_workflow_executions_status`: Index for lifecycle filtering.
- `ix_workflow_executions_started_at`: Index for temporal sorting.
- `ix_workflow_executions_project_status`: Compound index for project + status queries.
- `ix_workflow_executions_project_started`: Compound index for project history queries (`started_at DESC`).

---

## 4. Persistence Lifecycle & Transaction Boundary

The persistence lifecycle in `WorkflowService.execute_workflow()` progresses through 6 deterministic stages:

```text
1. Resolve Context ──► 2. Generate UUID ──► 3. Create Row (RUNNING) ──► 4. Execute Coordinator
                                                                               │
       ┌───────────────────────────────────────────────────────────────────────┴───────────────┐
       ▼                                                                                       ▼
[Success / Domain Terminal]                                                              [Unhandled Crash]
5. Count completed/failed/skipped steps                                                  Record FAILED status
   Serialize validated artifacts                                                         Capture exception text
   Update status (COMPLETED / PARTIAL_SUCCESS / FAILED)                                  Commit & re-raise
6. Commit & Return WorkflowResult
```

### Transaction Boundary
- The database session is injected via FastAPI's `Depends(get_db)`.
- The initial `WorkflowExecution` row is committed in `RUNNING` status before calling `coordinator.execute(...)`.
- If execution terminates normally (including domain failures), the row is updated with terminal statistics and committed.
- If an unhandled Python exception occurs, the catch block sets status to `FAILED`, persists the error message, commits, and re-raises the original exception to preserve RFC 7807 handler semantics.

---

## 5. API Endpoints

### 5.1 Project-Scoped Workflow History
- **Route:** `GET /api/v1/projects/{project_id}/workflows/history`
- **Query Parameters:**
  - `limit`: Integer, default 20, min 1, max 100.
  - `offset`: Integer, default 0, min 0.
  - `workflow_id`: Optional string filter (e.g. `software-design-workflow`).
  - `status`: Optional enum filter (`PENDING`, `RUNNING`, `COMPLETED`, `PARTIAL_SUCCESS`, `FAILED`).
- **Response:** `WorkflowHistoryListResponse` containing `items`, `total`, `limit`, and `offset`.

### 5.2 Workflow Execution Run Detail
- **Route:** `GET /api/v1/workflows/executions/{workflow_execution_id}`
- **Path Parameter:** `workflow_execution_id` (UUID format).
- **Response:** `WorkflowExecutionDetailResponse` containing complete execution identity, status, step metrics, artifacts, errors, warnings, and sanitized metadata.
- **Error:** 404 Not Found RFC 7807 Problem Details if ID does not exist.

---

## 6. Context Provenance Tracking

Persistence rigorously differentiates between live context runs and snapshot runs:
- **Live Context Run:** `context_snapshot_id = NULL`, `context_version = NULL`, `metadata.context_provenance = "live"`.
- **Snapshot Run:** `context_snapshot_id = <UUID>`, `context_version = <int>`, `metadata.context_provenance = "snapshot"`.

---

## 7. Security Safeguards

1. **No Secret Persistence:** Upstream provider API keys and environment variables are never written to `artifacts` or `metadata_payload`.
2. **No Raw Source Code Storage:** `CodeReviewAgent` inputs (raw user source code) are excluded from persistence. Only structured findings (`CodeReviewFinding`) are retained in the `artifacts` column.
3. **Deterministic Sanitization:** Request options are validated against an allowlist before execution (`fail_fast`). Client payloads cannot inject arbitrary JSON into database entities.
4. **Cascade Deletion:** Foreign key `ON DELETE CASCADE` from `projects.id` ensures deleting a project cleanly removes all associated workflow execution records without leaving orphaned data.

---

## 8. Failure Semantics & Crash Durability

- **Step Failure (Mandatory Step):** Status marked `FAILED`, blocking error recorded, artifacts from completed preceding steps preserved in database.
- **Step Failure (Optional Step):** Status marked `PARTIAL_SUCCESS`, warning recorded, execution continues to completion.
- **Unhandled Process Exception:** Catch block attempts to mark status `FAILED` with error text.
- **Hard Process Kill (SIGKILL / Power Outage):** A record may remain in `RUNNING` status. In the absence of an async background reconciliation daemon (explicit non-goal), hard process termination leaves the row in `RUNNING`.

---

## 9. Database Migration

- **Revision File:** `backend/migrations/versions/0005_workflow_executions.py`
- **Revision ID:** `0005_workflow_executions`
- **Revises:** `0004_audit_snapshot_provenance`
- **Operation:** Creates table `workflow_executions` and 10 indexes. Reversible via `downgrade()`.

---

## 10. Verification & Test Strategy

Comprehensive test suite in `backend/tests/unit/test_workflow_persistence.py`:
1. `test_workflow_execution_model_construction`: Entity field initialization, default values, and `__repr__`.
2. `test_workflow_execution_persisted_success`: Execution creates `COMPLETED` row with step counts and artifacts.
3. `test_workflow_execution_persisted_snapshot_provenance`: Execution persists `snapshot_id` and `version`.
4. `test_workflow_execution_persisted_partial_success`: Execution persists `PARTIAL_SUCCESS` and warnings.
5. `test_workflow_execution_security_no_source_code_persisted`: Verifies source code strings are not persisted.
6. `test_project_workflow_history_empty`: Returns empty list when no executions exist.
7. `test_project_workflow_history_pagination_and_sorting`: Verifies sorting by newest first, limit, and offset.
8. `test_project_workflow_history_filtering`: Verifies filtering by `workflow_id` and `status`.
9. `test_project_workflow_history_nonexistent_project`: Returns 404 for unknown project UUID.
10. `test_get_workflow_execution_detail_success`: Returns 200 OK with full execution detail.
11. `test_get_workflow_execution_detail_not_found`: Returns 404 for unknown execution UUID.

### Full Test Suite Results
- 433 tests passed in 16.16s (422 baseline + 11 new tests).
- 0 failures, 0 regressions.

---

## 11. Explicit Non-Goals for Phase 8.5

The following capabilities were deliberately excluded to maintain strict scope control:
- **No Background Task Queues:** Execution remains synchronous and request-scoped. No Celery, Redis, or Arq.
- **No Frontend Implementation:** UI remains cleanly separated and deferred to Phase 9.
- **No Authentication / RBAC:** JWT, user accounts, and permission models remain deferred.
- **No Event Streaming:** Server-Sent Events (SSE) and WebSockets remain deferred.
- **No Workflow Pause / Resume / Cancellation:** Workflows run sequentially to completion.
- **No Dynamic DAG Synthesis:** Pipelines remain predefined and deterministic.
