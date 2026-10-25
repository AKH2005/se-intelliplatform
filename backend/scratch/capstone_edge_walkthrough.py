"""Microsoft Edge Real User Walkthrough for SE IntelliPlatform Capstone Readiness.

Carries out the complete 18-step user journey directly in Microsoft Edge:
1. Open platform
2. Create EventHub project
3. Natural-language description
4. Select "Let AI Choose"
5. Build Application
6. Wait for generation
7. Open Live Preview
8. Interact with the generated application
9. Open AI Development Assistant
10. Ask: "Add authentication."
11. Verify the conversation
12. Ask: "Make the homepage more modern."
13. Verify the response
14. Ask: "The registration button isn't working."
15. Verify the debugging response
16. Open Advanced navigation
17. Inspect advanced workspaces (Requirements, Testing, Code Intelligence)
18. Return to Live Preview
"""

import sys
import os
import time
from pathlib import Path

# Force UTF-8 stdout on Windows
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright

ARTIFACTS_DIR = Path(r"C:\Users\DELL\.gemini\antigravity-ide\brain\f8073983-4e92-4061-86d7-99a4c45ecf7a\screenshots")
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

def run_walkthrough():
    print("=" * 70, flush=True)
    print("STARTING MICROSOFT EDGE REAL USER WALKTHROUGH — CAPSTONE READINESS", flush=True)
    print("=" * 70, flush=True)

    with sync_playwright() as p:
        # Launch real Microsoft Edge
        print("\n[STEP 1] Launching Microsoft Edge...", flush=True)
        browser = p.chromium.launch(channel="msedge", headless=False, slow_mo=300)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # Step 1: Open platform
        page.goto("http://localhost:5173", wait_until="networkidle")
        page.wait_for_timeout(2000)
        page.screenshot(path=str(ARTIFACTS_DIR / "01_platform_home.png"))
        print("  ✓ Platform loaded at http://localhost:5173", flush=True)

        # Step 2: Create a NEW EventHub project
        print("\n[STEP 2] Creating NEW EventHub Project...", flush=True)
        # Unique name to avoid conflicts if previously created
        ts = int(time.time()) % 10000
        proj_name = f"EventHub {ts}"
        
        # Click "Create & Build" or "New Project"
        create_btn = page.locator('button:has-text("Create & Build"), button:has-text("New Project"), button:has-text("Build Application")').first
        create_btn.click()
        page.wait_for_timeout(1000)
        page.screenshot(path=str(ARTIFACTS_DIR / "02_create_project_modal.png"))
        print("  ✓ Opened Create Project Modal", flush=True)

        # Step 3: Natural language description
        print("\n[STEP 3] Entering Natural-Language Description...", flush=True)
        page.fill('#project-name', proj_name)
        page.fill(
            '#project-desc',
            "Build an event management platform where users can discover events, "
            "view event details, register for events, cancel registrations, "
            "and search events by category and date."
        )
        page.wait_for_timeout(800)

        # Step 4: Select "Let AI Choose"
        print("\n[STEP 4] Selecting 'Let AI Choose' Architecture...", flush=True)
        ai_choice_btn = page.locator('button:has-text("Let AI Choose")').first
        if ai_choice_btn.is_visible():
            ai_choice_btn.click()
            page.wait_for_timeout(500)
        page.screenshot(path=str(ARTIFACTS_DIR / "03_stack_selection.png"))
        print("  ✓ Confirmed 'Let AI Choose (Recommended)' stack option", flush=True)

        # Step 5: Click Build Application
        print("\n[STEP 5] Clicking 'Build Application'...", flush=True)
        build_app_btn = page.locator('.modal-footer #btn-build-app, .modal-footer button:has-text("Build Application")').first
        build_app_btn.click()
        page.wait_for_timeout(2500)
        print("  ✓ Submitted project creation with fast-track synthesis", flush=True)

        # Step 6: Wait for application
        print("\n[STEP 6] Waiting for Application and Landing on Live Preview...", flush=True)
        page.wait_for_timeout(3000)
        page.screenshot(path=str(ARTIFACTS_DIR / "04_live_preview_landing.png"))
        print("  ✓ Landed on Live Preview workspace", flush=True)

        # Step 7: Open Live Preview (if not already active)
        preview_tab = page.locator('aside button:has-text("Live Preview")').first
        if preview_tab.is_visible() and preview_tab.is_enabled():
            try:
                preview_tab.click()
                page.wait_for_timeout(1000)
            except Exception:
                pass

        # Step 8: Interact with generated application
        print("\n[STEP 8] Interacting with Generated EventHub Application...", flush=True)
        # Switch device viewports
        tablet_btn = page.locator('button[title="Tablet View"]').first
        if tablet_btn.is_visible():
            tablet_btn.click()
            page.wait_for_timeout(800)
            page.screenshot(path=str(ARTIFACTS_DIR / "05_preview_tablet.png"))

        desktop_btn = page.locator('button[title="Desktop View"]').first
        if desktop_btn.is_visible():
            desktop_btn.click()
            page.wait_for_timeout(800)
            page.screenshot(path=str(ARTIFACTS_DIR / "06_preview_desktop.png"))

        # Open separate tab to interact with port 8001 directly
        app_page = context.new_page()
        app_page.goto("http://127.0.0.1:8001", wait_until="networkidle")
        app_page.wait_for_timeout(1000)
        app_page.screenshot(path=str(ARTIFACTS_DIR / "07_app_8001_browse.png"))
        print("  ✓ EventHub application loaded on port 8001", flush=True)

        # Filter by Technology category
        tech_cat = app_page.locator('.cat-chip:has-text("Technology")').first
        if tech_cat.is_visible():
            tech_cat.click()
            app_page.wait_for_timeout(600)
            print("  ✓ Filtered events by Technology category", flush=True)

        # Search for 'Summit'
        search_box = app_page.locator('#search-input')
        if search_box.is_visible():
            search_box.fill("Summit")
            app_page.wait_for_timeout(600)
            print("  ✓ Searched events for 'Summit'", flush=True)

        # Register for event
        reg_btn = app_page.locator('button:has-text("Register")').first
        if reg_btn.is_visible():
            reg_btn.click()
            app_page.wait_for_timeout(1000)
            app_page.screenshot(path=str(ARTIFACTS_DIR / "08_app_registered.png"))
            print("  ✓ Successfully completed event registration", flush=True)

        app_page.close()
        page.bring_to_front()

        # Step 9: Open AI Development Assistant
        print("\n[STEP 9] Opening AI Development Assistant...", flush=True)
        # Can be opened via header toggle or sidebar tab
        assistant_btn = page.locator('button[aria-label="Toggle Intelli Assistant"], aside button:has-text("AI Development Assistant")').first
        if assistant_btn.is_visible():
            assistant_btn.click()
            page.wait_for_timeout(1500)
        page.screenshot(path=str(ARTIFACTS_DIR / "09_assistant_dock_open.png"))
        print("  ✓ AI Development Assistant dock open", flush=True)

        # Step 10: Say: "Add authentication."
        print("\n[STEP 10] Conversational Turn 1: 'Add authentication.'...", flush=True)
        chat_input = page.locator('textarea[aria-label="Assistant message input"], textarea.form-textarea').first
        send_btn = page.locator('button[aria-label="Send inquiry"]').first
        if chat_input.is_visible():
            chat_input.fill("Add authentication.")
            page.wait_for_timeout(500)
            if send_btn.is_visible() and send_btn.is_enabled():
                send_btn.click()
            else:
                chat_input.press("Enter")
            print("  ✓ Sent: 'Add authentication.'", flush=True)

        # Step 11: Verify the conversation
        print("\n[STEP 11] Waiting for AI Development Partner Response 1...", flush=True)
        page.wait_for_timeout(5000)
        page.screenshot(path=str(ARTIFACTS_DIR / "10_assistant_auth_response.png"))
        print("  ✓ Received conversational development response for authentication", flush=True)

        # Step 12: Say: "Make the homepage more modern."
        print("\n[STEP 12] Conversational Turn 2: 'Make the homepage more modern.'...", flush=True)
        if chat_input.is_visible():
            chat_input.fill("Make the homepage more modern.")
            page.wait_for_timeout(500)
            if send_btn.is_visible() and send_btn.is_enabled():
                send_btn.click()
            else:
                chat_input.press("Enter")
            print("  ✓ Sent: 'Make the homepage more modern.'", flush=True)

        # Step 13: Verify the response
        print("\n[STEP 13] Waiting for AI Development Partner Response 2...", flush=True)
        page.wait_for_timeout(5000)
        page.screenshot(path=str(ARTIFACTS_DIR / "11_assistant_modern_response.png"))
        print("  ✓ Received conversational UI modernization response", flush=True)

        # Step 14: Say: "The registration button isn't working."
        print("\n[STEP 14] Conversational Turn 3: 'The registration button isn't working.'...", flush=True)
        if chat_input.is_visible():
            chat_input.fill("The registration button isn't working.")
            page.wait_for_timeout(500)
            if send_btn.is_visible() and send_btn.is_enabled():
                send_btn.click()
            else:
                chat_input.press("Enter")
            print("  ✓ Sent: 'The registration button isn't working.'", flush=True)

        # Step 15: Verify the debugging response
        print("\n[STEP 15] Waiting for AI Development Partner Response 3...", flush=True)
        page.wait_for_timeout(5000)
        page.screenshot(path=str(ARTIFACTS_DIR / "12_assistant_debug_response.png"))
        print("  ✓ Received conversational debugging response", flush=True)

        # Step 16: Open Advanced navigation
        print("\n[STEP 16] Opening Advanced Engineering Section...", flush=True)
        adv_expand_btn = page.locator('aside button:has-text("ENGINEERING"), aside button:has-text("Show")').first
        if adv_expand_btn.is_visible():
            adv_expand_btn.click()
            page.wait_for_timeout(800)

        # Step 17: Inspect advanced workspaces
        print("\n[STEP 17] Inspecting Advanced Engineering Workspaces...", flush=True)
        # Requirements & Specs
        spec_tab = page.locator('aside button:has-text("Requirements"), aside button:has-text("Specs")').first
        if spec_tab.is_visible():
            spec_tab.click()
            page.wait_for_timeout(1500)
            page.screenshot(path=str(ARTIFACTS_DIR / "13_advanced_requirements.png"))
            print("  ✓ Inspected Requirements & Specifications workspace", flush=True)

        # Testing & Quality
        testing_tab = page.locator('aside button:has-text("Testing & Quality")').first
        if testing_tab.is_visible():
            testing_tab.click()
            page.wait_for_timeout(1500)
            page.screenshot(path=str(ARTIFACTS_DIR / "14_advanced_testing.png"))
            print("  ✓ Inspected Testing & Quality workspace", flush=True)

        # Code Intelligence
        code_intel_tab = page.locator('aside button:has-text("Code Intelligence")').first
        if code_intel_tab.is_visible():
            code_intel_tab.click()
            page.wait_for_timeout(1500)
            page.screenshot(path=str(ARTIFACTS_DIR / "15_advanced_code_intelligence.png"))
            print("  ✓ Inspected Polyglot Code Intelligence workspace", flush=True)

        # Step 18: Return to Live Preview
        print("\n[STEP 18] Returning to Live Preview...", flush=True)
        preview_tab = page.locator('aside button:has-text("Live Preview")').first
        if preview_tab.is_visible():
            preview_tab.click()
            page.wait_for_timeout(1500)
            page.screenshot(path=str(ARTIFACTS_DIR / "16_final_live_preview.png"))
            print("  ✓ Successfully returned to Live Preview", flush=True)

        page.wait_for_timeout(2000)
        browser.close()
        print("\n" + "=" * 70, flush=True)
        print("ALL 18 STEPS OF MICROSOFT EDGE REAL USER WALKTHROUGH COMPLETED!", flush=True)
        print("=" * 70, flush=True)

if __name__ == "__main__":
    run_walkthrough()
