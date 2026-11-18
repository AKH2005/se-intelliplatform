# SE IntelliPlatform — Database & Migrations Reference
**Relational Schema Architecture, Alembic Migration Revisions, and Pre-Execution Workflow**

---

## 1. Database Architecture & Engine Configuration

SE IntelliPlatform employs **SQLAlchemy 2.0 Async Engine** with dual-driver support:
- **Local Development / Capstone Demo**: `sqlite+aiosqlite:///./se_intelliplatform.db` (zero-setup local file).
- **Production / Staging**: `postgresql+asyncpg://...` (enterprise concurrent multi-user database).

### Session Lifecycle Management (`app/core/database.py`)
```python
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)
```
Database sessions are request-scoped using FastAPI's dependency injection (`Depends(get_db)`), ensuring all connection transactions either commit cleanly or roll back completely on unhandled exceptions.

---

## 2. Alembic Migration History (0001–0010)

The database schema has evolved through 10 deterministic, reviewable migrations managed under Alembic:

| Rev ID | Migration Title | Core Tables & Alterations |
| :---: | :--- | :--- |
| **0001** | `initial_schema` | Core entities: `users`, `projects`, `requirements`. |
| **0002** | `context_snapshots` | Snapshotting engine: `project_context_snapshots`. |
| **0003** | `workflow_executions` | Multi-agent execution tracking: `workflow_executions`. |
| **0004** | `code_artifacts` | Generated code files, AST hashes, and bundle metadata. |
| **0005** | `code_reviews` | Code review findings, severity categories, and rule violations. |
| **0006** | `test_intelligence` | Test suites, test cases, and tier classifications. |
| **0007** | `ai_testing_sandbox` | Execution runs, Docker container logs, and telemetry. |
| **0008** | `failure_analysis` | Anomaly diagnostics, root causes, and blast radiuses. |
| **0009** | `remediation_patches`| Code patches, unified diffs, and verification tokens. |
| **0010** | `production_hardening`| Tenancy indices, foreign key cascades, and status constraints. |

---

## 3. Production Schema Management Policy

In accordance with Phase 6D production readiness requirements:
- **Development**: Conveniently runs `Base.metadata.create_all` on startup to facilitate fast iteration if tables do not exist.
- **Production & Staging**: Automatically skips `create_all`. Database schema changes are **strictly delegated to Alembic migrations** to eliminate connection deadlocks and race conditions.

---

## 4. Pre-Execution Migration Runner (`scripts/migrate.py`)

To ensure zero-risk schema deployments, `backend/scripts/migrate.py` provides an automated pre-execution workflow:

```bash
# Check if database is in sync with latest head revision
python scripts/migrate.py --action check

# Apply all pending migrations (creates timestamped backup automatically on SQLite)
python scripts/migrate.py --action upgrade --revision head

# Roll back the most recent migration safely
python scripts/migrate.py --action downgrade --revision -1

# Inspect active schema revision
python scripts/migrate.py --action current
```

### Automatic SQLite Disaster Recovery Backup
When running migrations against SQLite, `migrate.py` automatically duplicates the active database file prior to executing any DDL:
`se_intelliplatform.backup_YYYYMMDD_HHMMSS.db`.
If a migration fails, the database can be restored immediately by copying the backup file back into place.
