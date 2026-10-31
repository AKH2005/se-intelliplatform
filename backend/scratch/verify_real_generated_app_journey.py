"""Live End-to-End Verification: Real Generated React + FastAPI Application in Isolated Docker Runtime.

Requirements:
1. Generate a small React + FastAPI application through the existing IntelliPlatform workflow.
2. Launch that generated application using the real isolated Docker runtime.
3. Verify the frontend loads and successfully calls the generated backend API.
4. Confirm logs, health checks, and shutdown/cleanup work.
5. Run relevant regression tests.
"""

import asyncio
import json
import os
import shutil
import sys
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Ensure Windows selector event loop policy for subprocess execution
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.project import Project, ProjectStatus
from app.models.requirement import Requirement, RequirementPriority, RequirementStatus, RequirementType
from app.models.workflow_execution import WorkflowExecution, WorkflowStatus
from app.agents.registry import register_all_agents, AgentRegistry
from app.api.dependencies import get_agent_executor, agent_registry
from app.services.context_engine import ProjectContextEngine
from app.workflows.coordinator import WorkflowCoordinator
from app.services.workflow_service import WorkflowService
from app.services.development_version_service import DevelopmentVersionService
from app.schemas.workflow import WorkflowExecuteRequest
from app.runtime.application_runtime_manager import ApplicationRuntimeManager
from app.runtime.contracts import RuntimeLimits, RuntimeStatus
from app.runtime.docker_runtime_executor import DockerRuntimeExecutor
from app.schemas.runtime import ApplicationRuntimeManifest, RuntimeFramework, RuntimeLanguage
from app.browser.browser_testing_service import BrowserTestingService
from app.browser.browser_executor import BrowserExecutor
from app.browser.contracts import (
    BrowserInteractionType,
    BrowserLimits,
    DeterministicBrowserTestDefinition,
    DeterministicInteraction,
)
from app.schemas.browser_testing import BrowserTestStatus


