import asyncio
import json
import sys
import uuid
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.sandbox.docker_executor import DockerSandboxExecutor
from app.sandbox.static_analysis.service import StaticAnalysisService
from app.sandbox.static_analysis.contracts import (
    StaticAnalysisRequest,
    StaticAnalysisStatus,
    DiagnosticCategory,
    DiagnosticSeverity,
)
from tests.unit.test_sandbox import make_valid_code_output


async def main():
    print("=== STARTING PHASE 11C LIVE VERIFICATION ===")
    project_id = uuid.uuid4()
    executor = DockerSandboxExecutor()
    service = StaticAnalysisService(executor=executor)

    # -------------------------------------------------------------
    # 1. FIXTURE WITH INTENTIONAL LINT ISSUE (unused import 'os')
    # -------------------------------------------------------------
    print("\n--- Test Case 1: Fixture with Intentional Lint Issue (Unused Import) ---")
    dirty_artifact = make_valid_code_output([
        ("app/main.py", "import os\nfrom fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get('/')\ndef root():\n    return {'status': 'ok'}\n"),
        ("requirements.txt", "fastapi>=0.100.0\npytest>=8.0.0\n"),
        ("tests/test_main.py", "from app.main import app\n\ndef test_root():\n    assert app is not None\n"),
    ])

    request = StaticAnalysisRequest(project_id=project_id)
    result_dirty = await service.analyze_artifact(
        project_id=project_id,
        artifact=dirty_artifact,
        request=request,
    )

    print(f"Status: {result_dirty.status}")
    print(f"Duration: {result_dirty.duration_seconds:.3f}s")
    print(f"Files Analyzed: {result_dirty.files_analyzed}")
    print(f"Errors: {result_dirty.error_count}, Warnings: {result_dirty.warning_count}, Info: {result_dirty.info_count}")
    print(f"Lint issues: {result_dirty.lint_issue_count}, Tests discovered: {result_dirty.test_file_count}")
    print("Diagnostics:")
    for d in result_dirty.diagnostics:
        print(f"  [{d.severity.value}] [{d.category.value}] {d.code} at {d.file_path}:{d.line} - {d.message} (source: {d.source})")

    # Assertions for dirty fixture
    assert result_dirty.status == StaticAnalysisStatus.ISSUES_FOUND
    assert result_dirty.warning_count >= 1
    assert result_dirty.lint_issue_count >= 1
    assert any(d.code == "F401" and "os" in d.message for d in result_dirty.diagnostics), "Expected F401 unused import 'os'"
    assert result_dirty.test_file_count == 1
    print(">>> Test Case 1 PASSED: Intentional lint issue deterministically detected!")

    # -------------------------------------------------------------
    # 2. CLEAN FIXTURE (Zero errors, zero warnings)
    # -------------------------------------------------------------
    print("\n--- Test Case 2: Clean Fixture (Zero Errors, Zero Warnings) ---")
    clean_artifact = make_valid_code_output([
        ("app/main.py", "from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get('/')\ndef root():\n    return {'status': 'ok'}\n"),
        ("requirements.txt", "fastapi>=0.100.0\npytest>=8.0.0\n"),
        ("tests/test_main.py", "from app.main import app\n\ndef test_root():\n    assert app is not None\n"),
    ])

    result_clean = await service.analyze_artifact(
        project_id=project_id,
        artifact=clean_artifact,
        request=request,
    )

    print(f"Status: {result_clean.status}")
    print(f"Duration: {result_clean.duration_seconds:.3f}s")
    print(f"Files Analyzed: {result_clean.files_analyzed}")
    print(f"Errors: {result_clean.error_count}, Warnings: {result_clean.warning_count}, Info: {result_clean.info_count}")
    print(f"Lint issues: {result_clean.lint_issue_count}, Tests discovered: {result_clean.test_file_count}")
    print("Diagnostics:")
    for d in result_clean.diagnostics:
        print(f"  [{d.severity.value}] [{d.category.value}] {d.code} at {d.file_path}:{d.line} - {d.message} (source: {d.source})")

    # Assertions for clean fixture
    assert result_clean.status == StaticAnalysisStatus.PASSED, f"Expected PASSED but got {result_clean.status}"
    assert result_clean.error_count == 0, f"Expected 0 errors, got {result_clean.error_count}"
    assert result_clean.warning_count == 0, f"Expected 0 warnings, got {result_clean.warning_count}"
    assert result_clean.lint_issue_count == 0, f"Expected 0 lint issues, got {result_clean.lint_issue_count}"
    assert result_clean.test_file_count == 1
    print(">>> Test Case 2 PASSED: Clean fixture produced zero errors and zero warnings!")

    # Output JSON summary
    summary_path = Path(__file__).resolve().parent / "phase_11c_live_verification.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "dirty_case": result_dirty.model_dump(mode="json"),
                "clean_case": result_clean.model_dump(mode="json"),
            },
            f,
            indent=2,
            default=str,
        )
    print(f"\nVerification summary saved to: {summary_path}")
    print("=== PHASE 11C LIVE VERIFICATION COMPLETED SUCCESSFULLY ===")


if __name__ == "__main__":
    asyncio.run(main())
