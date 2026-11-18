# SE IntelliPlatform

**Autonomous & AI-Assisted Multi-Agent Platform for Continuous Software Engineering**

---

## 1. Project Overview

SE IntelliPlatform is a complete, production-grade intelligent software engineering platform designed to assist and automate tasks across the Software Development Life Cycle (SDLC):

$$\text{DESCRIBE} \longrightarrow \text{ANALYZE} \longrightarrow \text{DESIGN} \longrightarrow \text{BUILD} \longrightarrow \text{RUN} \longrightarrow \text{TEST} \longrightarrow \text{DEBUG} \longrightarrow \text{IMPROVE} \longrightarrow \text{DEPLOY} \longrightarrow \text{OBSERVE}$$

The platform is built on an architecture-led methodology prioritizing deterministic validation, strict domain boundaries, immutable versioning, secure sandbox execution, and explainable AI assistance.

---

## 2. Platform Architecture & Core Guarantees

1. **Single Source of Truth:** Centralized canonical state and project context prevent context drift across engineering stages.
2. **Deterministic Business Logic:** AI assists, explains, and proposes; deterministic domain rule engines verify all requirements, schemas, regression scopes, and promotion gates.
3. **Execution Boundaries:**
   - **`AgentExecutor`:** Single authoritative execution engine for individual AI agents with schema validation and audit logging.
   - **`WorkflowCoordinator`:** Single authoritative orchestrator for multi-agent DAG pipelines.
   - **`DockerSandboxExecutor` / `IsolatedRuntimeDeploymentAdapter`:** Secure containerized sandbox boundaries with non-root execution, resource limits, no privileged containers, and network isolation.
4. **Immutable Versioning:** `DevelopmentVersion` records are append-only and cryptographically verified via content SHA-256 and manifest hashes.
5. **Human-in-the-Loop Governance:** All consequential state mutations (patch application, activation, deployment, and rollback) require explicit human confirmation.
6. **Project Isolation:** Complete logical and relational data isolation across projects, contexts, versions, deployments, and assistant conversations.

---

## 3. Product Capabilities

| SDLC Phase | Capability | Authoritative Engine / Agent | User Interface | Status |
| :--- | :--- | :--- | :--- | :--- |
| **DESCRIBE** | Requirements Management & Snapshots | `ProjectContextEngine`, `RequirementService` | Specification Workspace | **IMPLEMENTED** |
| **ANALYZE** | Ambiguity & Completeness Analysis | `RequirementAnalysisAgent`, `RiskPredictionAgent` | Intelligence Workspace | **IMPLEMENTED** |
| **DESIGN** | System Architecture & Database ERD | `ArchitectureRecommendationAgent`, `DatabaseDesignAgent` | Specification & Workflows | **IMPLEMENTED** |
| **BUILD** | Scaffold Planning & Code Generation | `CodeGenerationPlanningAgent`, `CodeGenerationAgent` | Development Workspace | **IMPLEMENTED** |
| **RUN** | Containerized Isolated Sandbox Runtime | `DockerSandboxExecutor`, `SandboxExecutionService` | Development / Sandbox View | **IMPLEMENTED** |
| **TEST** | Multi-Tier Test Synthesis & Execution | `TestCaseGenerationAgent`, `RegressionTestExecutor` | Testing & Quality Workspace | **IMPLEMENTED** |
| **TEST (E2E)** | Browser Smoke & Journey Automation | `BrowserJourneyService`, Playwright Headless Runner | Testing Workspace | **IMPLEMENTED** |
| **DEBUG** | Root-Cause Localization & Remediation | `FailureAnalysisAgent`, `RemediationProposalAgent` | Issues & Debugging Workspace | **IMPLEMENTED** |
| **IMPROVE** | Polyglot Code Intelligence | Python, TypeScript, JavaScript, Java Adapters | Code Intelligence Workspace | **IMPLEMENTED** |
| **IMPROVE** | Impact Analysis & Regression Planning | `ImpactAnalysisService`, `RegressionPlanner` | Testing Intelligence Dashboard | **IMPLEMENTED** |
| **DEPLOY** | Multi-Environment Promotion & Rollback | `EnvironmentService`, `DeploymentExecutionService` | Environments Workspace | **IMPLEMENTED** |
| **ASSIST** | Intelli Assistant (34+ Actions) | `AssistantReasoningService`, `EngineeringActionService` | Intelli Assistant Dock | **IMPLEMENTED** |
| **OBSERVE** | Real-Time Telemetry & Event Streaming | `TelemetryBroadcaster`, SSE & WebSocket Pipeline | Live Execution Feed | **IMPLEMENTED** |

