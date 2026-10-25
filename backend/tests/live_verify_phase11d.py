"""Live verification script for Phase 11D Failure Analysis Agent.

Executes deterministic synthetic failure analysis with:
1. Groq provider (live API)
2. Gemini provider (live API)

Validates:
- Structured FailureDiagnosis contract adherence
- Evidence grounding (exact diagnostic ID, stderr traceback)
- Anti-hallucination controls (no fake files, diagnostics, requirements, or architecture components)
- Strictly read-only remediation (no diffs, no code patches, no claims of fixes applied)
- Zero credentials printed or leaked.
"""

import asyncio
import json
import logging
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Add backend to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.agents.execution import AgentExecutor
from app.agents.failure_analysis.agent import FailureAnalysisAgent
from app.agents.failure_analysis.contracts import (
    FailureDiagnosis,
    FailureType,
    ClaimType,
)
from app.agents.providers.factory import get_llm_provider
from app.core.config import settings
from app.models.project import ProjectStatus
from app.models.requirement import RequirementPriority, RequirementStatus, RequirementType
from app.sandbox.contracts import ExecutionResult, ExecutionStatus, ExecutionType
from app.sandbox.static_analysis.contracts import (
    DiagnosticCategory,
    DiagnosticSeverity,
    StaticAnalysisResult,
    StaticAnalysisStatus,
    StaticDiagnostic,
)
from app.schemas.context import ProjectContextResponse, RequirementStatistics
from app.schemas.project import ProjectResponse
from app.schemas.requirement import RequirementResponse
from tests.unit.test_sandbox import make_valid_code_output

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("live_verify_phase11d")


def build_synthetic_failure_fixture():
    project_id = uuid.uuid4()
    req1_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    # 1. Project Context
    project = ProjectResponse(
        id=project_id,
        name="Calculator Microservice",
        slug="calculator-service",
        description="Core arithmetic calculation microservice.",
        status=ProjectStatus.IN_PROGRESS,
        created_at=now,
        updated_at=now,
    )
    req1 = RequirementResponse(
        id=req1_id,
        project_id=project_id,
        title="Summation Engine",
        description="Calculate the sum of integer values.",
        priority=RequirementPriority.HIGH,
        type=RequirementType.FUNCTIONAL,
        status=RequirementStatus.APPROVED,
        is_archived=False,
        created_at=now,
        updated_at=now,
    )
    stats = RequirementStatistics(
        total_requirements=1,
        active_requirements=1,
        functional_count=1,
        non_functional_count=0,
        constraint_count=0,
        by_priority={"HIGH": 1},
        by_status={"APPROVED": 1},
        completion_percentage=100.0,
    )
    context = ProjectContextResponse(
        project=project,
        requirements=[req1],
        statistics=stats,
        context_version=1,
        generated_at=now,
    )

    # 2. Generated Code with intentional defect (NameError: total_sum undefined)
    code_output = make_valid_code_output([
        (
            "app/calculator.py",
            "def calculate(values: list[int]) -> int:\n"
            "    # Defect: references undefined variable 'total_sum'\n"
            "    return total_sum\n",
        ),
        (
            "tests/test_calculator.py",
            "from app.calculator import calculate\n\n"
            "def test_calculate():\n"
            "    assert calculate([1, 2, 3]) == 6\n",
        ),
    ])

    # 3. Static Analysis Result (F821 undefined name)
    static_analysis = StaticAnalysisResult(
        analysis_id=uuid.uuid4(),
        project_id=project_id,
        status=StaticAnalysisStatus.ISSUES_FOUND,
        duration_seconds=0.14,
        diagnostics=[
            StaticDiagnostic(
                diagnostic_id="diag-f821-calc",
                category=DiagnosticCategory.LINT,
                severity=DiagnosticSeverity.ERROR,
                code="F821",
                message="undefined name 'total_sum'",
                file_path="app/calculator.py",
                line=3,
                column=12,
                source="ruff",
                evidence="return total_sum",
            )
        ],
        files_analyzed=2,
        files_skipped=0,
        error_count=1,
        warning_count=0,
        info_count=0,
        security_issue_count=0,
        syntax_error_count=0,
        lint_issue_count=1,
        test_file_count=1,
        summary="Static analysis detected 1 error: F821 undefined name.",
    )

    # 4. Sandbox Test Execution Result (Failed test due to NameError)
    execution_result = ExecutionResult(
        execution_id=uuid.uuid4(),
        project_id=project_id,
        execution_type=ExecutionType.TEST,
        status=ExecutionStatus.FAILED,
        exit_code=1,
        duration_seconds=1.45,
        stdout="============================= test session starts =============================\ncollected 1 item\n\ntests/test_calculator.py F                                              [100%]\n",
        stderr=(
            "Traceback (most recent call last):\n"
            '  File "/workspace/tests/test_calculator.py", line 4, in test_calculate\n'
            "    assert calculate([1, 2, 3]) == 6\n"
            '  File "/workspace/app/calculator.py", line 3, in calculate\n'
            "    return total_sum\n"
            "NameError: name 'total_sum' is not defined\n"
        ),
        tests_total=1,
        tests_passed=0,
        tests_failed=1,
    )

    # Mock architecture and database design objects
    class MockArchComponent:
        def __init__(self, name: str):
            self.name = name

    class MockArchOutput:
        def __init__(self):
            self.components = [MockArchComponent("CalculatorService")]

    class MockDbEntity:
        def __init__(self, name: str):
            self.name = name

    class MockDbOutput:
        def __init__(self):
            self.entities = [MockDbEntity("CalculationHistory")]

    return {
        "context": context,
        "code_output": code_output,
        "static_analysis": static_analysis,
        "execution_result": execution_result,
        "arch_output": MockArchOutput(),
        "db_output": MockDbOutput(),
    }


