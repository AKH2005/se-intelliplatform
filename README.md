# SE IntelliPlatform

**An AI-Powered Multi-Agent Platform for Smart Software Development**

---

## 1. Project Overview

SE IntelliPlatform is an intelligent software engineering platform designed to assist and automate tasks across the Software Development Life Cycle (SDLC). The system is designed around an architecture-led methodology prioritizing deterministic validation, strict domain boundaries, and explainable AI assistance.

> **IMPORTANT PROJECT STATUS NOTICE:**  
> **Phase 1 (Foundation & Backend Infrastructure) is active.**  
> **AI agents are NOT implemented in Phase 1.**  
> Machine learning models, LLM integrations, RAG pipelines, authentication, and the React frontend client are strictly scheduled for subsequent development phases.

---

## 2. Architecture Principles

1. **Architecture Before Implementation:** Contracts, schemas, and boundaries precede feature implementation.
2. **Single Source of Truth:** Centralized canonical state prevents context drift across SDLC phases.
3. **Deterministic Business Logic:** AI is never the silent source of deterministic truth; calculations and constraints are verified by domain rule engines.
4. **Isolated Execution:** Code generated in future phases is never executed directly on the host operating system.
5. **Traceability & Explainability:** All future AI decisions maintain full provenance, citations, and explainability metrics.

---

## 3. Repository Structure

```text
se-intelliplatform/
│
├── .gitignore                      # Ignore rules for Python, Node, OS, and secrets
├── .editorconfig                   # Cross-editor formatting rules
├── .env.example                    # Template environment variables
├── docker-compose.yml              # Local PostgreSQL 16 & Redis 7 services
├── docker-compose.override.yml     # Local development container overrides
├── README.md                       # Project documentation
│
├── backend/
│   ├── pyproject.toml              # Modern Python packaging & pinned dependencies
│   ├── Dockerfile                  # Multi-stage non-root container image
│   ├── alembic.ini                 # Database migration configuration
│   ├── migrations/                 # Alembic migration scripts
│   │   ├── env.py                  # Migration runner with async support
│   │   └── versions/
│   │       └── 0001_initial_projects_table.py
│   │
│   ├── app/
│   │   ├── main.py                 # FastAPI application factory & lifespan
│   │   ├── core/                   # Cross-cutting concerns (config, logging, DB)
│   │   │   ├── config.py           # Pydantic BaseSettings with fail-fast checks
│   │   │   ├── database.py         # Async SQLAlchemy 2.0 engine & session
│   │   │   ├── exceptions.py       # Domain exception hierarchy
│   │   │   └── logging.py          # Structured JSON logger & correlation context
│   │   ├── api/                    # REST API routers & RFC 7807 error handlers
│   │   │   ├── dependencies.py     # Dependency injection providers
│   │   │   ├── error_handlers.py   # RFC 7807 problem details formatters
│   │   │   └── v1/
│   │   │       ├── api.py          # Router aggregator
│   │   │       └── endpoints/
│   │   │           ├── health.py   # System & DB health check
│   │   │           └── projects.py # Project CRUD & lifecycle endpoints
│   │   ├── models/                 # SQLAlchemy ORM entities
│   │   │   ├── base.py             # Declarative Base, UUID PK & timestamps
│   │   │   └── project.py          # Project entity with JSONB settings
│   │   ├── schemas/                # Pydantic v2 DTOs
│   │   │   ├── health.py           # Health response model
│   │   │   └── project.py          # ProjectCreate, ProjectUpdate, ProjectResponse
│   │   └── services/               # Business domain logic
│   │       └── project_service.py  # Project lifecycle management
│   │
│   └── tests/                      # Automated test suite
│       ├── conftest.py             # Async client & database test fixtures
│       ├── unit/                   # Configuration & schema unit tests
│       └── integration/            # API integration tests
│
├── frontend/
│   └── README.md                   # Frontend architectural boundary (Phase 7)
│
└── docs/
    └── architecture/
        └── foundation.md           # Foundation architecture specification
```

---

## 4. Prerequisites

* **Python:** 3.10 or newer (tested on 3.12 / 3.14)
* **Docker & Docker Compose:** For running PostgreSQL and Redis containers
* **Git:** For version control

---

## 5. Local Setup & Quickstart

### 5.1 Clone & Environment Configuration

```bash
# Clone the repository
git clone <repository-url>
cd "SE Intellplatform"

# Copy the environment template (NEVER commit .env to version control)
cp .env.example .env
```

### 5.2 Start Local Database & Cache Infrastructure

```bash
# Spin up PostgreSQL and Redis
docker compose up -d postgres redis

# Verify services are healthy
docker compose ps
```

### 5.3 Install Backend Dependencies

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
# On Windows PowerShell:
.venv\Scripts\Activate.ps1
# On Linux / macOS:
# source .venv/bin/activate

# Install dependencies with test extras
pip install --upgrade pip
pip install -e ".[test]"
```

### 5.4 Database Migrations (Alembic)

```bash
# Apply migrations to create the database schema
alembic upgrade head

# Roll back migration (to verify downgrade capability)
alembic downgrade base

# Re-apply migrations
alembic upgrade head
```

### 5.5 Start the Development Backend

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The interactive OpenAPI documentation will be accessible at:
* Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
* ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 6. Current API Endpoints (Phase 1)

All APIs are versioned under `/api/v1`:

| Method | Path | Description | Status Code |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/health` | Service health and database connectivity status | `200 OK` / `503 Service Unavailable` |
| `POST` | `/api/v1/projects` | Register a new project with unique slug | `201 Created` |
| `GET` | `/api/v1/projects` | Paginated project listing with status filter | `200 OK` |
| `GET` | `/api/v1/projects/{id}` | Retrieve project details by UUID | `200 OK` / `404 Not Found` |
| `PATCH` | `/api/v1/projects/{id}` | Partial update of project attributes | `200 OK` / `404 Not Found` |
| `DELETE`| `/api/v1/projects/{id}` | Safely archive project (soft deletion) | `200 OK` / `404 Not Found` |

---

## 7. Running Automated Tests

```bash
cd backend
pytest -v
```

To run with test coverage reporting:

```bash
pytest --cov=app --cov-report=term-missing
```

---

## 8. What is NOT Implemented Yet

To adhere to architecture-led engineering, the following capabilities are explicitly deferred:

* **AI Agents:** Requirement, Architecture, DB Design, Risk, Timeline, and Code Review agents.
* **Classical ML / XAI:** Scikit-learn predictive models and SHAP/LIME attribution engines.
* **Vector Store & Embeddings:** ChromaDB, FAISS, and RAG pipelines.
* **Frontend UI:** React.js dashboard and visualization components.
* **Authentication & Authorization:** User identity, JWT tokens, and role-based permissions.
* **Code Sandbox:** Containerized runtime for generated code.

These components will be introduced in subsequent planned phases.
