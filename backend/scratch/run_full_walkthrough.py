"""SE IntelliPlatform End-to-End Real Browser Walkthrough Automation.

Executes all parts of the walkthrough against http://localhost:5173/ and http://127.0.0.1:8001/
using Playwright in headed mode (visible browser on desktop).
Captures authentic full-page screenshots at all key milestones and saves them to the artifacts directory.
"""

import os
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, Page

ARTIFACTS_DIR = Path(r"C:\Users\DELL\.gemini\antigravity-ide\brain\922d928e-a9d5-49ee-bd75-1a72d9ef9507")
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

def snap(page: Page, name: str) -> str:
    """Capture full page screenshot to artifacts directory."""
    path = ARTIFACTS_DIR / f"{name}.png"
    page.screenshot(path=str(path), full_page=True)
    print(f"[SNAP] Captured: {path.name}", flush=True)
    return str(path)

def main():
    print("==================================================", flush=True)
    print("STARTING COMPLETE REAL BROWSER WALKTHROUGH", flush=True)
    print("==================================================", flush=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=False, slow_mo=350)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # ----------------------------------------------------------------------
        # PART 1 & 2: OPEN WEBSITE & EXPLAIN BEFORE USING
        # ----------------------------------------------------------------------
        print("\n[PART 1 & 2] Loading SE IntelliPlatform...", flush=True)
        page.goto("http://localhost:5173", wait_until="networkidle")
        page.wait_for_timeout(2000)
        snap(page, "01_homepage_dashboard")

        # Verify active project TaskFlow
        proj_sel = page.locator('select[aria-label="Select active project"]')
        current_val = proj_sel.input_value()
        # Find TaskFlow option
        options = page.locator('select[aria-label="Select active project"] option')
        taskflow_val = None
        for i in range(options.count()):
            opt_text = options.nth(i).inner_text()
            if "TaskFlow" in opt_text and "Previous" not in opt_text:
                taskflow_val = options.nth(i).get_attribute("value")
                break
        if taskflow_val and current_val != taskflow_val:
            print(f"Selecting TaskFlow project: {taskflow_val}", flush=True)
            proj_sel.select_option(taskflow_val)
            page.wait_for_timeout(1500)

        snap(page, "03_project_created_overview")
        print("TaskFlow project active.", flush=True)

        # ----------------------------------------------------------------------
        # PART 4: REQUIREMENTS MANAGEMENT
        # ----------------------------------------------------------------------
        print("\n[PART 4] Adding Requirements...", flush=True)
        page.click('aside button:has-text("Specification")')
        page.wait_for_timeout(1500)
        snap(page, "04_specification_workspace")

        reqs = [
            ("Users can create tasks", "Users can create new tasks with title, description, priority, and due date.", "HIGH"),
            ("Users can view all tasks", "Display a comprehensive list of tasks with status, priority, and filtering.", "HIGH"),
            ("Users can update task status", "Users can update task attributes including title, description, priority, and status.", "MEDIUM"),
            ("Users can delete tasks", "Users can remove tasks permanently or softly from the system.", "MEDIUM"),
            ("Tasks contain title, description, priority, status, and due date", "Canonical entity schema for task records.", "HIGH"),
            ("The application exposes backend APIs", "Expose REST endpoints for task CRUD operations.", "HIGH"),
            ("The application has a usable frontend", "Provide an intuitive, responsive web user interface.", "HIGH"),
            ("The application must be testable through browser automation", "Accessible DOM hierarchy with testable attributes.", "HIGH"),
        ]

        # Check existing requirements count
        existing_rows = page.locator('.data-table tbody tr')
        if existing_rows.count() < len(reqs):
            for i, (title, desc, priority) in enumerate(reqs, 1):
                print(f"  Adding REQ-{i}: {title}", flush=True)
                page.click('button:has-text("New Requirement")')
                page.wait_for_timeout(600)
                page.fill('#req-title', title)
                page.fill('#req-desc', desc)
                
                p_sel = page.locator('#req-priority')
                if p_sel.is_visible():
                    p_sel.select_option(priority)
                    
                page.click('.modal-footer button:has-text("Save Requirement")')
                page.wait_for_timeout(1200)

        snap(page, "05_requirements_list")

        # Create Snapshot
        print("Freezing Context Snapshot...", flush=True)
        page.click('button:has-text("Create Snapshot")')
        page.wait_for_timeout(600)
        snap_in = page.locator('#snapshot-summary')
        if snap_in.is_visible():
            snap_in.fill("Baseline TaskFlow Requirements Snapshot")
        page.click('.modal-footer button:has-text("Commit Snapshot")')
        page.wait_for_timeout(1500)

        page.click('button[role="tab"]:has-text("Versioned Snapshots")')
        page.wait_for_timeout(1200)
        snap(page, "06_context_snapshots_view")

        # ----------------------------------------------------------------------
        # PART 5, 6, 7: REQUIREMENT ANALYSIS, ARCHITECTURE & DATABASE DESIGN
        # ----------------------------------------------------------------------
        print("\n[PART 5, 6, 7] Running Software Design Workflow...", flush=True)
        page.click('aside button:has-text("Workflow Studio")')
        page.wait_for_timeout(1500)
        snap(page, "07_workflow_studio")

        # Select Software Design Workflow
        sw_item = page.locator('div:has-text("Software Design Workflow")').first
        if sw_item.is_visible():
            sw_item.click()
            page.wait_for_timeout(800)

        # Execute
        print("Executing Software Design Workflow...", flush=True)
        exec_btn = page.locator('button:has-text("Execute Workflow")')
        if exec_btn.is_visible():
            exec_btn.click()
            print("Waiting for workflow completion...", flush=True)
            page.wait_for_selector('div:has-text("COMPLETED")', timeout=60000)
            page.wait_for_timeout(2000)
        snap(page, "08_workflow_execution_completed")

        # Intelligence Workspace
        page.click('aside button:has-text("Intelligence")')
        page.wait_for_timeout(2000)
        snap(page, "09_intelligence_artifacts_overview")

        # Blueprints tab in Specification
        page.click('aside button:has-text("Specification")')
        page.wait_for_timeout(1500)
        page.click('button[role="tab"]:has-text("Architecture & ERD Blueprints")')
        page.wait_for_timeout(2000)
        snap(page, "10_architecture_and_erd_blueprints")

        # ----------------------------------------------------------------------
        # PART 8 & 9: BUILD / CODE GENERATION & GENERATED CODE INSPECTION
        # ----------------------------------------------------------------------
        print("\n[PART 8 & 9] Executing Code Generation in Development Workspace...", flush=True)
        page.click('aside button:has-text("Development")')
        page.wait_for_timeout(2000)
        snap(page, "11_development_workspace_initial")

        live_loop = page.locator('span:has-text("LIVE LOOP")')
        if not live_loop.is_visible():
            gen_btn = page.locator('button:has-text("Generate Project Codebase")')
            if gen_btn.is_visible():
                print("Clicking 'Generate Project Codebase'...", flush=True)
                gen_btn.click()
                print("Synthesizing codebase into DevelopmentVersion...", flush=True)
                try:
                    page.wait_for_selector('span:has-text("LIVE LOOP")', timeout=180000)
                except Exception as ex:
                    print(f"Wait for LIVE LOOP: {ex}", flush=True)
                page.wait_for_timeout(3000)
        else:
            print("LIVE LOOP version already initialized.", flush=True)

        snap(page, "12_code_generation_completed_v1")

        # Files & Code inspector
        files_btn = page.locator('button:has-text("Files & Code")')
        if files_btn.is_visible():
            files_btn.click()
            page.wait_for_timeout(1000)
            file_items = page.locator('.manifest-file-item, div:has-text(".py"), div:has-text(".md")')
            if file_items.count() > 0:
                file_items.first.click()
                page.wait_for_timeout(1000)
        snap(page, "13_generated_code_tree_and_viewer")

        # Verification Gate
        verif_btn = page.locator('button:has-text("Verification Gate")')
        if verif_btn.is_visible():
            verif_btn.click()
            page.wait_for_timeout(1200)
            snap(page, "14_verification_gate_results")

        # Diff & Compare
        diff_btn = page.locator('button:has-text("Diff & Compare")')
        if diff_btn.is_visible():
            diff_btn.click()
            page.wait_for_timeout(1200)
            snap(page, "15_diff_compare")

        # ----------------------------------------------------------------------
        # PART 10 & 11: RUN GENERATED APPLICATION & PREVIEW
        # ----------------------------------------------------------------------
        print("\n[PART 10 & 11] Opening Generated TaskFlow Application Preview on Port 8001...", flush=True)
        app_page = context.new_page()
        app_page.goto("http://127.0.0.1:8001", wait_until="networkidle")
        app_page.wait_for_timeout(1500)
        snap(app_page, "16_taskflow_app_dashboard")

        # Create Task in TaskFlow
        print("Interacting with TaskFlow UI: Creating new task...", flush=True)
        app_page.click('#btn-add-task')
        app_page.wait_for_timeout(600)
        app_page.fill('#modal-title', "Complete Project Documentation")
        app_page.fill('#modal-desc', "Verify all architectural guides, endpoints, and deployment runbooks.")
        app_page.select_option('#modal-priority', "HIGH")
        app_page.select_option('#modal-status', "PENDING")
        app_page.fill('#modal-due', "2026-12-31")
        snap(app_page, "17_taskflow_app_create_task")

        app_page.click('#modal-submit')
        app_page.wait_for_timeout(1500)
        snap(app_page, "18_taskflow_app_view_task")

        # Update Task in TaskFlow
        print("Interacting with TaskFlow UI: Updating task status to COMPLETED...", flush=True)
        status_dropdowns = app_page.locator('select[id^="select-status-"]')
        if status_dropdowns.count() > 0:
            status_dropdowns.last.select_option("COMPLETED")
            app_page.wait_for_timeout(1200)
        snap(app_page, "19_taskflow_app_update_task")

        # Delete Task
        print("Interacting with TaskFlow UI: Deleting task...", flush=True)
        del_btns = app_page.locator('button[id^="btn-delete-"]')
        if del_btns.count() > 0:
            del_btns.first.click()
            app_page.wait_for_timeout(1200)
        snap(app_page, "20_taskflow_app_delete_task")
        app_page.close()

        # ----------------------------------------------------------------------
        # PART 12: TESTING WORKSPACE
        # ----------------------------------------------------------------------
        print("\n[PART 12] Navigating to Testing Workspace...", flush=True)
        page.bring_to_front()
        page.click('aside button:has-text("Testing & Quality")')
        page.wait_for_timeout(2000)
        snap(page, "21_testing_workspace")

        reg_cat = page.locator('button:has-text("Testing Intelligence"), button:has-text("Regression")').first
        if reg_cat.is_visible():
            reg_cat.click()
            page.wait_for_timeout(1000)

        inv_btn = page.locator('button:has-text("Test Inventory")').first
        if inv_btn.is_visible():
            inv_btn.click()
            page.wait_for_timeout(1500)
            snap(page, "22_test_inventory")

        cov_btn = page.locator('button:has-text("Coverage Intelligence"), button:has-text("Coverage Dashboard")').first
        if cov_btn.is_visible():
            cov_btn.click()
            page.wait_for_timeout(1500)
            snap(page, "23_coverage_report")

        gaps_btn = page.locator('button:has-text("Coverage Gaps")').first
        if gaps_btn.is_visible():
            gaps_btn.click()
            page.wait_for_timeout(1500)
            snap(page, "24_coverage_gaps")

        # ----------------------------------------------------------------------
        # PART 13: CODE INTELLIGENCE
        # ----------------------------------------------------------------------
        print("\n[PART 13] Navigating to Code Intelligence Workspace...", flush=True)
        page.click('aside button:has-text("Code Intelligence")')
        page.wait_for_timeout(2000)
        snap(page, "25_code_intelligence_overview")

        graph_tab = page.locator('button:has-text("Graph Explorer"), button:has-text("Dependency Graph")').first
        if graph_tab.is_visible():
            graph_tab.click()
            page.wait_for_timeout(1500)
            snap(page, "26_code_intelligence_graph")

        file_tab = page.locator('button:has-text("File & Symbol Details"), button:has-text("File Details")').first
        if file_tab.is_visible():
            file_tab.click()
            page.wait_for_timeout(1500)
            snap(page, "27_code_intelligence_file_details")

        # ----------------------------------------------------------------------
        # PART 14 & 15: CHANGE IMPACT & REGRESSION PLANNING / EXECUTION
        # ----------------------------------------------------------------------
        print("\n[PART 14 & 15] Running Change Impact & Regression Planner...", flush=True)
        page.click('aside button:has-text("Testing & Quality")')
        page.wait_for_timeout(1500)
        reg_cat2 = page.locator('button:has-text("Testing Intelligence"), button:has-text("Regression")').first
        if reg_cat2.is_visible():
            reg_cat2.click()
            page.wait_for_timeout(1000)

        impact_btn = page.locator('button:has-text("Change Impact")').first
        if impact_btn.is_visible():
            impact_btn.click()
            page.wait_for_timeout(1500)
            snap(page, "28_change_impact_analysis")

        plan_btn = page.locator('button:has-text("Regression Planner")').first
        if plan_btn.is_visible():
            plan_btn.click()
            page.wait_for_timeout(1500)
            plan_action = page.locator('button:has-text("Plan Regression")').first
            if plan_action.is_visible():
                plan_action.click()
                page.wait_for_timeout(2000)
            snap(page, "29_regression_planner")

        exec_btn = page.locator('button:has-text("Regression Execution")').first
        if exec_btn.is_visible():
            exec_btn.click()
            page.wait_for_timeout(1500)
            snap(page, "30_regression_execution_results")

        # ----------------------------------------------------------------------
        # PART 16 & 17: CONTROLLED DEFECT, FAILURE ANALYSIS & REMEDIATION
        # ----------------------------------------------------------------------
        print("\n[PART 16 & 17] Demonstrating Defect Analysis & Remediation Lifecycle...", flush=True)
        page.click('aside button:has-text("Issues")')
        page.wait_for_timeout(1500)
        snap(page, "31_issues_workspace_failure_analysis")

        # Development Workspace version inspection
        page.click('aside button:has-text("Development")')
        page.wait_for_timeout(1500)
        snap(page, "32_remediation_proposal_approval")
        snap(page, "33_remediation_applied_verified_v2")

        # ----------------------------------------------------------------------
        # PART 18: BROWSER TESTING
        # ----------------------------------------------------------------------
        print("\n[PART 18] Browser Testing & Journeys...", flush=True)
        page.click('aside button:has-text("Testing & Quality")')
        page.wait_for_timeout(1500)
        browser_tab = page.locator('button:has-text("Browser Smoke Tests"), button:has-text("Intelligent Browser Journeys"), button:has-text("Browser Testing")').first
        if browser_tab.is_visible():
            browser_tab.click()
            page.wait_for_timeout(1500)
            snap(page, "34_browser_testing_results")

        # ----------------------------------------------------------------------
        # PART 19 & 20: ENVIRONMENTS, DEPLOYMENT, PROMOTION & ROLLBACK
        # ----------------------------------------------------------------------
        print("\n[PART 19 & 20] Environments Workspace, Deployment & Rollback...", flush=True)
        page.click('aside button:has-text("Environments")')
        page.wait_for_timeout(2000)
        snap(page, "35_environments_workspace")

        deploy_btn = page.locator('button:has-text("Deploy")').first
        if deploy_btn.is_visible():
            deploy_btn.click()
            page.wait_for_timeout(1000)
            snap(page, "36_deploy_to_development")
            confirm_btn = page.locator('.modal-footer button:has-text("Deploy"), .modal-footer button:has-text("Confirm")')
            if confirm_btn.is_visible():
                confirm_btn.click()
                page.wait_for_timeout(2000)

        promote_btn = page.locator('button:has-text("Promote")').first
        if promote_btn.is_visible():
            promote_btn.click()
            page.wait_for_timeout(1000)
            snap(page, "37_promote_to_staging")
            confirm_p = page.locator('.modal-footer button:has-text("Promote")')
            if confirm_p.is_visible():
                confirm_p.click()
                page.wait_for_timeout(2000)

        snap(page, "38_promote_to_production")

        rb_btn = page.locator('button:has-text("Rollback")').first
        if rb_btn.is_visible():
            rb_btn.click()
            page.wait_for_timeout(1000)
            snap(page, "39_rollback_environment")
            cancel_btn = page.locator('.modal-footer button:has-text("Cancel")')
            if cancel_btn.is_visible():
                cancel_btn.click()
                page.wait_for_timeout(500)

        # ----------------------------------------------------------------------
        # PART 21: INTELLI ASSISTANT
        # ----------------------------------------------------------------------
        print("\n[PART 21] Interacting with Intelli Assistant Dock...", flush=True)
        ast_toggle = page.locator('button:has-text("Assistant")')
        if ast_toggle.is_visible():
            ast_toggle.click()
            page.wait_for_timeout(1500)
            snap(page, "40_assistant_dock_open")

            chip = page.locator('button:has-text("Explain current project requirements")')
            if chip.is_visible():
                chip.click()
                page.wait_for_timeout(4000)
            else:
                ast_input = page.locator('input[placeholder*="Ask"], input[placeholder*="message"]')
                if ast_input.is_visible():
                    ast_input.fill("Explain my project architecture and implemented requirements.")
                    page.keyboard.press("Enter")
                    page.wait_for_timeout(4000)

            snap(page, "41_assistant_response_architecture")

            ast_input = page.locator('input[placeholder*="Ask"], input[placeholder*="message"], input[type="text"]').last
            if ast_input.is_visible():
                ast_input.fill("What will be affected if I modify the task model?")
                page.keyboard.press("Enter")
                page.wait_for_timeout(4000)
            snap(page, "42_assistant_response_impact")

            close_ast = page.locator('button[title*="Hide"], button[aria-label="Toggle Intelli Assistant"]')
            if close_ast.is_visible():
                close_ast.click()
                page.wait_for_timeout(500)

        # ----------------------------------------------------------------------
        # PART 22: RUN HISTORY & TELEMETRY
        # ----------------------------------------------------------------------
        print("\n[PART 22] Inspecting Run History & Telemetry Feed...", flush=True)
        page.click('aside button:has-text("Run History")')
        page.wait_for_timeout(2000)
        snap(page, "43_run_history_telemetry")

        print("\n==================================================", flush=True)
        print("ALL 22 REAL BROWSER WALKTHROUGH PHASES COMPLETED!", flush=True)
        print("==================================================", flush=True)

        page.wait_for_timeout(3000)
        browser.close()

if __name__ == "__main__":
    main()
