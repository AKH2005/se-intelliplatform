import asyncio
import os
import sys
from playwright.async_api import async_playwright

async def run_edge_verification():
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

        context = await browser.new_context(viewport={"width": 1400, "height": 950})
        page = await context.new_page()

        # =========================================================================
        # 1. VERIFY SKY STRIKE INTERACTIVE PREVIEW
        # =========================================================================
        sky_url = "http://127.0.0.1:8001/preview/6ab754dc-c2bb-4689-9d87-2f69b778527f"
        print(f"\n[1] Navigating to Sky Strike: {sky_url}")
        await page.goto(sky_url, wait_until="networkidle", timeout=15000)

        title = await page.title()
        print(f"  Page Title: {title}")
        assert "Sky Strike" in title, f"Title does not contain Sky Strike: {title}"

        # Assert no cross-project collision markers
        content = await page.content()
        assert "combatCanvas" not in content, "Shadow Master combatCanvas leaked in Sky Strike preview!"
        assert "Katana Slash" not in content, "Shadow Master Katana Slash leaked in Sky Strike preview!"
        assert "spawnFood" not in content, "Snake spawnFood leaked in Sky Strike preview!"
        assert "new-task-input" not in content, "Kanban new-task-input leaked in Sky Strike preview!"

        # Verify Canvas presence and dimensions
        canvas = page.locator("canvas#skyStrikeCanvas")
        await canvas.wait_for(state="visible", timeout=5000)
        box = await canvas.bounding_box()
        print(f"  Sky Strike Flight Canvas dimensions: {box['width']}x{box['height']}")
        assert box['width'] >= 600 and box['height'] >= 350, "Invalid Canvas dimensions!"

        # Verify HUD and Telemetry
        hud_elements = ["AIRSPEED", "ALTITUDE", "HULL", "AFTERBURNER", "MISSILES", "SCORE"]
        for elem in hud_elements:
            loc = page.locator(f"text={elem}")
            count = await loc.count()
            print(f"  HUD Element '{elem}' present: {count > 0}")
            assert count > 0, f"Missing HUD element: {elem}"

        # Interact with Aircraft Controls
        # Move flight stick
        await canvas.click(position={"x": int(box['width'] / 2), "y": int(box['height'] / 2)})
        await page.keyboard.press("KeyW")
        await page.keyboard.press("KeyD")
        await page.keyboard.press("KeyS")
        await page.keyboard.press("KeyA")
        await asyncio.sleep(0.3)

        # Fire Vulcan Cannon (Space)
        print("  Firing Vulcan Cannon via Spacebar...")
        await page.keyboard.press("Space")
        await asyncio.sleep(0.2)
        await page.keyboard.press("Space")
        await asyncio.sleep(0.2)

        # Fire Sidewinder Missile (KeyE)
        print("  Launching Sidewinder Missile via E key...")
        await page.keyboard.press("KeyE")
        await asyncio.sleep(0.3)

        # Engage Afterburner boost (Shift)
        print("  Engaging Afterburner boost...")
        await page.keyboard.down("ShiftLeft")
        await page.keyboard.press("KeyW")
        await page.keyboard.up("ShiftLeft")
        await asyncio.sleep(0.3)

        # Cycle Dynamic Weather Mode to Thunderstorm
        thunder_btn = page.locator(".btn-weather:has-text('Thunderstorm')")
        if await thunder_btn.count() > 0:
            print("  Switching Dynamic Weather to Thunderstorm...")
            await thunder_btn.click()
            await asyncio.sleep(0.4)

        # Upgrade Hangar Interaction (Click first +UPGRADE button)
        upgrade_btn = page.locator(".btn-upgrade")
        if await upgrade_btn.count() > 0:
            print("  Applying Aircraft Upgrade Hangar improvement (+UPGRADE)...")
            await upgrade_btn.first.click()
            await asyncio.sleep(0.3)

        shot1_path = os.path.join(screenshot_dir, "qa_sky_strike_interactive.png")
        await page.screenshot(path=shot1_path, full_page=True)
        print(f"  📸 Saved screenshot: {shot1_path}")

        # =========================================================================
        # 2. VERIFY URL OVERRIDE IMMUNITY (ANTI-COLLISION IN BROWSER)
        # =========================================================================
        polluted_url = "http://127.0.0.1:8001/preview?project_id=6ab754dc-c2bb-4689-9d87-2f69b778527f&app=shadow_master"
        print(f"\n[2] Testing URL Override Immunity with polluted query: {polluted_url}")
        await page.goto(polluted_url, wait_until="networkidle", timeout=15000)

        polluted_content = await page.content()
        assert "skyStrikeCanvas" in polluted_content, "Sky Strike canvas missing under app=shadow_master query!"
        assert "combatCanvas" not in polluted_content, "Cross-project collision! Shadow Master canvas rendered!"
        assert "Katana Slash" not in polluted_content, "Cross-project collision! Katana Slash rendered!"

        shot2_path = os.path.join(screenshot_dir, "qa_sky_strike_url_immunity.png")
        await page.screenshot(path=shot2_path, full_page=True)
        print(f"  📸 Saved screenshot: {shot2_path}")

        # =========================================================================
        # 3. VERIFY SWITCHING ISOLATION (SHADOW MASTER -> SKY STRIKE)
        # =========================================================================
        shadow_url = "http://127.0.0.1:8001/preview/b9a73557-04a6-4db5-9056-10884a2d5d53"
        print(f"\n[3] Switching to Shadow Master project: {shadow_url}")
        await page.goto(shadow_url, wait_until="networkidle", timeout=15000)

        shadow_content = await page.content()
        assert "combatCanvas" in shadow_content, "Shadow Master combatCanvas missing!"
        assert "Katana Slash" in shadow_content, "Shadow Master Katana Slash missing!"
        assert "skyStrikeCanvas" not in shadow_content, "Sky Strike leaked into Shadow Master!"

        shot3_path = os.path.join(screenshot_dir, "qa_shadow_master_switch_verification.png")
        await page.screenshot(path=shot3_path, full_page=True)
        print(f"  📸 Saved screenshot: {shot3_path}")

        # Switch back to Sky Strike to verify zero persistence/cache pollution
        print(f"\n[4] Switching back to Sky Strike project: {sky_url}")
        await page.goto(sky_url, wait_until="networkidle", timeout=15000)

        back_content = await page.content()
        assert "skyStrikeCanvas" in back_content, "Sky Strike canvas missing on switch-back!"
        assert "combatCanvas" not in back_content, "Shadow Master leaked into Sky Strike on switch-back!"

        shot4_path = os.path.join(screenshot_dir, "qa_sky_strike_switch_back_clean.png")
        await page.screenshot(path=shot4_path, full_page=True)
        print(f"  📸 Saved screenshot: {shot4_path}")

        await browser.close()
        print("\n>>> ALL PLAYWRIGHT EDGE VERIFICATION TESTS PASSED SUCCESSFULLY! <<<")

if __name__ == "__main__":
    asyncio.run(run_edge_verification())
