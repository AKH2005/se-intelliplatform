# Phase 11J — Stage 2 Implementation Report
## ApplicationRuntimeManager + Isolated Docker Application Runtime

**Date:** 2026-10-02  
**Status:** COMPLETE  
**Stage:** Phase 11J — Stage 2 Only  
**Previous Baseline:** 813 / 813 tests passing (Phase 11J Stage 1 frozen)  
**Current Test Suite:** 833 / 833 tests passing (813 baseline regression + 16 new unit tests + 4 live Docker integration tests)  

---

## 1. Baseline
Prior to Phase 11J Stage 2:
- Phase 11A–11I and Phase 11J Stage 1 were completed and frozen.
- Phase 11J Stage 1 created foundational contracts: `ApplicationRuntimeManifest`, `BrowserTestRun`, `BrowserTestCaseResult`, `BrowserArtifactReference`, browser telemetry contracts, and `VerificationSnapshot.browser_validation`.
- Existing test baseline stood at 813 passing backend tests.
- Docker sandbox execution (`backend/app/sandbox/docker_executor.py`) existed strictly as a one-shot execution environment for pytest and static analysis.
- Stage 2 objective: Implement the isolated application runtime required to start a generated application safely inside Docker without touching the test sandbox, without publishing host ports, without Playwright/browser automation, and with strict concurrency and security guarantees.

---

## 2. Files Inspected
- `backend/app/sandbox/docker_executor.py`: Reviewed existing sandbox isolation patterns, non-root user (UID 2000), security flags (`--cap-drop=ALL`, `--security-opt=no-new-privileges:true`), and resource bounds. Confirmed separation of responsibilities: existing executor remains strictly for one-shot test execution.
- `backend/app/schemas/runtime.py`: Verified `ApplicationRuntimeManifest`, `RuntimeFramework`, `RuntimeLanguage`, safe startup commands, and health-check specifications.
- `backend/app/models/development_version.py`: Verified `DevelopmentVersion` model, `project_id`, `version_number`, and `workflow_execution_id` linkages.
- `backend/app/models/workflow_execution.py`: Verified artifact storage and access to `CodeGenerationOutput` JSON files.
- `backend/app/services/development_version_service.py`: Verified authoritative resolution patterns for development versions.
- `backend/Dockerfile.sandbox`: Verified sandbox image contents (`python:3.11-slim`, non-root user `sandboxuser`, UID 2000, pre-installed Python libraries).

---

## 3. Runtime Architecture
The application runtime subsystem is housed in a clean, dedicated package:
```
backend/app/runtime/
├── __init__.py                     # Clean package exports
├── contracts.py                    # RuntimeStatus, RuntimeLimits, RuntimeSessionConfig, RuntimeSessionResult
├── errors.py                       # Runtime exception hierarchy
├── docker_runtime_executor.py      # Hardened, zero-port, unprivileged Docker CLI executor
└── application_runtime_manager.py  # Orchestrator: artifact resolution, isolation, lifecycle, cleanup
```

### Architectural Separation
```
+-------------------------------------------------------------+
|                     SE IntelliPlatform                      |
+-------------------------------------------------------------+
                               |
               +---------------+---------------+
               |                               |
               v                               v
+-----------------------------+ +-----------------------------+
|   DockerSandboxExecutor     | |  ApplicationRuntimeManager  |
| (backend/app/sandbox/)      | |   (backend/app/runtime/)    |
| - One-shot pytest/analysis  | | - Long-running app session  |
| - No network                | | - Dedicated internal bridge |
| - Untouched & Frozen        | | - Concurrency cap (max 2)   |
+-----------------------------+ +-----------------------------+
                                               |
                                               v
                                +-----------------------------+
                                |    DockerRuntimeExecutor    |
                                | - Zero host ports published |
                                | - Non-root (UID 2000)       |
                                | - Read-only workspace mount |
                                | - Internal health probe     |
                                +-----------------------------+
```

---

