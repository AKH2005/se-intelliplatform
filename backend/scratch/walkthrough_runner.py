"""SE IntelliPlatform End-to-End Real Browser Walkthrough Automation.

Runs against http://localhost:5173/ using Playwright in headed mode (visible browser on desktop).
Captures authentic full-page screenshots at all key milestones and saves them to the artifacts directory.
"""

import os
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, expect

ARTIFACTS_DIR = Path(r"C:\Users\DELL\.gemini\antigravity-ide\brain\922d928e-a9d5-49ee-bd75-1a72d9ef9507")
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

def snap(page: Page, name: str) -> str:
    """Capture full page screenshot to artifacts directory."""
    path = ARTIFACTS_DIR / f"{name}.png"
    page.screenshot(path=str(path), full_page=True)
    print(f"Captured screenshot: {path.name}", flush=True)
    return str(path)

def run_phase_a_b(page: Page):
    """Phase A & B: Open Platform and Inspect UI Workspaces."""
    print("\n--- PHASE A & B: Open Website & Inspect Workspaces ---", flush=True)
    page.goto("http://localhost:5173", wait_until="networkidle")
    page.wait_for_timeout(2000)
    snap(page, "01_homepage_dashboard")
    print(f"Page title: {page.title()}", flush=True)

def run_phase_c(page: Page):
    """Phase C: Create Project 'TaskFlow' through UI."""
    print("\n--- PHASE C: Create Project 'TaskFlow' ---", flush=True)
    # Click New Project button in Header
    new_proj_btn = page.locator('header button:has-text("New Project")')
    if not new_proj_btn.is_visible():
        new_proj_btn = page.locator('button:has-text("Create Project")').first
    new_proj_btn.click()
    page.wait_for_timeout(1000)
    
    # Fill Modal using exact IDs
    page.fill('#project-name', "TaskFlow")
    page.fill('#project-desc', "A task management web application where users can create, view, update, and delete tasks.")
    
    # Select Status IN_PROGRESS
    select_status = page.locator('#project-status')
    if select_status.is_visible():
        select_status.select_option("IN_PROGRESS")
        
    snap(page, "02_create_project_modal")
    
    # Submit
    page.click('button:has-text("Create Project")')
    page.wait_for_timeout(2500)
    
    snap(page, "03_project_created_overview")
    print("Project TaskFlow created and active in header.", flush=True)

def run_phase_d(page: Page):
    """Phase D: Add Requirements through UI and Create Snapshot."""
    print("\n--- PHASE D: Requirements Management ---", flush=True)
    page.click('button.nav-item:has-text("Specification")')
    page.wait_for_timeout(1500)
    snap(page, "04_specification_workspace")

    requirements = [
        ("Users can create tasks", "Allow users to create new tasks with title, description, priority, and due date.", "HIGH"),
        ("Users can view all tasks", "Display list of tasks with status, priority, and filtering options.", "HIGH"),
        ("Users can update task status", "Allow updating task title, description, status, and due date.", "MEDIUM"),
        ("Users can delete tasks", "Enable permanent or soft deletion of completed or unwanted tasks.", "MEDIUM"),
        ("Tasks contain title, description, priority, status, and due date", "Canonical data model for task entities.", "HIGH"),
        ("The application exposes backend APIs", "REST endpoints for CRUD task operations.", "HIGH"),
        ("The application has a usable frontend", "Responsive web UI with interactive forms and dashboard.", "HIGH"),
        ("The application must be testable through browser automation", "Accessible DOM selectors and predictable interaction paths.", "HIGH"),
    ]

    for idx, (title, desc, priority) in enumerate(requirements, 1):
        print(f"Adding requirement {idx}: {title}", flush=True)
        page.click('button:has-text("New Requirement")')
        page.wait_for_timeout(800)
        page.fill('#req-title', title)
        page.fill('#req-desc', desc)
        
        # Select Priority
        p_select = page.locator('#req-priority')
        if p_select.is_visible():
            p_select.select_option(priority)
            
        page.click('button:has-text("Save Requirement")')
        page.wait_for_timeout(1200)

    snap(page, "05_requirements_list")

    # Create Context Snapshot
    print("Creating Context Snapshot...", flush=True)
    page.click('button:has-text("Create Snapshot")')
    page.wait_for_timeout(800)
    snap_input = page.locator('#snapshot-summary')
    if snap_input.is_visible():
        snap_input.fill("Baseline TaskFlow Requirements Snapshot")
    page.click('button:has-text("Commit Snapshot")')
    page.wait_for_timeout(2000)

    # Click Versioned Snapshots Tab
    page.click('button[role="tab"]:has-text("Versioned Snapshots")')
    page.wait_for_timeout(1500)
    snap(page, "06_context_snapshots_view")

def run_phase_e_f_g(page: Page):
    """Phases E, F, G: Requirement Analysis, Architecture, and Database Design via Workflow Studio."""
    print("\n--- PHASES E, F, G: Multi-Agent Software Design Workflow ---", flush=True)
    # Navigate to Workflow Studio
    page.click('button.nav-item:has-text("Workflow Studio")')
    page.wait_for_timeout(2000)
    snap(page, "07_workflow_studio")

    # Select Software Design Workflow if not active
    sw_design = page.locator('div:has-text("Software Design Workflow")').first
    if sw_design.is_visible():
        sw_design.click()
        page.wait_for_timeout(1000)

    # Click Execute Workflow
    exec_btn = page.locator('button:has-text("Execute Workflow")')
    print("Clicking 'Execute Workflow' (Software Design: Analysis -> Architecture -> DB Design)...", flush=True)
    exec_btn.click()

    # Wait for execution to finish (may take 10-30s depending on LLM)
    print("Waiting for workflow execution to complete...", flush=True)
    page.wait_for_selector('div:has-text("COMPLETED")', timeout=60000)
    page.wait_for_timeout(3000)
    snap(page, "08_workflow_execution_completed")

    # Navigate to Intelligence Workspace to view generated artifacts
    print("Navigating to Intelligence Workspace...", flush=True)
    page.click('button.nav-item:has-text("Intelligence")')
    page.wait_for_timeout(2000)
    snap(page, "09_intelligence_artifacts_overview")

    # Inspect Blueprints tab in Specification
    print("Checking Architecture & ERD Blueprints in Specification...", flush=True)
    page.click('button.nav-item:has-text("Specification")')
    page.wait_for_timeout(1500)
    page.click('button[role="tab"]:has-text("Architecture & ERD Blueprints")')
    page.wait_for_timeout(2000)
    snap(page, "10_architecture_and_erd_blueprints")

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=False, slow_mo=400)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        
        try:
            run_phase_a_b(page)
            run_phase_c(page)
            run_phase_d(page)
            run_phase_e_f_g(page)
            print("\nPhases A - G completed successfully!", flush=True)
        finally:
            page.wait_for_timeout(3000)
            browser.close()

if __name__ == "__main__":
    main()