async def run_e2e_verification() -> dict:
    results = {}
    print("=" * 80)
    print("SE INTELLIPLATORM: REAL GENERATED APP LIVE DOCKER JOURNEY VERIFICATION")
    print("=" * 80)

    # Verify Docker Availability first
    docker_executor = DockerRuntimeExecutor()
    browser_executor = BrowserExecutor()
    is_docker_ready = await docker_executor.check_docker_available()
    print(f"[*] Docker Daemon Available: {is_docker_ready}")
    if not is_docker_ready:
        raise RuntimeError("Docker daemon is not accessible.")

    is_browser_ready = await browser_executor.check_image_available()
    print(f"[*] Playwright Browser Image ({browser_executor.image}) Ready: {is_browser_ready}")
    if not is_browser_ready:
        raise RuntimeError(f"Playwright browser image {browser_executor.image} is missing.")

    register_all_agents(agent_registry)
    run_uuid = uuid.uuid4().hex[:8]

    async with AsyncSessionLocal() as session:
        # ======================================================================
        # STEP 1: Generate small React + FastAPI app through IntelliPlatform workflow
        # ======================================================================
        print("\n" + "-" * 70)
        print("STEP 1: Generate React + FastAPI Application via Workflow")
        print("-" * 70)

        project_id = uuid.uuid4()
        project = Project(
            id=project_id,
            name=f"Task Item Manager {run_uuid}",
            slug=f"task-manager-{run_uuid}",
            description="A modern full-stack task item manager with React frontend and FastAPI backend.",
            status=ProjectStatus.IN_PROGRESS,
        )
        session.add(project)

        req1 = Requirement(
            id=uuid.uuid4(),
            project_id=project_id,
            title="Interactive React Task Dashboard",
            description="Full-stack React web interface communicating with backend REST endpoints for task listing and creation.",
            type=RequirementType.FUNCTIONAL,
            priority=RequirementPriority.CRITICAL,
            status=RequirementStatus.APPROVED,
            is_archived=False,
        )
        session.add(req1)
        await session.commit()
        print(f"[+] Project created: '{project.name}' (id={project_id})")
        print(f"[+] Requirement created: '{req1.title}'")

        # Execute code-generation-workflow
        engine = ProjectContextEngine(session=session)
        executor = get_agent_executor()
        coordinator = WorkflowCoordinator(executor=executor, registry=agent_registry)
        wf_service = WorkflowService(session=session, context_engine=engine, coordinator=coordinator)

        wf_req = WorkflowExecuteRequest(project_id=project_id, options={"fail_fast": True})
        print("[*] Executing 'code-generation-workflow' through WorkflowService...")
        wf_result = await wf_service.execute_workflow("code-generation-workflow", wf_req)
        print(f"[+] Workflow Status: {wf_result.status.value}")
        for step in wf_result.step_results:
            print(f"    - Step '{step.step_id}': status={step.status.value}")

        assert wf_result.status.value in ("COMPLETED", "PARTIAL_SUCCESS"), f"Workflow failed: {wf_result.status}"
        artifacts = wf_result.artifacts or {}
        code_artifact = artifacts.get("code-generation") or artifacts.get("code_generation")
        assert code_artifact is not None, "Missing code generation artifact"

        if hasattr(code_artifact, "generated_files"):
            raw_files = code_artifact.generated_files
        elif isinstance(code_artifact, dict):
            raw_files = code_artifact.get("generated_files", [])
        else:
            raw_files = []

        generated_files = []
        for f in raw_files:
            if hasattr(f, "model_dump"):
                generated_files.append(f.model_dump())
            elif isinstance(f, dict):
                generated_files.append(f)

        print(f"[+] Generated {len(generated_files)} files in scaffold:")
        has_react_frontend = False
        has_fastapi_backend = False
        for gf in generated_files:
            p = gf.get("path", "")
            sz = gf.get("size_bytes", 0)
            lang = gf.get("language", "")
            print(f"    - {p} ({sz} bytes, {lang})")
            if "frontend" in p or "react" in p.lower():
                has_react_frontend = True
            if "backend" in p or "main.py" in p:
                has_fastapi_backend = True

        assert has_react_frontend, "Scaffold missing React frontend files"
        assert has_fastapi_backend, "Scaffold missing FastAPI backend files"

        # Resolve DevelopmentVersion registered from workflow
        dev_service = DevelopmentVersionService(session=session)
        dev_versions = await dev_service.list_versions(project_id)
        assert dev_versions.total >= 1, "DevelopmentVersion was not auto-registered"
        v1 = dev_versions.items[0]
        version_id = v1.version_id
        print(f"[+] Registered DevelopmentVersion v{v1.version_number} (id={version_id}, status={v1.status})")

        results["STEP_1_CODE_GENERATION"] = {
            "status": "PASS",
            "project_id": str(project_id),
            "version_id": str(version_id),
            "files_count": len(generated_files),
        }

        # ======================================================================
        # STEP 2 & 3: Launch in isolated Docker container and verify via Playwright
        # ======================================================================
        print("\n" + "-" * 70)
        print("STEP 2 & 3: Launch Application Container & Verify via Playwright")
        print("-" * 70)

        runtime_manager = ApplicationRuntimeManager(session=session, docker_executor=docker_executor)
        files_map, manifest = await runtime_manager.resolve_version_files_and_manifest(project_id, version_id)
        print(f"[*] Resolved {len(files_map)} files from version.")
        print(f"[*] Runtime Manifest: entrypoint='{manifest.entrypoint}', port={manifest.application_port}, health_path='{manifest.health_check_path}'")

        # Define deterministic Playwright test definition checking the React + FastAPI journey
        smoke_journey_test = DeterministicBrowserTestDefinition(
            test_id="journey_react_fastapi_live",
            name="Verify React Frontend Calls FastAPI Backend API",
            target_path="/",
            expected_status=200,
            expected_title_contains=f"Task Item Manager {run_uuid}",
            expected_elements=["#root", "#api-status", "#task-form", "#item-list"],
            interactions=[
                DeterministicInteraction(
                    action=BrowserInteractionType.ASSERT_VISIBLE,
                    selector="#api-status",
                ),
                # Wait for React useEffect fetch('/tasks') to finish and update status
                DeterministicInteraction(
                    action=BrowserInteractionType.WAIT,
                    selector="#api-status",
                    value="1.5",
                ),
                DeterministicInteraction(
                    action=BrowserInteractionType.ASSERT_TEXT,
                    selector="#api-status",
                    expected_text="Ready",
                ),
                DeterministicInteraction(
                    action=BrowserInteractionType.ASSERT_VISIBLE,
                    selector="[data-testid='item-card']",
                ),
                DeterministicInteraction(
                    action=BrowserInteractionType.ASSERT_TEXT,
                    selector="#item-list",
                    expected_text="Verify isolated Docker runtime",
                ),
                # Fill form and create new task via React frontend
                DeterministicInteraction(
                    action=BrowserInteractionType.FILL,
                    selector="#new-task-input",
                    value="Live Real E2E Task",
                ),
                DeterministicInteraction(
                    action=BrowserInteractionType.CLICK,
                    selector="#add-task-btn",
                ),
                # Wait for POST response and React state re-render
                DeterministicInteraction(
                    action=BrowserInteractionType.WAIT,
                    selector="#item-list",
                    value="1.0",
                ),
                DeterministicInteraction(
                    action=BrowserInteractionType.ASSERT_TEXT,
                    selector="#item-list",
                    expected_text="Live Real E2E Task",
                ),
                DeterministicInteraction(
                    action=BrowserInteractionType.SCREENSHOT,
                    selector="#root",
                ),
            ],
            capture_screenshot=True,
        )

        test_artifacts_dir = tempfile.mkdtemp(prefix="se_e2e_artifacts_")
        browser_service = BrowserTestingService(
            session=session,
            runtime_manager=runtime_manager,
            browser_executor=browser_executor,
            artifacts_base_dir=test_artifacts_dir,
        )

        print("[*] Launching application container and executing Playwright browser container...")
        test_run = await browser_service.execute_browser_tests(
            project_id=project_id,
            version_id=version_id,
            test_definitions=[smoke_journey_test],
            manifest=manifest,
        )

        print(f"[+] Test Run Status: {test_run.status}")
        print(f"[+] Summary: {test_run.summary}")
        print(f"[+] Total Cases: {test_run.tests_total}, Passed: {test_run.tests_passed}, Failed: {test_run.tests_failed}")
        for case in test_run.test_cases:
            print(f"    - Case '{case.test_id}': status={case.status}, duration={case.duration_seconds}s")
            if case.failed_step:
                print(f"      Failure: {case.failed_step}")
            print(f"      Assertion Summary: {case.assertion_summary}")
            print(f"      Console Errors: {len(case.console_errors)}")
            for ce in case.console_errors:
                print(f"        Console Err: {ce.level} - {ce.message} ({ce.source}:{ce.line_number})")
            print(f"      Network Errors: {len(case.network_errors)}")
            for ne in case.network_errors:
                print(f"        Network Err: {ne.url} - {ne.error_type} {ne.status_code}")
            print(f"      Screenshots: {len(case.screenshots)}")

        assert test_run.status == BrowserTestStatus.PASSED, f"Browser test run failed: {test_run.failure_reason}"
        assert test_run.tests_passed == 1, "Expected 1 passed browser test case"

        results["STEP_2_LAUNCH"] = {"status": "PASS", "runtime_type": "isolated_docker"}
        results["STEP_3_BROWSER_VERIFICATION"] = {
            "status": "PASS",
            "passed_tests": test_run.tests_passed,
            "failed_tests": test_run.tests_failed,
            "screenshots_count": len(test_run.artifacts),
        }

        # ======================================================================
        # STEP 4: Confirm logs, health checks, and shutdown/cleanup
        # ======================================================================
        print("\n" + "-" * 70)
        print("STEP 4: Confirm Logs, Health Checks, and Shutdown/Cleanup")
        print("-" * 70)

        # Run dedicated managed runtime session to inspect container logs, health check, and cleanup
        async with runtime_manager.managed_runtime_session(
            project_id=project_id,
            files_map=files_map,
            manifest=manifest,
            version_id=version_id,
        ) as app_session:
            print(f"[+] Session Status: {app_session.status}")
            print(f"[+] Container Name: {app_session.container_name}")
            print(f"[+] Internal Network: {app_session.network_name}")
            print(f"[+] Internal URL: {app_session.internal_url}")
            print(f"[+] Health Status: {app_session.health_status}")

            assert app_session.status == RuntimeStatus.READY, f"Session failed: {app_session.failure_reason}"
            assert "Application healthy" in (app_session.health_status or ""), "Health check did not confirm readiness"

            # Execute container health probe manually to re-verify
            healthy, health_msg = await docker_executor.poll_health(
                container_name=app_session.container_name,
                port=manifest.application_port,
                path="/health",
                timeout_seconds=5.0,
            )
            print(f"[+] Manual Health Check Probe on /health: healthy={healthy}, msg='{health_msg}'")
            assert healthy is True, "Manual health probe failed"

            # Inspect container logs
            stdout, stderr, truncated = await docker_executor.get_container_logs(app_session.container_name)
            print(f"[+] Container Log Bytes: stdout={len(stdout)}, stderr={len(stderr)}")
            log_sample = (stdout or stderr)[:500].replace("\n", " ")
            print(f"    Log Sample: {log_sample}")
            assert len(stdout) > 0 or len(stderr) > 0, "Expected non-empty container logs"

            saved_container_name = app_session.container_name
            saved_network_name = app_session.network_name

        # Session has exited. Verify guaranteed cleanup
        print("[*] Verifying guaranteed container and network removal...")
        is_running, exit_code = await docker_executor.get_container_status(saved_container_name)
        print(f"[+] Post-cleanup Container Status: is_running={is_running}, exit_code={exit_code}")
        assert is_running is False, "Container was not stopped"

        # Check docker inspect on container
        code, _, _ = await docker_executor._safe_subprocess_exec("docker", "inspect", saved_container_name)
        assert code != 0, "Container still exists after cleanup"
        print(f"[+] Verified container '{saved_container_name}' completely removed.")

        # Check docker inspect on network
        code, _, _ = await docker_executor._safe_subprocess_exec("docker", "network", "inspect", saved_network_name)
        assert code != 0, "Network still exists after cleanup"
        print(f"[+] Verified network '{saved_network_name}' completely removed.")

        results["STEP_4_LOGS_HEALTH_CLEANUP"] = {
            "status": "PASS",
            "health_check": "HTTP 200 OK confirmed",
            "logs_verified": True,
            "container_cleaned": True,
            "network_cleaned": True,
        }

        # Clean artifacts dir
        shutil.rmtree(test_artifacts_dir, ignore_errors=True)

    print("\n" + "=" * 80)
    print("LIVE END-TO-END JOURNEY COMPLETED SUCCESSFULLY")
    print("=" * 80)
    return results


if __name__ == "__main__":
    out = asyncio.run(run_e2e_verification())
    print("\nFINAL EXECUTION RESULTS:")
    print(json.dumps(out, indent=2))