## 4. ApplicationRuntimeManager Design
`ApplicationRuntimeManager` manages the high-level lifecycle of starting, health-probing, and terminating generated application containers:
- **Validation:** Authoritatively resolves `DevelopmentVersion` by `version_id` and validates project ownership (`project_id == version.project_id`). Rejects cross-project access deterministically.
- **Artifact Resolution:** Inspects `version.workflow_execution_id`, loads the `code_generation_output` artifact, and extracts file paths and contents.
- **Manifest Resolution:** Authoritatively extracts `ApplicationRuntimeManifest` from the artifact or falls back to a deterministic default FastAPI manifest.
- **Workspace Materialization:** Writes files to a unique, ephemeral host directory (`tempfile.mkdtemp`), validating that every file path is relative and strictly contained inside the workspace.
- **Concurrency Management:** Enforces a maximum concurrency limit of 2 concurrent runtime sessions using an asynchronous semaphore. Excess requests immediately receive `RuntimeStatus.RESOURCE_LIMIT`.
- **Lifecycle Guarantees:** Employs an asynchronous context manager (`managed_runtime_session`) with a deterministic `finally:` block ensuring container stoppage, container removal, network removal, and workspace deletion.

---

## 5. DockerRuntimeExecutor Design
`DockerRuntimeExecutor` encapsulates all direct Docker CLI operations using `asyncio.create_subprocess_exec`:
- **No Shell Execution:** `shell=True` is strictly prohibited. Commands are executed as fixed argument vectors `["docker", ...]` without shell interpolation.
- **Dedicated Internal Network:** Creates a unique internal bridge network (`docker network create --internal --driver bridge {network_name}`).
- **Container Creation:** Starts the application container with hardened flags:
  - `--read-only` root filesystem.
  - `--cap-drop=ALL` (drops all Linux capabilities).
  - `--security-opt=no-new-privileges:true`.
  - `--user=2000:2000` (non-root `sandboxuser`).
  - `--network={network_name}`.
  - `--name={container_name}`.
  - `--hostname={container_name}`.
  - `--workdir=/workspace`.
  - `-v {workspace_dir}:/workspace:ro` (read-only application source mount).
  - `--tmpfs /tmp:rw,size=64m` (isolated writable scratch space).
  - `--tmpfs /home/sandboxuser:rw,size=64m`.
  - Resource limits: `--memory=512m`, `--cpus=1.0`, `--pids-limit=64`.
  - **Zero Host Ports:** No `-p` or `--publish` flag is ever passed.
- **Internal Health Probing:** Probes application health via an unprivileged in-container probe (`docker exec -u 2000:2000 {container_name} python -c "..."`) polling `127.0.0.1:{port}{path}` internally without publishing host ports.
- **Diagnostics Capture:** Captures bounded stdout/stderr via `docker logs`, enforcing strict byte limits.

---

## 6. Artifact Resolution
Artifact resolution is strictly authoritative:
1. `DevelopmentVersion` is queried by ID within the database session.
2. `version.project_id` must match the caller's authorized `project_id`. If mismatched, raises `RuntimeConfigurationError("Version ... does not belong to project ...")`.
3. `version.workflow_execution_id` is queried from `WorkflowExecution`. If missing or not completed, raises `RuntimeConfigurationError`.
4. Artifact `code_generation_output` is parsed into a structured `CodeGenerationOutput` model.
5. All file paths are validated against path traversal (`..`, absolute paths, Windows drive letters, backslashes).
6. Runtime manifest is validated against the Pydantic schema `ApplicationRuntimeManifest`.

---

## 7. Workspace Isolation
- Created in an ephemeral system directory using `tempfile.mkdtemp(prefix="se_app_workspace_")`.
- Only generated source files from `code_generation_output` are written into the workspace.
- Prohibited paths (`.git`, `.env`, `.env.*`, `..`, absolute paths, backend secrets) are strictly rejected during workspace population.
- The directory is mounted into the container as **read-only** (`:ro`), preventing any runtime modification of the materialized files.
- Guaranteed deletion in `finally:` via `shutil.rmtree(temp_dir, ignore_errors=True)`.

