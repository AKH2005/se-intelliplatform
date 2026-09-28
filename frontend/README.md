# SE IntelliPlatform Frontend Client

## 1. Overview & Purpose
The **SE IntelliPlatform Frontend** is a modern, high-performance developer workspace and orchestration console built for Software Engineering intelligence. It provides engineering teams and platform architects with interactive controls for:
- Canonical project and requirement management
- Immutable context snapshot tracking and deterministic progress metrics
- Dynamic discovery and synchronous orchestration of predefined multi-agent SDLC workflows
- Modular visualization of validated domain artifacts emitted by all 9 framework agents
- Audit logging and run history inspection backed by persisted workflow execution records

---

## 2. Architecture & Tech Stack
- **Framework:** React 18 with TypeScript 5
- **Build System:** Vite 6
- **Server Cache & State Synchronization:** TanStack React Query v5
- **UI State Management:** React Context (`ProjectContext` for active project scoping)
- **Styling:** Custom Obsidian Dark Design System using Vanilla CSS (Glassmorphism, CSS tokens, zero heavy third-party CSS libraries)
- **Iconography:** Lucide React
- **Testing:** Vitest, React Testing Library, and jsdom

---

## 3. Directory Structure
```
frontend/
├── package.json
├── tsconfig.json
├── tsconfig.node.json
├── vite.config.ts
├── index.html
├── .env.example
├── README.md
└── src/
    ├── main.tsx
    ├── App.tsx
    ├── styles/
    │   ├── tokens.css
    │   ├── globals.css
    │   └── components.css
    ├── types/
    │   ├── api.ts
    │   ├── project.ts
    │   ├── requirement.ts
    │   ├── context.ts
    │   ├── workflow.ts
    │   ├── agent.ts
    │   └── artifacts.ts
    ├── services/
    │   ├── apiClient.ts
    │   ├── projectsApi.ts
    │   ├── requirementsApi.ts
    │   ├── contextApi.ts
    │   ├── workflowsApi.ts
    │   └── historyApi.ts
    ├── context/
    │   └── ProjectContext.tsx
    ├── components/
    │   ├── common/
    │   ├── layout/
    │   ├── projects/
    │   ├── requirements/
    │   ├── workflows/
    │   ├── artifacts/
    │   └── history/
    ├── views/
    │   ├── ProjectWorkspace.tsx
    │   ├── RequirementsWorkspace.tsx
    │   ├── WorkflowStudio.tsx
    │   └── RunHistory.tsx
    └── test/
        ├── setup.ts
        ├── apiClient.test.ts
        ├── contracts.test.tsx
        └── components.test.tsx
```

---

## 4. Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Default configuration:
```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

---

## 5. Development & Build Commands
Run from the `frontend/` directory:

- **Install dependencies:**
  ```bash
  npm install
  ```
- **Start development server:**
  ```bash
  npm run dev
  ```
- **Run tests:**
  ```bash
  npm test
  ```
- **TypeScript typecheck & production build:**
  ```bash
  npm run build
  ```

---

## 6. Backend Contract Safety Invariants
The frontend is strictly coupled to the authoritative FastAPI backend schemas and respects all ML and agent contracts:
1. **Risk Prediction:**
   - Displays continuous score on the authoritative **1.0 – 10.0 scale**.
   - Displays deterministic policy bands (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
   - Does NOT render invented 0–1 percentage meters or synthetic factors.
2. **Timeline Prediction:**
   - Displays actual point duration estimates (`predicted_duration_months`, `estimated_duration_months`).
   - Does NOT invent confidence intervals or duration brackets.
3. **Bug Prediction:**
   - Uses strict backend labels (`DEFECTIVE` and `NON_DEFECTIVE`).
   - Does NOT use deprecated or stale labels (`DEFECT_PRONE` / `NOT_DEFECT_PRONE`).
4. **Architecture Recommendation:**
   - Visualizes styles, components, candidate technologies, data flows, and trade-offs.
   - Does NOT compute or display invented architecture quality scores or rankings.
5. **Explainability Insights:**
   - Preserves exact epistemic claim types (`FACT`, `INTERPRETATION`, `RECOMMENDATION`, `LIMITATION`).
   - Displays verified source traceability without synthetic citations.

---

## 7. Current Scope vs. Intentionally Deferred Features
### Implemented in Phase 9:
- Centralized RFC 7807 API client with correlation ID propagation
- Project & Requirement Management Workspace (CRUD, soft-delete archiving, status filtering)
- Canonical Context & Snapshot Visualization (deterministic statistics, snapshot freezes)
- Dynamic Workflow Studio (discovery, configuration, synchronous execution outcome rendering)
- Modular Artifact Renderers for all 9 platform agents
- Persisted Run History inspection with execution detail modal
- Comprehensive test suite covering API client, contract safety, and user flows

### Intentionally Deferred:
- User Authentication & Role-Based Access Control (RBAC)
- Server-Sent Events (SSE) & WebSocket real-time progress streaming
- Asynchronous Celery/Redis background task polling
- Sandbox code execution environments
- Direct Git/GitHub automated PR creation
- Dynamic arbitrary agent DAG designer
