# SE INTELLIPLATFORM — NORMAL VERSION RESTORATION PLAN
**Target:** Clean 2D Architecture Restoration & 3D De-coupling  
**Project:** SE IntelliPlatform (`C:\Users\DELL\OneDrive\Documents\SE Intellplatform`)  
**Status:** PROPOSED PLAN (Awaiting Approval Before Execution)

---

## 1. PURPOSE & PRINCIPLES

The goal of this operation is to restore the original SE IntelliPlatform repository to its clean, robust 2D user interface and architecture, eliminating all 3D libraries, canvases, and WebGL dependencies, while **100% preserving**:
1. All 9 AI agents and their orchestration pipelines.
2. The complete React frontend architecture and custom history routing.
3. All original 2D workspaces and tools (Overview, Requirements/Spec, Code Studio Monaco Editor, Testing, Workflow Studio, Code Intelligence Adjacency, Issues, Intelligence, Preview).
4. All non-3D Phase 6D production hardening improvements (rate limiting, secret validation, project authorization, async workflow execution, migration runner).
5. The independent 3D edition repository at `C:\Users\DELL\OneDrive\Documents\SE-IntelliPlatform-3D` (completely untouched and isolated).

---

## 2. PRE-RESTORATION BACKUP & SAFETY GUARANTEE

Before any modification or file deletion occurs:
1. An uncommitted snapshot backup will be created in `backup/phase6d_snapshot/` or `scratch/backup_phase6d.zip` containing all working-tree edits and untracked 3D files.
2. Verification that the sibling folder `C:\Users\DELL\OneDrive\Documents\SE-IntelliPlatform-3D` is unaffected.

---

## 3. STEP-BY-STEP RESTORATION WORKFLOW

### STEP 1: Dependencies Cleanup (`frontend/package.json`)
- Remove 3D libraries:
  - `three`
  - `@react-three/fiber`
  - `@react-three/drei`
  - `@types/three`
  - `@gsap/react`
  - `gsap`
  - `framer-motion`
- Retain all core dependencies:
  - `react`, `react-dom`, `@tanstack/react-query`, `lucide-react`.
- Reinstall dependencies cleanly (`npm install`) to update `package-lock.json` and remove orphaned node_modules.

### STEP 2: Bundler Optimization Reversion (`frontend/vite.config.ts`)
- Revert the `manualChunks` in `vite.config.ts` to standard React vendor chunks, removing:
  - `vendor-three`
  - `vendor-gsap`
  - `vendor-motion`

### STEP 3: Workspace Views Reversion (2D Restoration)
1. **`AppShell.tsx`**:
   - Remove `LazyGlobalCanvas` and `SceneFallback`.
   - Remove background canvas container element.
2. **`OverviewWorkspace.tsx`**:
   - Remove `LazyProjectTopologyViewer` import and state toggle.
   - Retain 2D project cards, project summary metrics, recent runs, and `safeContext` race-protection logic.
3. **`SpecificationWorkspace.tsx`**:
   - Remove `LazyArchitectureBlueprint3DViewer` import and 3D toggle buttons.
   - Ensure original 2D `ArchitectureTopologyView` and `ErdPreview` are the active visualizers.
4. **`CodeStudioWorkspace.tsx`**:
   - Remove 3D topology helix toggle and `LazyCodeTopologyViewer`.
   - Restore standard full-screen Monaco 2D `CodeEditor` workspace.
5. **`TestingWorkspace.tsx`**:
   - Remove `3d-intelligence` navigation sub-tab and `LazyTestingIntelligenceViewer`.
   - Retain all 2D testing tabs (overview, unit, integration, e2e, coverage, intelligence metrics).
6. **`WorkflowStudio.tsx`**:
   - Remove `LazyWorkflowDag3DViewer`.
   - Restore original 2D `WorkflowDagView` for graphical workflow inspection.
7. **`CodeIntelligenceWorkspace.tsx`**:
   - Remove 3D Cosmos toggle and `LazyCodeTopologyViewer`.
   - Retain 2D dependency graph / adjacency matrix, file symbols, and module metrics.

### STEP 4: Styling Cleanup (`frontend/src/styles/components.css`)
- Remove Section 11 (`.viewer-3d-*` classes).
- Ensure all 2D layout and card CSS remains intact.

### STEP 5: Deletion of Untracked 3D Files
- Safely remove directory: `frontend/src/components/3d/` (8 subdirectories, ~25 files).
- Safely remove the 7 untracked 3D test files:
  - `frontend/src/test/ambient3DEnvironment.test.tsx`
  - `frontend/src/test/architectureBlueprintTopology.test.tsx`
  - `frontend/src/test/codeIntelligence3dExplorer.test.tsx`
  - `frontend/src/test/codeTopology.test.tsx`
  - `frontend/src/test/projectTopology.test.tsx`
  - `frontend/src/test/testingTopology.test.tsx`
  - `frontend/src/test/workflowDagTopology.test.tsx`

### STEP 6: Restore Baseline Missing Views
- Restore `frontend/src/views/ProjectWorkspace.tsx` and `frontend/src/views/RequirementsWorkspace.tsx` from `origin/main` to guarantee no accidental file loss.

### STEP 7: Backend Confirmation
- Confirm all 9 AI agents are present in `backend/app/agents/`.
- Confirm Phase 6D hardening (rate limiting, secret key validation, project ownership authorization, async workflow endpoints, and `scripts/migrate.py`) are fully intact.

---

## 4. VERIFICATION & QUALITY GATES

1. **TypeScript Typecheck:**
   - Execute `cd frontend; npx tsc --noEmit`
   - Expect: 0 errors.
2. **Frontend Production Build:**
   - Execute `cd frontend; npm run build`
   - Expect: Successful bundle generation with clean 2D chunks and no three/gsap references.
3. **Frontend Test Suite Execution:**
   - Execute `cd frontend; npm test -- --run`
   - Expect: 35 passing test suites (0 failures).
4. **Backend Test Suite Execution:**
   - Execute `pytest backend/tests/`
   - Expect: All 27 unit tests pass (0 failures).
5. **Final Sign-off Report:**
   - Generate `docs/normal-restoration/NORMAL_PROJECT_RESTORATION_REPORT.md`.