---

## 4. Repository Structure

```text
se-intelliplatform/
├── backend/
│   ├── app/
│   │   ├── agents/                 # Multi-agent implementations (analysis, design, code-gen, remediation)
│   │   ├── api/v1/endpoints/       # Domain REST routers (requirements, workflows, testing, environments, assistant)
│   │   ├── core/                   # Cross-cutting concerns (config, logging, async DB, security)
│   │   ├── models/                 # SQLAlchemy 2.0 ORM models (projects, versions, environments, deployments)
│   │   ├── sandbox/                # Docker sandbox executor, static analysis, container isolation
│   │   ├── schemas/                # Pydantic v2 DTOs and contracts
│   │   ├── services/               # Authoritative domain services (code intelligence, regression, deployment)
│   │   ├── telemetry/              # Real-time event streaming and subscription management
│   │   └── workflows/              # Workflow definitions, DAG coordinator, and execution engines
│   ├── migrations/                 # Alembic migrations (current head: 0008_environments_and_deployments)
│   └── tests/                      # Automated test suite (1,279+ unit and integration tests)
│
├── frontend/
│   ├── src/
│   │   ├── components/             # Reusable UI components (artifacts, environments, assistant, testing)
│   │   ├── context/                # Global project and telemetry context
│   │   ├── services/               # Typed API clients for all backend endpoints
│   │   ├── types/                  # TypeScript contracts matching backend Pydantic schemas
│   │   ├── views/                  # Primary workspaces (Overview, Specification, Development, Testing, Environments, Issues)
│   │   └── styles/                 # Glassmorphism design system tokens and utilities
│   └── src/test/                   # Vitest UI test suite (107 tests across 19 suites)
│
└── docs/                           # Architectural specifications and phase implementation reports
```

---

## 5. Prerequisites

- **Python:** 3.10+ (tested on Python 3.12 / 3.14)
- **Node.js:** 18+ (tested on Node.js 20+)
- **Docker & Docker Compose:** For isolated sandbox execution and backing services
- **PostgreSQL 16 & Redis 7**

---

## 6. Quickstart

### 6.1 Start Backing Services
```bash
docker compose up -d postgres redis
```

### 6.2 Backend Setup
```bash
cd backend
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Linux / macOS:
# source .venv/bin/activate

pip install -e ".[test]"
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Interactive API docs:
- Swagger: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### 6.3 Live Preview Runtime Server
To run the interactive project Live Preview runtime on Port 8001:
```bash
cd backend
uvicorn app.runtime.preview_server:app --reload --host 127.0.0.1 --port 8001
```
Live Preview endpoint: [http://127.0.0.1:8001](http://127.0.0.1:8001)

### 6.4 Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Web Application: [http://localhost:5173](http://localhost:5173)

---

## 7. Running Verification & Test Suites

### Backend Test Suite
```bash
cd backend
pytest tests/ -v
# Total: 1,287 passing tests (1,168 unit tests, 119 integration tests)
```

### Frontend Test Suite & Production Build
```bash
cd frontend
npm test        # 128 passing tests across 23 test suites
npm run build   # Type-check (tsc) & Vite production bundle compilation
```

---

## 8. Unsupported & External Capabilities

To maintain engineering transparency, the following capabilities are explicitly classified as outside platform boundaries:

- **Unsupported Code Languages:** Non-targeted languages (e.g., C/C++, Rust, Go, Ruby, PHP) are explicitly classified as `UNSUPPORTED` / `UNKNOWN` by the polyglot code intelligence adapter.
- **Direct Arbitrary Host Execution:** Arbitrary shell execution on the host OS is prohibited by design; all dynamic code execution is confined to non-root Docker sandboxes.
- **Direct Unverified Production Mutation:** Direct deployment from `DEVELOPMENT` to `PRODUCTION` is prohibited; all releases must pass deterministic verification and `STAGING` promotion gates.
