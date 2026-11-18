# SE IntelliPlatform — Capstone Demonstration Guide
**Evaluator & Grading Committee Step-by-Step Interactive Walkthrough Script**

---

## 1. Demonstration Overview & Timing

This script provides an interactive, chronological walkthrough designed for academic evaluators, grading committee members, and peer reviewers. It systematically demonstrates the complete feature spectrum of SE IntelliPlatform across **User Mode**, **Developer Mode**, **9 Autonomous AI Agents**, and **7 Hardware-Accelerated 3D Workspaces**.

- **Estimated Total Demonstration Time**: 15–20 minutes.
- **Pre-requisites**: Frontend running on [http://127.0.0.1:5173](http://127.0.0.1:5173), Backend running on [http://127.0.0.1:8000](http://127.0.0.1:8000).

---

## 2. Interactive Walkthrough Script

### Act 1: Authentication & Brand Experience (2 Minutes)
1. **Navigate to Platform**: Open [http://127.0.0.1:5173](http://127.0.0.1:5173).
2. **Observe**: The application opens directly to the **Split-Screen Brand Showcase**.
   - Left side: Architectural highlights, 9 AI agents, and 7 3D workspaces.
   - Right side: Clean, accessible authentication form.
3. **Inspect Registration Validation**:
   - Click "Need an account? Register".
   - Type a password to observe the **Live Password Security Checklist** update in real-time.
4. **Log In**:
   - Enter email: `developer@se-intelliplatform.local`
   - Enter password: `Password123!`
   - Click **Sign In**.
5. **Mode Choice**: If prompted with the Mode Selection screen, choose **User Mode (Beginner)**.

---

### Act 2: User Mode & Autonomous App Building (4 Minutes)
1. **Welcome Dashboard**: Observe the clean, non-technical dashboard presenting 3 starting pathways:
   - *Choice 1*: Build with AI (Conversational prompt).
   - *Choice 2*: Start from a Template (EventHub, SaaS Starter, E-Commerce).
   - *Choice 3*: Start from Scratch.
2. **One-Click Template Launch**:
   - Click **Start from a Template**.
   - Select **EventHub Verification 2026**.
   - Click **Generate Project & Launch Live Preview**.
3. **Autonomous SDLC Synthesis**:
   - Watch the automated orchestration pipeline execute: Requirements $\to$ Architecture $\to$ DB $\to$ Code $\to$ Live Preview container.
4. **Inspect Live Container Preview**:
   - The application automatically renders the live interactive running application in the embedded preview container on Port `8001`.
5. **Natural Language Refinement**:
   - In the refinement input, type: *"Add a dark mode toggle button to the top header"*.
   - Click **Propose Changes**.
   - Review the generated **Unified Diff Preview**.
   - Click **Apply Refinement**.
   - Notice the preview container updates with an immutable version increment (`v2`).
   - Click **Rollback to v1** to observe zero-downtime version reversion.

---

### Act 3: Developer Mode & 3D Volumetric Tour (8 Minutes)
1. **Switch to Developer Mode**:
   - In the top navigation header, locate the **Mode Switcher** pill.
   - Click **Developer Mode**. Notice that the active project context is preserved seamlessly.
2. **Scene 1: Global Ambient Mesh**:
   - Observe the ambient particle field smoothly morphing from User Mode emerald to Developer Mode deep indigo.
3. **Scene 2: Project Topology Cosmos (`Overview Workspace`)**:
   - Navigate to **Overview** in the sidebar.
   - Click **3D Cosmos View**.
   - Orbit and zoom into the central celestial star representing the project root.
   - Hover over orbiting module spheres to view file count, lines of code, and complexity ratings.
4. **Scene 3: Architecture & ERD 3D Blueprint Cosmos (`Specifications Workspace`)**:
   - Navigate to **Specifications** in the sidebar.
   - Click the **3D Architecture Blueprint** tab.
   - Inspect the 3 tiered horizontal strata: Client Ingress, Application Services, Data & Infrastructure.
   - Click the **Project ERD Blueprint** sub-mode:
     - Observe volumetric database entity tables (`users`, `events`, `tickets`).
     - Trace the glowing cubic Bezier relationship cables representing Foreign Keys with cardinality badges (`1:N`).
   - Click **Source: Generated Project Architecture** to demonstrate strict data provenance and honest empty state fallback.
5. **Scene 4: Code Studio 3D Helix (`Code Studio Workspace`)**:
   - Navigate to **Code Studio** in the sidebar.
   - Click the **3D Code Helix** toggle above the file tree.
   - Click on any file node in the 3D double-helix; observe the Monaco Editor immediately open and highlight that file's contents.
6. **Scene 5: Testing Intelligence Cosmos (`Testing Intelligence Workspace`)**:
   - Navigate to **Testing Intelligence** in the sidebar.
   - Click the **3D Test Cosmos** view.
   - Observe the 3 concentric orbital rings: Inner (Unit), Middle (Integration), Outer (E2E).
   - Click an amber/red sphere to inspect the test outcome and stack trace.
7. **Scene 6: Workflow DAG Cosmos (`Workflow Studio Workspace`)**:
   - Navigate to **Workflow Studio** in the sidebar.
   - Click **3D DAG Explorer**.
   - Observe the 9 agent nodes arranged as a Directed Acyclic Graph with glowing dependency edges.
8. **Scene 7: Code Intelligence 3D Graph Explorer (`Code Intelligence Workspace`)**:
   - Navigate to **Code Intelligence** in the sidebar.
   - Click the **3D Cosmos** toggle.
   - Manipulate the force-directed symbol graph; select a node to reveal its caller/callee relationships in the slide-out inspector drawer.
   - Click **Open in Editor** to transition straight back to Code Studio.

---

### Act 4: Self-Healing AI Remediation Loop (3 Minutes)
1. Navigate to **Testing Intelligence**.
2. Click **Execute Regression Plan**.
3. When a simulated unit test failure is triggered:
   - Notice the status badge switch to **FAILED**.
   - Click **Analyze Failure with AI**.
   - Observe `FailureAnalysisAgent` parse the stack trace and pinpoint the root-cause AST node.
   - Click **Generate Autonomous Remediation**.
   - Inspect the unified code patch generated by `AutomatedRemediationAgent`.
   - Click **Apply Patch & Re-verify**.
   - The test suite re-runs in the background and transitions to **PASSED (Green)**.

---

### Act 5: Source Code Export & Verification (2 Minutes)
1. Return to **Overview Workspace**.
2. Click the **Download Project Code (ZIP)** button in the upper-right corner.
3. Observe the generated authenticated archive (`eventhub-verification-2026.zip`) download immediately, containing the complete, security-filtered source code bundle.
4. Conclude the demonstration by presenting the **Test & Verification Report** showing **259/259 Vitest tests passed** and **120+ Pytest tests passed**.
