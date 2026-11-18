# SE IntelliPlatform — Project Context Engine & Deterministic Domain Specification

**Status:** Approved Baseline (Phase 2 Implemented)  
**Version:** 0.2.0  
**Phase:** Phase 2 — Project Context Engine & Deterministic Domain Foundation  
**Authors:** SE IntelliPlatform Core Engineering Team  

---

## 1. Primary Objective & Architectural Principle

In SE IntelliPlatform, future AI/ML software engineering intelligence agents must **never** independently query disparate database tables or reconstruct project state on their own. Context fragmentation leads to hallucination, state drift, and conflicting agent decisions.

Instead, the platform enforces the **Canonical Project Context Architecture**:

```text
PostgreSQL / Persistence Layer
               ↓
    ProjectContextEngine (Deterministic)
               ↓
    Canonical ProjectContext / Versioned Snapshot
               ↓
   ┌───────────────────────────────────────────┐
   │        Future AI / ML Agents              │
   │  (Requirements Analysis, Architecture,   │
   │   Code Generation, Review, Testing)       │
   │               [PLANNED]                   │
   └───────────────────────────────────────────┘
```

### Separation of Responsibilities

* **Deterministic Backend (Implemented in Phase 2):**
  * Business rules and validations
  * Mathematical calculations (completion percentage, metric tallies)
  * Lifecycle state transitions
  * Immutable snapshot versioning and persistence
* **AI / LLM Agents (PLANNED for Phase 3+):**
  * Semantic interpretation
  * Code and artifact generation
  * Architectural recommendations
  * Reasoning and natural language explanations

> [!IMPORTANT]
> **Zero LLM Dependency for Ground Truth:** Calculations, statistics, and domain constraints are computed strictly by deterministic Python backend algorithms. An LLM is never permitted to calculate or infer authoritative project state.

---

## 2. Requirement Domain

The `Requirement` entity captures structured software specifications.

### Entity Attributes

* `id` (UUID): Primary key.
* `project_id` (UUID): Foreign key to `projects.id` with `ON DELETE CASCADE`.
* `title` (VARCHAR(255)): Non-empty requirement summary.
* `description` (TEXT): Non-empty requirement details and acceptance criteria.
* `type` (VARCHAR(32)): Domain enum:
  * `FUNCTIONAL`: Behavioral features and user capabilities.
  * `NON_FUNCTIONAL`: Performance, scalability, security, and reliability attributes.
  * `CONSTRAINT`: Architectural, technological, or regulatory constraints.