---

## 8. Docker Network Design
- Ephemeral network name: `se_net_{run_uuid}`.
- Created with `--driver bridge --internal`.
- The `--internal` flag cuts off all external internet / WAN routing from the container.
- Container receives deterministic hostname `app-{run_uuid}`.
- Future Stage 3 browser container will join this internal network to communicate with `http://app-{run_uuid}:{application_port}`.
- Removed immediately upon session completion or error in `finally:`.

---

## 9. Container Security
| Security Control | Implementation | Verification |
|---|---|---|
| User | Non-root `2000:2000` (`sandboxuser`) | Verified via `id -u` / `id -g` in integration tests |
| Root Filesystem | Read-only (`--read-only`) | Verified via flags in unit & integration tests |
| Capabilities | Dropped all (`--cap-drop=ALL`) | Verified via flag inspection |
| Privileges | `--security-opt=no-new-privileges:true` | Verified via flag inspection |
| Docker Socket | Inaccessible (never mounted) | Verified via `test -e /var/run/docker.sock` in integration tests |
| Privileged Mode | Disabled (never used) | Verified in code & unit tests |
| Memory Limit | Bounded to 512 MB (`--memory=512m`) | Verified via flags |
| CPU Limit | Bounded to 1.0 CPU (`--cpus=1.0`) | Verified via flags |
| PID Limit | Bounded to 64 PIDs (`--pids-limit=64`) | Verified via flags |
| Writable Areas | Isolated tmpfs (`/tmp:rw,size=64m`) | Verified via flags |
| Host Ports | None (`-p` / `--publish` forbidden) | Verified via `docker port` returning empty |

---

## 10. Startup Process
1. Manifest `startup_command` validated as tokenized argument vector (e.g. `["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]`).
2. Arguments passed directly to `docker run -d ... image *startup_command`.
3. Process launches in background inside the isolated Docker container.
4. Container startup timeout (default 15.0 seconds) is monitored.

---

## 11. Health-Check Process
1. Health-check settings extracted from manifest (`health_check_path`, `application_port`, `health_check_method`, `health_check_timeout_seconds`).
2. Deterministic internal URL target: `http://127.0.0.1:{application_port}{health_check_path}` inside container namespace.
3. Health probe executes via `docker exec -u 2000:2000 container_name python -c "..."` connecting to internal HTTP endpoint.
4. Polled iteratively at bounded intervals (default 0.5s) up to manifest timeout (capped at 60s).
5. If container exits before health check passes, immediately captures exit code and stderr diagnostics.
6. Returns `(True, "HTTP 200 OK")` or `(False, failure_reason)`.

---

## 12. Timeout Handling
- **Startup / Health Timeout:** Bounded by `manifest.health_check_timeout_seconds` (default 15s, maximum 60s).
- **Session Timeout:** Bounded by `limits.session_timeout_seconds` (default 60s).
- On timeout, `RuntimeStatus.TIMEOUT` is recorded, bounded logs are gathered, and `stop_and_remove_container` is invoked immediately.

---

## 13. Concurrency Handling
- Enforced via class-level `asyncio.Semaphore(2)` in `ApplicationRuntimeManager`.
- If 2 sessions are active, a 3rd concurrent request does not block indefinitely; it immediately returns `RuntimeStatus.RESOURCE_LIMIT` with failure reason: `"Maximum concurrent application runtime sessions (2) reached."`.
- When an active session completes (or fails), the semaphore is reliably released in `finally:`.

---

## 14. Cleanup Guarantees
Deterministic cleanup order in `finally:`:
1. `docker_executor.stop_and_remove_container(container_name)` (stops within 5s grace period, then force removes).
2. `docker_executor.remove_network(network_name)` (removes the internal bridge network).
3. `shutil.rmtree(temp_dir, ignore_errors=True)` (removes ephemeral host workspace).
4. Semaphore released.
Guaranteed to execute on success, startup failure, health check timeout, process exit, invalid config, or unhandled exception.

