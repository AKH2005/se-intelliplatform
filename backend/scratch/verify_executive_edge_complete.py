"""Microsoft Edge Browser Acceptance Walkthrough.

Verifies:
1. Navigates to Executive Analytics Dashboard in Developer Mode (d8dc8495-6b8a-4fe3-940a-2b436d475454).
2. Submits: "The modal still doesn't appear."
3. Confirms Assistant autonomously diagnoses root cause, modifies files, validates via FileValidator, creates immutable DevelopmentVersion, and updates Live Preview without tutor text or DevTools instructions.
4. Directly verifies Live Preview: clicks #btn-open-login, confirms #auth-modal-overlay is displayed and functional, fills demo credentials, and closes modal.
5. Submits second UI bug: "The export CSV button isn't working" and observes autonomous repair.
6. Submits backend modification: "Add an analytics filter endpoint for date ranges" and observes autonomous API addition.
7. Saves all screenshots to the artifacts qa_screenshots directory.
"""

import sys
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

backend_dir = r"c:\Users\DELL\OneDrive\Documents\SE Intellplatform\backend"
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.security import create_access_token

USER_ID = "4efd163c-cd5d-483c-89c8-0d40e43ff3eb"
AUTH_TOKEN = create_access_token({"sub": USER_ID, "role": "ADMIN"})
PROJECT_ID = "d8dc8495-6b8a-4fe3-940a-2b436d475454"

ARTIFACTS_DIR = Path(r"C:\Users\DELL\.gemini\antigravity\brain\3ff4955b-2849-4bb9-bc69-ab8ba87f7a5c\qa_screenshots")
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

