import time
from pathlib import Path
from playwright.sync_api import sync_playwright

ARTIFACTS_DIR = Path(r"C:\Users\DELL\.gemini\antigravity\brain\3ff4955b-2849-4bb9-bc69-ab8ba87f7a5c\qa_screenshots")

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 800})
    page.goto("http://127.0.0.1:8001/preview?project_id=68289eab-12f4-4602-a4b7-143f29c52c58", wait_until="networkidle")
    page.wait_for_timeout(1000)

    # Click the login button
    btn = page.locator('#btn-open-login')
    if btn.is_visible():
        btn.click()
        page.wait_for_timeout(1000)

    # Fill password to show password strength meter
    pwd_input = page.locator('#auth-password')
    if pwd_input.is_visible():
        pwd_input.fill("ShadowMaster#2026!")
        page.wait_for_timeout(500)

    modal_ss = ARTIFACTS_DIR / "qa_edge_preview_login_modal.png"
    page.screenshot(path=str(modal_ss), full_page=True)
    print("Saved preview modal screenshot:", modal_ss)
    browser.close()