---

## 15. Logging Limits
- Stdout and stderr logs captured via `docker logs` with bounded tail (`--tail=1000`).
- Strict byte truncation enforced: `RuntimeLimits.max_log_bytes = 50 * 1024` (50 KB).
- Truncated logs include deterministic marker: `"\n... [TRUNCATED - EXCEEDED 51200 BYTES] ..."`.
- Zero secrets, `.env` files, or Docker daemon internals exposed.

---

## 16. Unit Tests
16 unit tests added in `backend/tests/unit/test_application_runtime.py`:
1. `test_manifest_resolution_valid`: Validates parsing and default fallback.
2. `test_cross_project_version_rejection`: Validates cross-project access failure.
3. `test_version_not_found`: Validates 404 behavior for unknown versions.
4. `test_missing_workflow_execution`: Validates failure on incomplete executions.
5. `test_missing_code_generation_artifact`: Validates handling of missing code artifacts.
6. `test_workspace_materialization_and_cleanup`: Validates clean write and cleanup of temp workspace.
7. `test_workspace_rejects_path_traversal`: Validates blocking of `..` and relative escapes.
8. `test_workspace_rejects_sensitive_files`: Validates blocking of `.env` and `.git`.
9. `test_docker_run_args_security`: Validates presence of `--cap-drop=ALL`, `--security-opt`, `--read-only`, non-root user, limits, and **absence of `-p` / `--publish`**.
10. `test_concurrency_limit_enforced`: Validates semaphore capacity capping at 2 and immediate `RESOURCE_LIMIT` rejection for 3rd session.
11. `test_health_check_polling_success`: Validates successful health check lifecycle.
12. `test_health_check_polling_timeout`: Validates timeout handling when health check never succeeds.
13. `test_health_check_premature_exit`: Validates detection of early container termination.
14. `test_bounded_log_capture`: Validates 50 KB log truncation and marker insertion.
15. `test_cleanup_guarantee_on_exception`: Validates complete teardown during unexpected runtime errors.
16. `test_managed_runtime_session_context_manager`: Validates async context manager lifecycle and cleanup.

**Result:** 16 / 16 PASSED.

---

## 17. Docker Integration Tests
4 integration tests added in `backend/tests/integration/test_runtime_docker.py` executing against the live Docker daemon:
1. `test_live_docker_availability`: Confirms Docker daemon is online and responsive.
2. `test_live_isolated_application_runtime_lifecycle`:
   - Creates live internal network `se_net_*`.
   - Starts live container with non-root UID 2000.
   - Verifies zero host ports published (`docker port` returns empty).
   - Verifies Docker socket `/var/run/docker.sock` is absent/inaccessible.
   - Verifies health endpoint returns HTTP 200 OK.
   - Verifies clean shutdown, container removal, and network deletion.
3. `test_live_invalid_application_fails_safely`:
   - Runs application script that exits with code 42.
   - Verifies health poll detects early container exit.
   - Verifies clean teardown of failed container and network.
4. `test_live_health_check_timeout_handles_safely`:
   - Runs server probing non-existent 404 endpoint.
   - Verifies bounded timeout is enforced without hanging or resource leaks.
   - Verifies clean teardown.

**Result:** 4 / 4 PASSED in 13.22s.

---

## 18. Security Audit
Automated audit of `backend/app/runtime/`:
- `shell=True`: **ZERO** instances.
- `os.system`: **ZERO** instances.
- `eval(` / `exec(`: **ZERO** instances.
- `/var/run/docker.sock`: **ZERO** mounts (inaccessible).
- Host ports (`-p` / `--publish`): **ZERO** published.
- Subprocess calls: Strictly fixed `asyncio.create_subprocess_exec("docker", ...)`.
- Security flags: `--cap-drop=ALL`, `--security-opt=no-new-privileges:true`, `--read-only`, `--user=2000:2000` enforced on every container creation.
- Result: **PASS**.