* `priority` (VARCHAR(32)): Domain enum:
  * `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.
* `status` (VARCHAR(32)): Domain enum:
  * `DRAFT`, `APPROVED`, `IMPLEMENTED`, `DEFERRED`, `REJECTED`.
* `is_archived` (BOOLEAN): Soft-delete flag (defaults to `false`).
* `created_at` / `updated_at` (TIMESTAMP WITH TIME ZONE): UTC timestamps.

### Requirement Deletion & History Preservation

In accordance with core engineering principles, software requirements represent critical institutional context and historical intelligence. Therefore:
* `DELETE /api/v1/projects/{project_id}/requirements/{requirement_id}` performs a **soft-archive** operation (`is_archived = true`).
* Requirements are preserved in the persistence store.
* Physical hard deletion is restricted exclusively to internal automated test teardown fixtures.

---

## 3. Project Context Inclusion Rules

When `ProjectContextEngine` compiles the canonical Project Context, it applies deterministic inclusion rules:

| Requirement Status | Included in Active Canonical Context? | Justification |
|---|---|---|
| `DRAFT` | **INCLUDED** | Active in-progress requirement definition |
| `APPROVED` | **INCLUDED** | Ready for architecture, planning, or implementation |
| `IMPLEMENTED` | **INCLUDED** | Active completed feature providing codebase context |
| `DEFERRED` | **EXCLUDED** | Postponed from the active milestone/scope |
| `REJECTED` | **EXCLUDED** | Discarded requirement; preserved only for audit history |
| *(Archived)* (`is_archived=true`) | **EXCLUDED** | Inactive or soft-deleted items |

---

## 4. Deterministic Statistics Calculation

All statistical aggregations are calculated by `ProjectContextEngine.calculate_statistics()` without external model dependencies:

1. **Active Requirements:**
   $$\text{active\_requirements} = |\text{DRAFT}| + |\text{APPROVED}| + |\text{IMPLEMENTED}|$$
   *(where $is\_archived = false$)*

2. **Completion Percentage:**
   $$\text{completion\_percentage} = \begin{cases} 
   \text{round}\left(\frac{|\text{IMPLEMENTED}|}{\text{active\_requirements}} \times 100.0, \, 2\right) & \text{if } \text{active\_requirements} > 0 \\
   0.0 & \text{if } \text{active\_requirements} = 0
   \end{cases}$$

3. **Breakdowns:**
   * Category tallies: `functional_count`, `non_functional_count`, `constraint_count`.
   * Priority distribution: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.
   * Complete lifecycle audit distribution: counts for all statuses including deferred and rejected.

---

## 5. Immutable Context Snapshots

To enable reproducible agent executions, regressions testing, and audit trails, SE IntelliPlatform provides **Versioned Context Snapshots**:

* **Immutability Guarantee:** Once a `ContextSnapshot` row is created, it is completely immutable. No `PATCH`, `PUT`, or `DELETE` endpoints exist for snapshots.
* **Sequential Versioning:** Snapshots within a project increment strictly sequentially: $v1, v2, v3, \dots$.
* **Concurrency Handling:** A database `UniqueConstraint("project_id", "version")` guarantees integrity. If concurrent creation attempts collide on version $N$, `ProjectContextEngine` automatically catches the integrity violation, rolls back, re-evaluates the latest sequence, and retries.
* **Storage:** Canonical JSON context payload is stored using PostgreSQL-native `JSONB`.

---

## 6. API Endpoints Reference

All endpoints reside under the `/api/v1` namespace and implement RFC 7807 Problem Details for all error conditions:

### Requirements API

| Method | Path | Summary | Success Status |
|---|---|---|---|
| `POST` | `/api/v1/projects/{project_id}/requirements` | Create requirement | 201 Created |
| `GET` | `/api/v1/projects/{project_id}/requirements` | List requirements (supports `skip`, `limit`, `type`, `priority`, `status`, `include_archived`) | 200 OK |
| `GET` | `/api/v1/projects/{project_id}/requirements/{requirement_id}` | Get requirement details | 200 OK |
| `PATCH` | `/api/v1/projects/{project_id}/requirements/{requirement_id}` | Partial update of requirement attributes | 200 OK |
| `DELETE` | `/api/v1/projects/{project_id}/requirements/{requirement_id}` | Soft-archive requirement (preserves history) | 200 OK |

### Project Context & Snapshots API

| Method | Path | Summary | Success Status |
|---|---|---|---|
| `GET` | `/api/v1/projects/{project_id}/context` | Get active canonical project context & deterministic stats | 200 OK |
| `POST` | `/api/v1/projects/{project_id}/context/snapshots` | Commit a new immutable point-in-time snapshot ($v_{N+1}$) | 201 Created |
| `GET` | `/api/v1/projects/{project_id}/context/snapshots` | List historical snapshots (version descending) | 200 OK |
| `GET` | `/api/v1/projects/{project_id}/context/snapshots/{version}` | Retrieve specific historical snapshot by version number | 200 OK |

---

## 7. Future Extension Points (Phase 3+)

The canonical Project Context schema is deliberately architected to incorporate downstream SDLC domains in future phases without breaking changes:

* `architecture`: Component diagrams, service boundaries, technology selections **[PLANNED - Phase 4]**
* `database_schema`: ER models, migration plans, table definitions **[PLANNED - Phase 4]**
* `risk_indicators`: Deterministic complexity and security risk ratings **[PLANNED - Phase 5]**
* `testing_matrix`: Generated test coverage targets and validation plans **[PLANNED - Phase 6]**
* `code_artifacts`: Generated source modules, review reports, and execution logs **[PLANNED - Phase 6+]**

All future agents will interface with Project Context via a strongly typed `AbstractProjectContextConsumer` interface.
