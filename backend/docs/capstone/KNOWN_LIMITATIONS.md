# SE IntelliPlatform — Known Limitations & Architectural Boundaries
**Transparent Academic Capstone Boundaries, Trade-offs, and Future Work**

---

## 1. Context & Academic Scope

SE IntelliPlatform is designed as an academic capstone demonstration platform rather than an enterprise multi-tenant commercial SaaS product. While engineered to production-grade architectural standards with rigorous security boundaries and comprehensive testing, specific architectural trade-offs have been intentionally chosen to prioritize **local-first reproducibility, zero cloud spend, and hardware portability**.

---

## 2. Technical Limitations & Operational Boundaries

### 1. Local SQLite Concurrency Characteristics
- **Current Behavior**: By default, the application runs on SQLite (`se_intelliplatform.db`) using `aiosqlite`.
- **Limitation**: While SQLite supports high-throughput read operations via WAL (Write-Ahead Logging), concurrent write operations are serialized through database-level file locks. Rapid parallel write transactions across multiple background tasks can occasionally experience SQLite busy timeouts.
- **Production Recommendation**: For multi-user enterprise deployments with high concurrent write volume, configure `DATABASE_URL=postgresql+asyncpg://...`. All models, migrations, and queries are natively compatible with PostgreSQL.

### 2. Local Docker Sandbox Requirement for Live Runtime
- **Current Behavior**: The live application preview runtime (Port 8001) relies on Docker Engine API to spin up isolated container instances.
- **Limitation**: If Docker Desktop is not installed or not running on the evaluator's workstation, real container isolation is bypassed in favor of the local fallback runtime executor.
- **Mitigation**: The platform gracefully degrades without crashing, continuing to serve mocked preview responses and static file inspection.

### 3. Multi-Tab WebGL GPU Memory Footprint
- **Current Behavior**: SE IntelliPlatform renders 7 rich 3D volumetric scenes using Three.js and React Three Fiber.
- **Limitation**: Opening many simultaneous browser tabs or repeatedly switching between heavy 3D workspaces on integrated GPU laptops can stress browser WebGL context limits (browsers typically enforce a maximum of 8–16 simultaneous active WebGL contexts).
- **Mitigation**: Workspaces implement explicit WebGL resource disposal on unmount, and every 3D viewer provides an instant 1-click Accessible 2D Fallback view.

### 4. Mock LLM Provider vs Live Inference
- **Current Behavior**: To guarantee 100% test reproducibility and zero-spend execution, `LLM_PROVIDER=mock` is the default setting in `.env.example`.
- **Limitation**: In mock mode, agents return pre-registered canonical responses rather than generating novel, prompt-specific synthesis.
- **Production Recommendation**: To experience dynamic generative reasoning, set `LLM_PROVIDER=groq` or `LLM_PROVIDER=gemini` with your respective free API key.

### 5. Single-Node Background Tasks
- **Current Behavior**: Asynchronous workflow execution (`/execute-async`) dispatches jobs using FastAPI's in-process `BackgroundTasks`.
- **Limitation**: If the backend server process is abruptly terminated or restarted while an asynchronous workflow is executing, the background task will terminate without automatic retry.
- **Production Recommendation**: For distributed scale, integrate Celery or Temporal with Redis/RabbitMQ message brokers.
