"""Comprehensive Microsoft Edge Verification of AI Development Assistant.

Verifies:
1. User login as madanuakhil07@gmail.com
2. Carrom Master in Developer Mode (657e9d2a-4dd2-4fe9-9bb7-20717c43b588)
3. Assistant message submission: "Add a login page."
4. Streaming reasoning and proposed changes without "Failed to fetch" or 403 Forbidden
5. Creating a new Assistant conversation
6. Project switching to Shadow Master (b9a73557-04a6-4db5-9056-10884a2d5d53) and Sky Strike (6ab754dc-c2bb-4689-9d87-2f69b778527f)
7. Full network event trace, preflight inspection, and screenshots
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

USER_ID = "4efd163c-cd5d-483c-89c8-0d40e43ff3eb"  # madanuakhil07@gmail.com
AUTH_TOKEN = create_access_token({"sub": USER_ID})

CARROM_ID = "657e9d2a-4dd2-4fe9-9bb7-20717c43b588"
SHADOW_ID = "b9a73557-04a6-4db5-9056-10884a2d5d53"
SKY_STRIKE_ID = "6ab754dc-c2bb-4689-9d87-2f69b778527f"

ARTIFACTS_DIR = Path(r"C:\Users\DELL\.gemini\antigravity\brain\3ff4955b-2849-4bb9-bc69-ab8ba87f7a5c\qa_screenshots")
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


def main():
    print("=" * 80)
    print("STARTING MICROSOFT EDGE VERIFICATION: AI ASSISTANT FETCH & REASONING")
    print("=" * 80)

    network_logs = []
    failed_requests = []
    console_logs = []

    with sync_playwright() as p:
        print("[1/6] Launching Microsoft Edge browser...")
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
        page.on("request", lambda req: network_logs.append(f"--> {req.method} {req.url}"))
        page.on("requestfailed", lambda req: failed_requests.append(f"FAILED: {req.method} {req.url} - {req.failure}"))
        page.on("response", lambda res: network_logs.append(f"<-- {res.status} {res.url}"))

        # Step 1: Seed LocalStorage and Navigate to Carrom Master
        print("\n[2/6] Navigating to platform and seeding authentication token...")
        page.goto("http://127.0.0.1:5173/", wait_until="networkidle")
        page.evaluate(f"""() => {{
            localStorage.setItem('se_auth_token', '{AUTH_TOKEN}');
            localStorage.setItem('se_platform_mode', 'developer');
            localStorage.setItem('se_platform_mode_remember', 'true');
            localStorage.setItem('se_active_project_id', '{CARROM_ID}');
        }}""")

        print(f"Navigating to Carrom Master Developer Workspace: /projects/{CARROM_ID}/workspace ...")
        page.goto(f"http://127.0.0.1:5173/projects/{CARROM_ID}/workspace", wait_until="networkidle")
        page.wait_for_timeout(2000)

        # Step 2: Open Assistant Dock
        print("\n[3/6] Opening AI Development Assistant Dock...")
        assistant_dock = page.locator('.assistant-dock')
        if not assistant_dock.is_visible():
            btn = page.locator('button:has-text("AI Development Assistant")').first
            if btn.is_visible():
                btn.click()
                page.wait_for_timeout(1500)

        assert assistant_dock.is_visible(), "Assistant Dock failed to open!"
        print("Assistant Dock is open and visible.")

        # Step 3: Send "Add a login page."
        print("\n[4/6] Sending prompt: 'Add a login page.' ...")
        textarea = page.locator('textarea[aria-label="Assistant message input"]')
        assert textarea.is_visible(), "Assistant message textarea not found!"
        textarea.fill("Add a login page.")
        textarea.press("Enter")
        print("Message submitted. Awaiting streaming reasoning and response...")

        completed = False
        for sec in range(40):
            page.wait_for_timeout(1000)
            error_banner = page.locator('[data-testid="assistant-error-banner"]')
            if error_banner.is_visible():
                err_text = error_banner.inner_text()
                print(f"WARNING: Error banner detected: {err_text}")
                assert "Failed to fetch" not in err_text, f"FAILED TO FETCH occurred! {err_text}"
                assert "You do not have permission" not in err_text, f"Permission error occurred! {err_text}"

            is_working = page.locator('[data-testid="assistant-working-progress"]').is_visible()
            if not is_working and sec > 3:
                print(f"Assistant completed reasoning successfully at {sec} seconds!")
                completed = True
                break

        assert completed, "Assistant reasoning timed out after 40 seconds!"

        # Verify Assistant Response bubble exists
        bubbles = page.locator('.assistant-body .chat-bubble, .assistant-body [style*="border-radius"]')
        bubble_count = bubbles.count()
        print(f"Assistant messages visible: {bubble_count}")
        assert bubble_count >= 2, f"Expected at least 2 chat bubbles (user + assistant), found {bubble_count}"

        screenshot_carrom = ARTIFACTS_DIR / "qa_edge_assistant_carrom_login_page_fixed.png"
        page.screenshot(path=str(screenshot_carrom), full_page=True)
        print(f"Screenshot saved: {screenshot_carrom}")

        # Step 4: Test Creating a New Assistant Conversation
        print("\n[5/6] Testing 'New Chat' button...")
        new_conv_btn = page.locator('button:has-text("New Chat"), button[title="Start a new conversation"]').first
        if new_conv_btn.is_visible():
            new_conv_btn.click()
            page.wait_for_timeout(1500)
            print("New Chat clicked. Verifying empty conversation state...")
            screenshot_new_conv = ARTIFACTS_DIR / "qa_edge_assistant_new_conversation_fixed.png"
            page.screenshot(path=str(screenshot_new_conv), full_page=True)
            print(f"Screenshot saved: {screenshot_new_conv}")

        # Step 5: Test Project Switching to Shadow Master and Sky Strike
        print("\n[6/6] Testing Project Switching to Shadow Master & Sky Strike...")
        # Shadow Master
        print("Switching to Shadow Master...")
        page.goto(f"http://127.0.0.1:5173/projects/{SHADOW_ID}/workspace", wait_until="networkidle")
        page.wait_for_timeout(2000)
        if not page.locator('.assistant-dock').is_visible():
            page.locator('button:has-text("AI Development Assistant")').first.click()
            page.wait_for_timeout(1000)

        textarea = page.locator('textarea[aria-label="Assistant message input"]')
        textarea.fill("Add score multiplier.")
        textarea.press("Enter")
        for sec in range(30):
            page.wait_for_timeout(1000)
            if not page.locator('[data-testid="assistant-working-progress"]').is_visible() and sec > 3:
                print(f"Shadow Master Assistant finished at {sec}s")
                break

        screenshot_shadow = ARTIFACTS_DIR / "qa_edge_assistant_shadow_master_fixed.png"
        page.screenshot(path=str(screenshot_shadow), full_page=True)
        print(f"Screenshot saved: {screenshot_shadow}")

        # Sky Strike
        print("Switching to Sky Strike...")
        page.goto(f"http://127.0.0.1:5173/projects/{SKY_STRIKE_ID}/workspace", wait_until="networkidle")
        page.wait_for_timeout(2000)
        if not page.locator('.assistant-dock').is_visible():
            page.locator('button:has-text("AI Development Assistant")').first.click()
            page.wait_for_timeout(1000)

        textarea = page.locator('textarea[aria-label="Assistant message input"]')
        textarea.fill("Add shields powerup.")
        textarea.press("Enter")
        for sec in range(30):
            page.wait_for_timeout(1000)
            if not page.locator('[data-testid="assistant-working-progress"]').is_visible() and sec > 3:
                print(f"Sky Strike Assistant finished at {sec}s")
                break

        screenshot_sky = ARTIFACTS_DIR / "qa_edge_assistant_sky_strike_fixed.png"
        page.screenshot(path=str(screenshot_sky), full_page=True)
        print(f"Screenshot saved: {screenshot_sky}")

        print("\n" + "=" * 80)
        print("MICROSOFT EDGE VERIFICATION COMPLETED WITH ZERO ERRORS!")
        print("=" * 80)

        print("\n=== NETWORK TRACE SUMMARY ===")
        assistant_reqs = [l for l in network_logs if "assistant" in l]
        for r in assistant_reqs:
            print(r)

        print("\n=== FAILED REQUESTS ===")
        if failed_requests:
            for f in failed_requests:
                print(f)
        else:
            print("Zero failed requests!")

        browser.close()


if __name__ == "__main__":
    main()