---

## 19. Persistence Decision
- In-memory typed `RuntimeSessionResult` is returned by `ApplicationRuntimeManager`.
- Zero database migrations introduced.
- No `runtime_sessions`, `containers`, or `docker_networks` tables created.
- Preserves database schema stability.

---

## 20. Files Changed / Created
### Created:
- `backend/app/runtime/__init__.py`
- `backend/app/runtime/contracts.py`
- `backend/app/runtime/errors.py`
- `backend/app/runtime/docker_runtime_executor.py`
- `backend/app/runtime/application_runtime_manager.py`
- `backend/tests/unit/test_application_runtime.py`
- `backend/tests/integration/test_runtime_docker.py`
- `docs/architecture/Phase_11J_Stage2_Implementation_Report.md`

### Modified:
- None.

---

## 21. Files Deliberately Not Changed
- `backend/app/sandbox/docker_executor.py`: Untouched and preserved for one-shot test execution.
- `backend/app/schemas/runtime.py`: Untouched (Stage 1 schema frozen).
- `backend/app/schemas/browser_testing.py`: Untouched (Stage 1 schema frozen).
- `backend/app/services/verification_service.py`: Untouched.
- `backend/app/services/engineering_action_service.py`: Untouched.
- `frontend/*`: Zero frontend changes.
- `backend/migrations/*`: Zero database migrations.

---

## 22. Deferred Stage 3+ Work
The following items remain strictly deferred to subsequent stages:
- **Stage 3:** Playwright browser automation container, Chromium runner, screenshot capture, DOM inspection, browser test execution.
- **Stage 4:** FailureAnalysis agent browser evidence ingestion and browser test remediation.
- **Stage 5:** EngineeringAction `RUN_BROWSER_TESTS`, Assistant integration, REST API endpoints, and frontend UI.

---

## 23. Git Status
`git status --short`:
- Zero commits made.
- Zero pushes made.
- Working tree contains only Stage 1 and Stage 2 files.

---

## 24. Definition of Done Checklist
- [x] `ApplicationRuntimeManager` exists
- [x] Dedicated Docker runtime executor exists
- [x] Existing `DockerSandboxExecutor` remains unchanged
- [x] Generated artifact is resolved through `DevelopmentVersion`
- [x] No arbitrary filesystem path accepted
- [x] Runtime manifest is authoritative
- [x] Application workspace is isolated
- [x] Ephemeral Docker network created
- [x] Network is internal
- [x] No host port publishing
- [x] No host networking
- [x] Application runs as non-root (`sandboxuser`, UID 2000)
- [x] `--cap-drop=ALL`
- [x] `--security-opt=no-new-privileges:true`
- [x] Bounded memory (512 MB)
- [x] Bounded CPU (1.0)
- [x] Bounded PIDs (64)
- [x] No Docker socket
- [x] No privileged mode
- [x] Source artifact mounted read-only (cannot be mutated)
- [x] Startup command uses validated argv
- [x] No shell interpolation
- [x] Health endpoint is internal only
- [x] Health timeout enforced
- [x] Total runtime timeout enforced
- [x] Maximum concurrency enforced (2 concurrent sessions)
- [x] Cleanup guaranteed in `finally:`
- [x] No orphan container
- [x] No orphan network
- [x] Bounded logs (50 KB cap)
- [x] No secrets in logs/results
- [x] Unit tests pass (16/16)
- [x] Docker integration tests pass (4/4 on live Docker daemon)
- [x] Existing 813 backend tests remain passing (813/813)
- [x] No frontend changes
- [x] No Playwright
- [x] No browser execution
- [x] No Assistant browser actions
- [x] No new Agent
- [x] No new Workflow
- [x] No LLM calls
- [x] No database migration
- [x] No Git commit
- [x] No Git push

---

## 25. Final Verdict
Phase 11J Stage 2 is **COMPLETE**, fully tested, hardened, and verified with zero regressions across the existing platform.