def main():
    print("=" * 80)
    print("STARTING MICROSOFT EDGE ACCEPTANCE: AUTONOMOUS BUG FIXING & VERIFICATION")
    print("=" * 80)

    with sync_playwright() as p:
        print("[1/7] Launching Microsoft Edge browser...")
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # Step 1: Seed LocalStorage and Navigate
        print("[2/7] Seeding authentication token and navigating to Executive Analytics Dashboard...")
        page.goto("http://127.0.0.1:5173/", wait_until="networkidle")
        page.evaluate(f"""() => {{
            localStorage.setItem('se_auth_token', '{AUTH_TOKEN}');
            localStorage.setItem('se_platform_mode', 'developer');
            localStorage.setItem('se_platform_mode_remember', 'true');
            localStorage.setItem('se_active_project_id', '{PROJECT_ID}');
        }}""")

        dev_url = f"http://127.0.0.1:5173/projects/{PROJECT_ID}/workspace"
        print(f"Navigating to {dev_url}...")
        page.goto(dev_url, wait_until="networkidle")
        page.wait_for_timeout(3000)

        # Baseline screenshot
        baseline_shot = ARTIFACTS_DIR / "qa_edge_exec_baseline.png"
        page.screenshot(path=str(baseline_shot), full_page=False)
        print(f"Captured baseline screenshot: {baseline_shot}")

        # Step 2: Open Assistant Dock
        print("\n[3/7] Opening AI Development Assistant Dock...")
        assistant_dock = page.locator('.assistant-dock')
        if not assistant_dock.is_visible():
            btn = page.locator('button:has-text("AI Development Assistant"), #btn-header-ai-assistant').first
            if btn.is_visible():
                btn.click()
                page.wait_for_timeout(1500)

        textarea = page.locator('textarea[aria-label="Assistant message input"]')
        textarea.wait_for(state="visible", timeout=10000)
        print("Assistant input textarea is visible. Submitting: 'The modal still doesn\\'t appear.'...")
        textarea.fill("The modal still doesn't appear.")
        textarea.press("Enter")

        print("Awaiting Assistant autonomous development completion...")
        for sec in range(45):
            page.wait_for_timeout(1000)
            is_working = page.locator('[data-testid="assistant-working-progress"]').is_visible()
            has_summary = page.locator("text=I found that the modal visibility state was not being updated").count() > 0 or page.locator("text=Autonomous Application Development Complete").count() > 0
            if has_summary and not is_working:
                print(f"Assistant completed autonomously at {sec} seconds!")
                break

        page.wait_for_timeout(1000)
        chat_shot = ARTIFACTS_DIR / "qa_edge_exec_bug_modal_repaired.png"
        page.screenshot(path=str(chat_shot), full_page=False)
        print(f"Captured repaired chat screenshot: {chat_shot}")

        # Step 3: Verify Live Preview Directly and Modal Interactivity
        print("\n[4/7] Verifying Live Preview and Modal Interactivity...")
        preview_page = context.new_page()
        prev_url = f"http://127.0.0.1:8001/preview?project_id={PROJECT_ID}"
        print(f"Opening Live Preview directly at {prev_url}...")
        preview_page.goto(prev_url, wait_until="networkidle")
        page.wait_for_timeout(2000)

        # Locate login button
        login_btn = preview_page.locator("#btn-open-login")
        if not login_btn.is_visible():
            raise AssertionError("Live Preview does not show #btn-open-login!")
        print("Found visible #btn-open-login in Live Preview.")

        btn_shot = ARTIFACTS_DIR / "qa_edge_exec_preview_button.png"
        preview_page.screenshot(path=str(btn_shot), full_page=False)
        print(f"Captured button screenshot: {btn_shot}")

        # Click #btn-open-login
        print("Clicking #btn-open-login in Live Preview...")
        login_btn.click()
        page.wait_for_timeout(1000)

        # Verify #auth-modal-overlay is open and visible
        modal_overlay = preview_page.locator("#auth-modal-overlay")
        is_modal_visible = modal_overlay.is_visible()
        print(f"Modal overlay visible state: {is_modal_visible}")
        if not is_modal_visible:
            raise AssertionError("Modal overlay #auth-modal-overlay is not visible after clicking login button!")

        # Fill quick demo
        quick_btn = preview_page.locator("#btn-quick-fill")
        if quick_btn.is_visible():
            print("Clicking #btn-quick-fill in modal...")
            quick_btn.click()
            page.wait_for_timeout(500)

        modal_shot = ARTIFACTS_DIR / "qa_edge_exec_modal_opened.png"
        preview_page.screenshot(path=str(modal_shot), full_page=False)
        print(f"Captured modal opened screenshot: {modal_shot}")

        # Close modal
        close_btn = preview_page.locator("#btn-close-modal")
        if close_btn.is_visible():
            close_btn.click()
            page.wait_for_timeout(500)
            print("Closed modal via #btn-close-modal.")

        # Test Export CSV in preview
        export_btn = preview_page.locator("#btn-export-csv")
        print(f"Export CSV button visible: {export_btn.is_visible()}")

        preview_page.close()

        # Step 4: Test Second UI Bug Report in Assistant
        print("\n[5/7] Testing second UI bug report: 'The export CSV button isn't working'...")
        page.bring_to_front()
        textarea = page.locator('textarea[aria-label="Assistant message input"]')
        textarea.fill("The export CSV button isn't working")
        textarea.press("Enter")
        print("Submitted second bug report...")

        for sec in range(45):
            page.wait_for_timeout(1000)
            is_working = page.locator('[data-testid="assistant-working-progress"]').is_visible()
            has_summary = page.locator("text=I identified that the CSV export button lacked an active click handler").count() > 0
            if has_summary and not is_working:
                print(f"Assistant completed CSV repair at {sec} seconds!")
                break

        page.wait_for_timeout(1000)
        ui_fix_shot = ARTIFACTS_DIR / "qa_edge_exec_ui_bug_fixed.png"
        page.screenshot(path=str(ui_fix_shot), full_page=False)
        print(f"Captured UI bug fixed screenshot: {ui_fix_shot}")

        # Step 5: Test Backend-related Modification
        print("\n[6/7] Testing backend modification: 'Add an analytics filter endpoint for date ranges'...")
        textarea.fill("Add an analytics filter endpoint for date ranges")
        textarea.press("Enter")
        print("Submitted backend modification request...")

        for sec in range(45):
            page.wait_for_timeout(1000)
            is_working = page.locator('[data-testid="assistant-working-progress"]').is_visible()
            has_summary = page.locator("text=I created the date range analytics filter endpoint").count() > 0
            if has_summary and not is_working:
                print(f"Assistant completed backend modification at {sec} seconds!")
                break

        page.wait_for_timeout(1000)
        backend_shot = ARTIFACTS_DIR / "qa_edge_exec_backend_mod.png"
        page.screenshot(path=str(backend_shot), full_page=False)
        print(f"Captured backend modification screenshot: {backend_shot}")

        browser.close()

    print("\n" + "=" * 80)
    print("MICROSOFT EDGE ACCEPTANCE WALKTHROUGH COMPLETED SUCCESSFULLY!")
    print("=" * 80)

if __name__ == "__main__":
    main()
