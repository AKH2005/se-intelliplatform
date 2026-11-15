import asyncio
import os
import sys
from playwright.async_api import async_playwright

async def run_platform_ui_verification():
    screenshot_dir = r"C:\Users\DELL\.gemini\antigravity\brain\3ff4955b-2849-4bb9-bc69-ab8ba87f7a5c\qa_screenshots"
    os.makedirs(screenshot_dir, exist_ok=True)

    async with async_playwright() as p:
        browser = None
        try:
            browser = await p.chromium.launch(channel="msedge", headless=True)
            print("Launched Microsoft Edge browser successfully.")
        except Exception as e:
            print("Edge launch fallback to chromium:", e)
            browser = await p.chromium.launch(headless=True)

        context = await browser.new_context(viewport={"width": 1440, "height": 960})
        page = await context.new_page()

        print("Navigating to User Mode Workspace: http://localhost:5173/user")
        await page.goto("http://localhost:5173/user", wait_until="domcontentloaded", timeout=15000)
        await asyncio.sleep(2.0)

        # Look for project selector or projects list
        proj_select = page.locator("select")
        if await proj_select.count() > 0:
            options = await proj_select.locator("option").all_inner_texts()
            print("Available projects in workspace selector:", options)
            for opt in options:
                if "Sky Strike" in opt:
                    print(f"Selecting project option: {opt}")
                    await proj_select.select_option(label=opt)
                    await asyncio.sleep(2.0)
                    break

        # Check for Live Preview tab if tabs exist
        preview_tab = page.locator("button:has-text('Preview'), [role='tab']:has-text('Preview')")
        if await preview_tab.count() > 0:
            await preview_tab.first.click()
            await asyncio.sleep(1.0)

        # Inspect iframe src
        iframe_elem = page.locator("iframe")
        if await iframe_elem.count() > 0:
            src = await iframe_elem.first.get_attribute("src")
            print(f"Platform Preview iframe src: {src}")
            assert "6ab754dc" in (src or "") or "sky-strike" in (src or ""), f"Iframe src missing Sky Strike ID: {src}"
            assert "app=shadow_master" not in (src or ""), f"Iframe src contains corrupted query param app=shadow_master: {src}"
            print("✅ Verified: Iframe src is clean and correctly targets Sky Strike without stale app overrides!")

        # Take screenshot of platform workspace
        shot_path = os.path.join(screenshot_dir, "qa_sky_strike_platform_workspace.png")
        await page.screenshot(path=shot_path, full_page=True)
        print(f"📸 Saved platform workspace screenshot: {shot_path}")

        await browser.close()
        print(">>> PLATFORM UI VERIFICATION COMPLETED SUCCESSFULLY! <<<")

if __name__ == "__main__":
    asyncio.run(run_platform_ui_verification())