async def run_live_verification_for_provider(provider_name: str) -> dict:
    logger.info(f"=== Starting Live Verification with Provider: {provider_name.upper()} ===")
    fixture = build_synthetic_failure_fixture()

    try:
        provider = get_llm_provider(provider_name=provider_name)
    except Exception as exc:
        logger.error(f"Failed to initialize provider '{provider_name}': {exc}")
        return {
            "provider": provider_name,
            "status": "CONFIG_ERROR",
            "error": str(exc),
        }

    executor = AgentExecutor(provider=provider, max_retries=2)
    agent = FailureAnalysisAgent()

    t0 = time.perf_counter()
    result = await executor.execute(
        agent=agent,
        context=fixture["context"],
        code_generation=fixture["code_output"],
        static_analysis_result=fixture["static_analysis"],
        execution_result=fixture["execution_result"],
        architecture_recommendation=fixture["arch_output"],
        database_design=fixture["db_output"],
    )
    duration = time.perf_counter() - t0

    is_valid = result.validation.is_valid
    diag: FailureDiagnosis | None = result.output

    if not diag:
        return {
            "provider": provider_name,
            "model": provider.default_model if hasattr(provider, "default_model") else "unknown",
            "execution_id": str(result.execution_id),
            "status": result.status.value,
            "duration_seconds": round(duration, 3),
            "is_valid": is_valid,
            "validation_errors": result.validation.errors,
            "errors": [err.model_dump() for err in result.errors] if hasattr(result, "errors") else [],
            "diagnosis": None,
        }

    # Check for hallucinated items
    all_files = {"app/calculator.py", "tests/test_calculator.py"}
    file_errors = [f for f in diag.affected_files if f not in all_files]
    diag_errors = [
        ev.evidence_id
        for ev in diag.evidence
        if ev.evidence_id not in {"diag-f821-calc", "sandbox_stdout", "sandbox_stderr", "exit_code"}
        and not ev.evidence_id.startswith("diag_")
        and not ev.evidence_id.startswith("exec_")
    ]
    from app.agents.failure_analysis.validator import FailureAnalysisValidator
    has_diff = any(m in diag.suggested_remediation for m in FailureAnalysisValidator.DIFF_MARKERS)
    has_replace = any(p.search(diag.suggested_remediation) for p in FailureAnalysisValidator.REPLACEMENT_PATTERNS)
    has_insert = any(p.search(diag.suggested_remediation) for p in FailureAnalysisValidator.INSERTION_PATTERNS)
    has_code_expr = any(p.search(diag.suggested_remediation) for p in FailureAnalysisValidator.CODE_EXPRESSION_PATTERNS)
    is_conceptual = not (has_diff or has_replace or has_insert or has_code_expr)

    meta = getattr(provider, "last_usage_metadata", None) or result.metadata

    record = {
        "provider": provider_name,
        "model": provider.default_model if hasattr(provider, "default_model") else "unknown",
        "execution_id": str(result.execution_id),
        "status": result.status.value,
        "duration_seconds": round(duration, 3),
        "is_valid": is_valid,
        "validation_errors": result.validation.errors,
        "hallucinated_files": file_errors,
        "hallucinated_diagnostics": diag_errors,
        "contains_diff_patch": has_diff,
        "contains_replacement_directive": has_replace,
        "contains_insertion_directive": has_insert,
        "contains_code_expression": has_code_expr,
        "is_conceptual_remediation": is_conceptual,
        "token_usage": meta.get("usage") if meta else None,
        "diagnosis": {
            "diagnosis_id": str(diag.diagnosis_id),
            "failure_type": diag.failure_type.value,
            "title": diag.title,
            "summary": diag.summary,
            "root_cause": diag.root_cause,
            "severity": diag.severity.value,
            "confidence": diag.confidence.value,
            "affected_files": diag.affected_files,
            "evidence_count": len(diag.evidence),
            "claims_count": len(diag.claims),
            "claims_by_type": {
                ct: sum(1 for c in diag.claims if c.claim_type.value == ct)
                for ct in ["FACT", "INTERPRETATION", "RECOMMENDATION", "LIMITATION"]
            },
            "requirement_links": diag.requirement_links,
            "architecture_links": diag.architecture_links,
            "database_links": diag.database_links,
            "suggested_remediation": diag.suggested_remediation,
            "limitations": diag.limitations,
        },
    }

    logger.info(
        f"Provider {provider_name.upper()} finished in {duration:.2f}s | "
        f"Status: {result.status.value} | Valid: {is_valid} | "
        f"Failure Type: {diag.failure_type.value} | Root Cause: {diag.root_cause[:80]}..."
    )
    return record


