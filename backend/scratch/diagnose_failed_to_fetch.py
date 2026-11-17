import sys
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

backend_dir = r"c:\Users\DELL\OneDrive\Documents\SE Intellplatform\backend"
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.security import create_access_token

USER_ID = "4efd163c-cd5d-483c-89c8-0d40e43ff3eb"  # madanuakhil07@gmail.com
AUTH_TOKEN = create_access_token({"sub": USER_ID})
CARROM_ID = "657e9d2a-4dd2-4fe9-9bb7-20717c43b588"

def main():
    print("Launching Edge with full network and console interception...")
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        requests_log = []
        failed_requests = []
        console_messages = []

        page.on("console", lambda msg: console_messages.append(f"[{msg.type}] {msg.text}"))
        page.on("request", lambda req: requests_log.append(f"--> {req.method} {req.url}"))
        page.on("requestfailed", lambda req: failed_requests.append(f"FAILED: {req.method} {req.url} - {req.failure}"))
        page.on("response", lambda res: requests_log.append(f"<-- {res.status} {res.url}"))

        print("Navigating to local frontend...")
        page.goto("http://127.0.0.1:5173/", wait_until="networkidle")
        page.evaluate(f"""() => {{
            localStorage.setItem('se_auth_token', '{AUTH_TOKEN}');
            localStorage.setItem('se_platform_mode', 'developer');
            localStorage.setItem('se_platform_mode_remember', 'true');
            localStorage.setItem('se_active_project_id', '{CARROM_ID}');
        }}""")

        print(f"Navigating to Carrom Master workspace: /projects/{CARROM_ID}/workspace ...")
        page.goto(f"http://127.0.0.1:5173/projects/{CARROM_ID}/workspace", wait_until="networkidle")
        page.wait_for_timeout(2000)

        # Open Assistant Dock if needed
        assistant_dock = page.locator('.assistant-dock')
        if not assistant_dock.is_visible():
            btn = page.locator('button:has-text("AI Development Assistant")').first
            if btn.is_visible():
                btn.click()
                page.wait_for_timeout(1000)

        # Check API base URL evaluated in frontend window
        base_url_info = page.evaluate("""() => {
            return {
                origin: window.location.origin,
                protocol: window.location.protocol,
                localStorageToken: localStorage.getItem('se_auth_token') ? 'PRESENT' : 'MISSING',
            };
        }""")
        print("Frontend window info:", json.dumps(base_url_info, indent=2))

        print("Entering prompt: 'Add a login page.'")
        textarea = page.locator('textarea[aria-label="Assistant message input"]')
        if textarea.is_visible():
            textarea.fill("Add a login page.")
            textarea.press("Enter")
            print("Message sent, waiting for streaming or errors...")

            for i in range(15):
                page.wait_for_timeout(1000)
                error_banner = page.locator('[data-testid="assistant-error-banner"]')
                if error_banner.is_visible():
                    print(f"Detected error banner at second {i}: {error_banner.inner_text()}")
                    break
                is_working = page.locator('[data-testid="assistant-working-progress"]').is_visible()
                if not is_working and i > 3:
                    print(f"Assistant finished at second {i}")
                    break
        else:
            print("ERROR: Textarea not visible!")

        print("\n=== RECENT NETWORK EVENTS ===")
        for r in requests_log[-20:]:
            print(r)

        print("\n=== FAILED REQUESTS ===")
        for f in failed_requests:
            print(f)

        print("\n=== CONSOLE LOGS ===")
        for c in console_messages[-25:]:
            print(c)

        browser.close()

if __name__ == "__main__":
    main()
