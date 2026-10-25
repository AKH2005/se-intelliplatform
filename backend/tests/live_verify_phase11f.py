"""Live Verification Script for Phase 11F: AI Test Generation Agent & Ephemeral Docker Execution.

Executes live generation with:
1. Groq provider (live API)
2. Gemini provider (live API)

Validates:
- Structured AITestSuiteCandidate contract adherence
- Deterministic AST safety & quality validation (no forbidden imports, no dangerous calls)
- Anti-hallucination controls (modifies ONLY supplied files, uses ONLY supplied requirement IDs)
- Code size bounds & secret scanning
- Meaningful assertions ('assert' or 'pytest.raises')
- Ephemeral Docker execution (original code artifact is NOT mutated, tests execute inside container)
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

from app.agents.code_generation.contracts import (
    CodeGenerationOutput,
    CodeGenerationPlan,
    GeneratedFile,
    PlannedFile,
)
from app.agents.execution import AgentExecutor
from app.agents.providers.factory import get_llm_provider
from app.agents.test_generation.agent import TestGenerationAgent
from app.agents.test_generation.contracts import (
    AITestSuite,
    AITestSuiteCandidate,
    TestCategory,
    TestGenerationInput,
)
from app.agents.test_generation.validator import AITestValidator
from app.core.config import settings
from app.models.project import ProjectStatus
from app.models.requirement import RequirementPriority, RequirementStatus, RequirementType
from app.sandbox.contracts import ExecutionRequest, ExecutionStatus, ExecutionType, ResourceLimits
from app.sandbox.docker_executor import DockerSandboxExecutor
from app.schemas.context import ProjectContextResponse, RequirementStatistics
from app.schemas.project import ProjectResponse
from app.schemas.requirement import RequirementResponse

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("live_verify_phase11f")


def build_synthetic_project_fixture():
    project_id = uuid.uuid4()
    req1_id = uuid.uuid4()
    req2_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

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
        description="Calculate the sum of two integers.",
        priority=RequirementPriority.HIGH,
        type=RequirementType.FUNCTIONAL,
        status=RequirementStatus.APPROVED,
        is_archived=False,
        created_at=now,
        updated_at=now,
    )
    req2 = RequirementResponse(
        id=req2_id,
        project_id=project_id,
        title="Division Engine",
        description="Calculate the quotient of two numbers and raise ValueError on zero division.",
        priority=RequirementPriority.HIGH,
        type=RequirementType.FUNCTIONAL,
        status=RequirementStatus.APPROVED,
        is_archived=False,
        created_at=now,
        updated_at=now,
    )

    requirements = [req1, req2]
    stats = RequirementStatistics(
        total_requirements=2,
        active_requirements=2,
        functional_count=2,
        non_functional_count=0,
        constraint_count=0,
        by_priority={"HIGH": 2},
        by_status={"APPROVED": 2},
        completion_percentage=100.0,
    )
    context = ProjectContextResponse(
        project=project,
        requirements=requirements,
        statistics=stats,
        context_version=1,
        generated_at=now,
    )

    calc_content = (
        "def add(a: int, b: int) -> int:\n"
        "    return a + b\n\n"
        "def divide(a: float, b: float) -> float:\n"
        "    if b == 0:\n"
        "        raise ValueError('Cannot divide by zero')\n"
        "    return a / b\n"
    )

    code_output = CodeGenerationOutput(
        plan=CodeGenerationPlan(
            project_type="backend-service",
            language="python",
            framework="fastapi",
            database="sqlite",
            package_manager="pip",
            files=[
                PlannedFile(
                    path="app/calculator.py",
                    purpose="Calculator functions",
                    file_type="SOURCE",
                    requirement_ids=[str(req1_id), str(req2_id)],
                    dependencies=[],
                )
            ],
            rationale="Calculation service",
        ),
        generated_files=[
            GeneratedFile(
                path="app/calculator.py",
                content=calc_content,
                language="python",
                size_bytes=len(calc_content.encode("utf-8")),
                requirement_ids=[str(req1_id), str(req2_id)],
            )
        ],
        total_files=1,
        total_size_bytes=len(calc_content.encode("utf-8")),
        summary="Verified calculator module",
    )

    return {
        "context": context,
        "code_output": code_output,
        "req1_id": str(req1_id),
        "req2_id": str(req2_id),
    }


async def test_live_provider(provider_name: str, fixture_data: dict) -> dict:
    logger.info(f"--- Running Live Test Generation with [{provider_name.upper()}] ---")

    provider = get_llm_provider(provider_name=provider_name)
    executor = AgentExecutor(provider=provider, max_retries=1)
    agent = TestGenerationAgent()

    context = fixture_data["context"]
    code_output = fixture_data["code_output"]
    req_ids = [fixture_data["req1_id"], fixture_data["req2_id"]]

    files_map = {f.path: f.content for f in code_output.generated_files}
    manifest = list(files_map.keys())

    test_input = TestGenerationInput(
        project_id=context.project.id,
        manifest=manifest,
        files=files_map,
        available_requirement_ids=req_ids,
        available_architecture_components=["CalculatorComponent"],
        allowed_categories=list(TestCategory),
    )

    start_time = time.monotonic()
    result = await executor.execute(
        agent=agent,
        context=context,
        test_input=test_input,
    )
    elapsed = round(time.monotonic() - start_time, 2)

    logger.info(f"[{provider_name.upper()}] Status: {result.status.value}, Elapsed: {elapsed}s")

    if result.status.value != "COMPLETED" or not result.output:
        logger.error(f"[{provider_name.upper()}] Execution Failed: {result.error}")
        return {
            "provider": provider_name,
            "status": "FAILED",
            "elapsed_seconds": elapsed,
            "error": result.error.message if result.error else "Unknown error",
        }

    candidate: AITestSuiteCandidate = result.output
    val_res = AITestValidator.validate(candidate, test_input)
    logger.info(f"[{provider_name.upper()}] Deterministic Validation: is_valid={val_res.is_valid}, errors={val_res.errors}")

    suite: AITestSuite = AITestValidator.compile_candidate_to_suite(candidate, test_input, result.metadata)

    logger.info(f"[{provider_name.upper()}] Compiled Suite: {suite.test_count} tests generated.")
    for t in suite.tests:
        logger.info(f"  - [{t.test_id}] {t.name} ({t.category.value}) -> {t.target_file}")

    return {
        "provider": provider_name,
        "model": provider.default_model,
        "status": result.status.value,
        "elapsed_seconds": elapsed,
        "is_valid": val_res.is_valid,
        "validation_errors": val_res.errors,
        "test_count": suite.test_count,
        "tests": [
            {
                "test_id": t.test_id,
                "name": t.name,
                "category": t.category.value,
                "target_file": t.target_file,
                "target_symbol": t.target_symbol,
                "requirement_ids": t.requirement_ids,
                "code": t.code,
            }
            for t in suite.tests
        ],
        "compiled_test_file": suite.test_files.get("tests/test_ai_generated.py", ""),
        "metadata": result.metadata,
    }


async def test_ephemeral_docker_execution(fixture_data: dict, test_suite_data: dict) -> dict:
    """Execute the compiled AI test suite inside the real Docker sandbox."""
    logger.info("--- Testing Ephemeral Execution inside Docker Sandbox ---")
    docker_executor = DockerSandboxExecutor()

    is_ready = await docker_executor.is_available()
    if not is_ready:
        logger.warning("Docker daemon is not reachable in current environment. Skipping live container run.")
        return {"status": "SKIPPED", "reason": "Docker daemon unavailable"}

    original = fixture_data["code_output"]
    original_files_count = len(original.generated_files)

    # Build ephemeral files: original files + tests/test_ai_generated.py
    combined_files = list(original.generated_files)
    test_content = test_suite_data.get("compiled_test_file", "")
    combined_files.append(
        GeneratedFile(
            path="tests/test_ai_generated.py",
            content=test_content,
            language="python",
            size_bytes=len(test_content.encode("utf-8")),
            requirement_ids=[],
        )
    )

    ephemeral_artifact = CodeGenerationOutput(
        plan=original.plan,
        generated_files=combined_files,
        total_files=len(combined_files),
        total_size_bytes=sum(f.size_bytes for f in combined_files),
        summary="Ephemeral live verification artifact",
    )

    req = ExecutionRequest(
        project_id=fixture_data["context"].project.id,
        execution_type=ExecutionType.TEST,
        test_target="tests/test_ai_generated.py",
        limits=ResourceLimits(timeout_seconds=25),
    )

    start_time = time.monotonic()
    exec_result = await docker_executor.execute(req, ephemeral_artifact)
    elapsed = round(time.monotonic() - start_time, 2)

    logger.info(f"Docker Execution Status: {exec_result.status.value}")
    logger.info(f"Tests Passed: {exec_result.tests_passed}/{exec_result.tests_total}")
    logger.info(f"Exit Code: {exec_result.exit_code}")
    logger.info(f"Duration: {elapsed}s")

    # Invariant check: original artifact was not modified
    assert len(original.generated_files) == original_files_count
    assert "tests/test_ai_generated.py" not in [f.path for f in original.generated_files]
    logger.info("Original artifact immutability verified (unchanged).")

    return {
        "status": exec_result.status.value,
        "exit_code": exec_result.exit_code,
        "duration_seconds": elapsed,
        "tests_total": exec_result.tests_total,
        "tests_passed": exec_result.tests_passed,
        "tests_failed": exec_result.tests_failed,
        "stdout": exec_result.stdout,
        "stderr": exec_result.stderr,
        "original_artifact_preserved": True,
    }


async def main():
    logger.info("Initializing Phase 11F Live AI Test Generation Verification...")
    fixture_data = build_synthetic_project_fixture()

    groq_res = await test_live_provider("groq", fixture_data)
    gemini_res = await test_live_provider("gemini", fixture_data)

    # Use valid suite for Docker execution
    active_suite_data = groq_res if groq_res.get("is_valid") else gemini_res
    docker_res = await test_ephemeral_docker_execution(fixture_data, active_suite_data)

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "groq": groq_res,
        "gemini": gemini_res,
        "docker_execution": docker_res,
    }

    scratch_path = Path("C:/Users/DELL/.gemini/antigravity-ide/brain/c2a62727-cf3a-49c9-9128-524cdfe35d95/scratch/phase_11f_live_verification.json")
    scratch_path.parent.mkdir(parents=True, exist_ok=True)
    with open(scratch_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    tests_json = backend_dir / "tests" / "phase_11f_live_verification.json"
    with open(tests_json, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Verification report saved to {scratch_path} and {tests_json}")
    print("\n=== PHASE 11F LIVE VERIFICATION SUMMARY ===")
    print(f"Groq Status: {groq_res.get('status')} | Valid: {groq_res.get('is_valid')} | Tests: {groq_res.get('test_count')}")
    print(f"Gemini Status: {gemini_res.get('status')} | Valid: {gemini_res.get('is_valid')} | Tests: {gemini_res.get('test_count')}")
    print(f"Docker Status: {docker_res.get('status')} | Passed: {docker_res.get('tests_passed')}/{docker_res.get('tests_total')} | Immutability: {docker_res.get('original_artifact_preserved')}")


if __name__ == "__main__":
    asyncio.run(main())