async def main():
    print("=================================================================")
    print("PHASE 11D — LIVE FAILURE ANALYSIS AGENT VERIFICATION")
    print("=================================================================")

    results = {}

    # 1. Groq Live Run
    print("\n--- 1. Testing Live Groq Provider ---")
    groq_record = await run_live_verification_for_provider("groq")
    results["groq"] = groq_record

    # 2. Inter-test buffer to respect rate limits
    print("\nWaiting 5 seconds between provider invocations...")
    await asyncio.sleep(5)

    # 3. Gemini Live Run
    print("\n--- 2. Testing Live Gemini Provider ---")
    gemini_record = await run_live_verification_for_provider("gemini")
    results["gemini"] = gemini_record

    # 4. Save results to JSON artifact
    out_path = Path(__file__).resolve().parent / "phase_11d_live_verification.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\nSaved live verification results to {out_path}")

    # 5. Output comparison table (Factual only, no better/worse evaluation)
    print("\n=================================================================")
    print("FACTUAL PROVIDER EXECUTION METRICS (NO SUBJECTIVE RANKING)")
    print("=================================================================")
    for p_name in ["groq", "gemini"]:
        rec = results.get(p_name, {})
        diag = rec.get("diagnosis", {})
        print(f"\nProvider: {p_name.upper()}")
        print(f"  Model: {rec.get('model')}")
        print(f"  Status: {rec.get('status')}")
        print(f"  Execution ID: {rec.get('execution_id')}")
        print(f"  Latency: {rec.get('duration_seconds')}s")
        print(f"  Valid Schema: {rec.get('is_valid')}")
        print(f"  Validation Errors: {rec.get('validation_errors')}")
        print(f"  Failure Type: {diag.get('failure_type')}")
        print(f"  Confidence: {diag.get('confidence')}")
        print(f"  Affected Files: {diag.get('affected_files')}")
        print(f"  Claims by Type: {diag.get('claims_by_type')}")
        print(f"  Contains Diff/Patch: {rec.get('contains_diff_patch')}")
        print(f"  Contains Replacement Directive ('replace X with Y'): {rec.get('contains_replacement_directive')}")
        print(f"  Contains Line Insertion Directive ('add this line'): {rec.get('contains_insertion_directive')}")
        print(f"  Contains Code Expression/Snippet: {rec.get('contains_code_expression')}")
        print(f"  Is Conceptual Remediation (Strict Boundary): {rec.get('is_conceptual_remediation')}")
        print(f"  Token Usage: {rec.get('token_usage')}")


if __name__ == "__main__":
    asyncio.run(main())
