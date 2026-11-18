# AI Code Review Agent Architecture Specification

## 1. Purpose
The `CodeReviewAgent` is the code inspection and quality analysis intelligence agent in SE IntelliPlatform (`AgentType.REVIEW`, version `1.0.0`, id `code-review`). It ingests in-memory source code files (`CodeReviewInput`) along with canonical project context (`ProjectContextResponse`), performs deterministic lexical credential scanning and standard-library Python AST analysis, and utilizes an `LLMProvider` for contextual explanation, semantic bug detection, and requirement alignment review.

> **CRITICAL SECURITY & EXECUTION POLICY:**  
> Phase 8.1 strictly does NOT execute reviewed source code or dynamic suggestions. No `compile()`, `exec()`, `eval()`, `subprocess`, dynamic import, shell command, or application execution is permitted. The agent operates strictly on in-memory syntax trees and text representations.

---

## 2. Agent Identity & Metadata
- **Agent ID:** `code-review`
- **Agent Name:** `AI Code Review Agent`
- **Agent Type:** `AgentType.REVIEW`
- **Version:** `1.0.0`
- **Output Schema:** `CodeReviewOutput`

---

## 3. Input Model & Boundaries
- **Representation:** In-memory `CodeReviewInput` containing a bounded list of `CodeFile` objects passed via execution `kwargs`.
- **Review Limits:**
  - Maximum files: 10 files
  - Maximum cumulative size: 100 KB
  - Maximum lines per file: 1,000 lines
- **Path Security:** Strict prohibition of path traversal (`..`), absolute filesystem paths (`/`, `\\`), Windows drive letters (`C:`), and UNC paths.
- **Language Scope:** Phase 8.1 primary deterministic support is Python (`python`, `py`).

---

## 4. Execution Lifecycle & Pipeline

```text
               ProjectContextResponse + CodeReviewInput
                                 │
                                 ▼
                   ┌───────────────────────────┐
                   │    Hook 2: analyze()      │
                   │  - Input boundary check   │
                   │  - Mandatory Secret Scan  │
                   │  - Redact secrets in mem  │
                   │  - Deterministic AST parse│
                   │  - Filter active reqs     │
                   └─────────────┬─────────────┘
                                 │
                                 ▼
                   ┌───────────────────────────┐
                   │    Hook 3: generate()     │
                   │  - Construct prompt       │
                   │  - LLM generate candidate │
                   │  - Merge static + AI      │
                   │  - Assign provenance      │
                   │  - Calculate summary stats│
                   └─────────────┬─────────────┘
                                 │
                                 ▼
                   ┌───────────────────────────┐
                   │ Hook 4: validate_output() │
                   │  - Line bounds 1..N       │
                   │  - Verbatim evidence check│
                   │  - Finding deduplication  │
                   │  - Metrics verification   │
                   └─────────────┬─────────────┘
                                 │
                                 ▼
                         CodeReviewOutput
```

---

## 5. Mandatory Secret Scanning & Redaction
Before any code content enters an LLM prompt:
1. `SecretScanner` scans content with compiled regex patterns (AWS keys, private key headers, bearer tokens, API keys, passwords, connection strings).
2. For each detected secret, a deterministic `CRITICAL` `SECURITY` finding is recorded with provenance `STATIC_ANALYSIS` and `rule_id="SECRET-DETECTION"`.
3. Secret values are replaced with `***REDACTED_SECRET***` in prompt payloads.
4. Raw secrets are NEVER included in finding evidence, output descriptions, or audit records.

---

## 6. Deterministic AST Analysis
- Standard library `ast.parse()` extracts syntax trees without compilation or execution.
- Captures `SyntaxError` deterministically as a `CRITICAL` `CORRECTNESS` finding.
- Performs focused AST pattern checks:
  - `AST-EVAL`: Dynamic code evaluation via `eval()` (`SECURITY`, `HIGH`)
  - `AST-EXEC`: Dynamic code execution via `exec()` (`SECURITY`, `HIGH`)
  - `AST-OS-SYSTEM`: Shell invocation via `os.system()` (`SECURITY`, `HIGH`)
  - `AST-SUBPROCESS-SHELL`: Subprocess calls with `shell=True` (`SECURITY`, `HIGH`)
  - `AST-EMPTY-EXCEPT`: Swallowed exceptions / empty handlers (`ERROR_HANDLING`, `MEDIUM`)
  - `AST-EXCESSIVE-NESTING`: Control flow depth $\ge 5$ (`MAINTAINABILITY`, `LOW`)
  - `AST-MISSING-DOCSTRING`: Top-level module docstrings on substantial files (`READABILITY`, `INFO`)

---

## 7. AI / LLM Responsibilities & Provenance
- The LLM receives redacted code, pre-computed static findings, and active project requirements.
- The LLM produces `CodeReviewCandidate` with semantic explanations, edge cases, and requirement-aligned refactoring suggestions.
- Provenance tracking:
  - `STATIC_ANALYSIS`: Deterministic scanner or AST rule.
  - `AI_REVIEW`: Probabilistic LLM observation.
  - `HYBRID`: AI explanation enriching a deterministic static finding.
- The backend normalizes finding IDs sequentially (`CR-001`, `CR-002`, ...).

---

## 8. Deterministic Validation Invariants
The backend `validate_code_review_output()` enforces:
1. **Summary & File Non-Emptiness:** `summary` and `files_reviewed` must be populated.
2. **File Authority:** Findings may only reference files in `files_reviewed`.
3. **Line Bounds:** $1 \le \text{line\_start} \le \text{line\_end} \le \text{total\_file\_lines}$.
4. **Verbatim Evidence Verification:** The `evidence` text must actually appear in lines `[line_start:line_end]` of the reviewed source file.
5. **Deduplication:** Dropping duplicate findings sharing identical line slices and rules.
6. **Mathematical Metric Consistency:** Authoritative counts for total, static, AI, severity, and category metrics.
7. **Scope Limitations:** Preserving $\ge 3$ comprehensive platform review limitations.

---

## 9. Audit & Privacy
Every execution dispatched through `AgentExecutor` generates an immutable `AgentExecutionAudit` record:
- Records `execution_id`, `project_id`, `agent_id="code-review"`, `agent_version="1.0.0"`, `status`, duration, and provenance.
- Privacy Invariant: Raw source code, detected secrets, and credentials are NEVER persisted in audit records or database tables.
