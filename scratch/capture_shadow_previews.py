import asyncio
import os
from playwright.async_api import async_playwright

async def capture_previews():
    screenshot_dir = r"C:\Users\DELL\.gemini\antigravity\brain\3ff4955b-2849-4bb9-bc69-ab8ba87f7a5c\qa_screenshots"
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="msedge", headless=True)
        page = await browser.new_page(viewport={"width": 1400, "height": 950})

        # 1. Standalone Live Preview
        await page.goto("http://127.0.0.1:8001/shadow_master", wait_until="networkidle")
        p1 = os.path.join(screenshot_dir, "qa_shadow_master_standalone_preview.png")
        await page.screenshot(path=p1, full_page=True)
        print("Captured standalone preview:", p1)

        # 2. Project preview on port 8001 with project_id
        await page.goto("http://127.0.0.1:8001/?project_id=b9a73557-04a6-4db5-9056-10884a2d5d53", wait_until="networkidle")
        p2 = os.path.join(screenshot_dir, "qa_shadow_master_backend_endpoint_preview.png")
        await page.screenshot(path=p2, full_page=True)
        print("Captured project preview:", p2)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(capture_previews())
