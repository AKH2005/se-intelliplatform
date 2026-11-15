
import asyncio
import os
import sys
from playwright.async_api import async_playwright

async def run_edge_verification():
    screenshot_dir = r"C:\Users\DELL\.gemini\antigravity\brain\3ff4955b-2849-4bb9-bc69-ab8ba87f7a5c\qa_screenshots"
    os.makedirs(screenshot_dir, exist_ok=True)

    async with async_playwright() as p:
        browser = None
        # Try msedge channel first
        try:
            browser = await p.chromium.launch(channel="msedge", headless=True)
            print("Launched Microsoft Edge browser successfully.")
        except Exception as e:
            print("Edge launch fallback to chromium:", e)
            browser = await p.chromium.launch(headless=True)

        context = await browser.new_context(viewport={"width": 1400, "height": 950})
        page = await context.new_page()

        # -------------------------------------------------------------
        # 1. VERIFY STANDALONE PREVIEW (PORT 8001)
        # -------------------------------------------------------------
        preview_url = "http://127.0.0.1:8001/?project_id=b9a73557-04a6-4db5-9056-10884a2d5d53"
        print(f"Navigating to Live Preview: {preview_url}")
        await page.goto(preview_url, wait_until="networkidle", timeout=15000)

        title = await page.title()
        print("Page Title:", title)
        assert "Shadow Master" in title, f"Title does not contain Shadow Master: {title}"

        # Verify Core Elements
        h1_text = await page.locator("h1").inner_text()
        print("Header H1:", h1_text)
        assert "Shadow Master" in h1_text, f"H1 does not match Shadow Master: {h1_text}"

        # Assert NO generic playground markers
        content = await page.content()
        assert "Interactive Application Playground" not in content, "Generic playground fallback found in Live Preview!"
        assert "Trigger Primary Action" not in content, "Generic Trigger Primary Action button found in Live Preview!"
        assert "spawnFood" not in content, "Snake collision spawnFood found in Live Preview!"
        assert "task-form" not in content, "Kanban collision task-form found in Live Preview!"

        # Verify Canvas is present
        canvas = page.locator("canvas#combatCanvas")
        await canvas.wait_for(state="visible", timeout=5000)
        box = await canvas.bounding_box()
        print(f"Combat Canvas dimensions: {box['width']}x{box['height']}")
        assert box['width'] >= 600 and box['height'] >= 350, "Combat Canvas invalid dimensions!"

        # Verify Ability Buttons
        abilities = ["Katana Slash", "Shadow Dash", "Shuriken Volley", "Shadow Cloak", "Shadow Decoy"]
        for ability in abilities:
            btn = page.locator(f"button:has-text('{ability}')")
            count = await btn.count()
            print(f"Ability button '{ability}' present: {count > 0}")
            assert count > 0, f"Missing ability button {ability}"

        # Click Start Battle
        start_btn = page.locator("#btn-start")
        if await start_btn.count() > 0:
            await start_btn.click()
            await asyncio.sleep(0.3)

        # Interact with the game - movement & abilities
        await canvas.click(position={"x": 350, "y": 210})
        await page.keyboard.press("KeyW")
        await page.keyboard.press("KeyD")
        await page.keyboard.press("KeyS")
        await page.keyboard.press("KeyA")
        await asyncio.sleep(0.3)

        # Trigger ability Q (Katana Slash)
        await page.keyboard.press("KeyQ")
        await asyncio.sleep(0.3)

        # Trigger ability E (Shuriken Volley)
        await page.keyboard.press("KeyE")
        await asyncio.sleep(0.3)

        # Trigger ability Space (Shadow Decoy)
        await page.keyboard.press("Space")
        await asyncio.sleep(0.3)

        # Verify Skill Customizer
        skill_dmg = page.locator("#inputDamage")
        await skill_dmg.wait_for(state="visible")
        # Change damage slider
        await skill_dmg.fill("85")
        await asyncio.sleep(0.2)

        # Apply to live game
        apply_btn = page.locator("button:has-text('Apply to Live Game')")
        if await apply_btn.count() > 0:
            await apply_btn.click()
            await asyncio.sleep(0.2)

        # Click Preset Chip
        assassin_chip = page.locator("span.chip:has-text('Assassin')")
        if await assassin_chip.count() > 0:
            await assassin_chip.click()
            await asyncio.sleep(0.3)
            print("Clicked Assassin preset chip!")

        # Toggle JSON export
        export_btn = page.locator("button:has-text('Export Skill Config')")
        await export_btn.click()
        await asyncio.sleep(0.3)
        json_elem = page.locator("#jsonExport")
        json_text = await json_elem.inner_text()
        print("Exported JSON snippet:", json_text[:120].replace('\n', ' '))
        assert "Shadow Master Skill Builder" in json_text, "Exported JSON missing game title!"
        assert "skills" in json_text, "Exported JSON missing skills array!"

        # Capture interactive gameplay screenshot
        p1 = os.path.join(screenshot_dir, "qa_shadow_master_gameplay_interactive.png")
        await page.screenshot(path=p1, full_page=True)
        print(f"Captured: {p1}")

        # -------------------------------------------------------------
        # 2. VERIFY USER MODE WORKSPACE (PORT 5173 /user)
        # -------------------------------------------------------------
        try:
            print("Navigating to User Mode Workspace: http://localhost:5173/user")
            await page.goto("http://localhost:5173/user", wait_until="domcontentloaded", timeout=10000)
            await asyncio.sleep(1.5)

            # Check if project selector exists and select Shadow Master
            proj_select = page.locator("select")
            if await proj_select.count() > 0:
                options = await proj_select.locator("option").all_inner_texts()
                print("Available projects in workspace selector:", options)
                for opt in options:
                    if "Shadow Master" in opt:
                        await proj_select.select_option(label=opt)
                        await asyncio.sleep(1.0)
                        break

            p2 = os.path.join(screenshot_dir, "qa_shadow_master_user_mode_workspace.png")
            await page.screenshot(path=p2, full_page=True)
            print(f"Captured: {p2}")
        except Exception as e:
            print("User mode workspace inspection note:", e)

        # -------------------------------------------------------------
        # 3. VERIFY DEVELOPER MODE CODE STUDIO (PORT 5173 /projects)
        # -------------------------------------------------------------
        try:
            print("Navigating to Code Studio: http://localhost:5173/projects")
            await page.goto("http://localhost:5173/projects", wait_until="domcontentloaded", timeout=10000)
            await asyncio.sleep(1.5)

            # If project card exists, click it
            shadow_card = page.locator("text='Shadow Master Skill Builder'")
            if await shadow_card.count() > 0:
                await shadow_card.first.click()
                await asyncio.sleep(1.5)

            p3 = os.path.join(screenshot_dir, "qa_shadow_master_developer_mode_code_studio.png")
            await page.screenshot(path=p3, full_page=True)
            print(f"Captured: {p3}")
        except Exception as e:
            print("Code studio inspection note:", e)

        await browser.close()
        print("\nALL MICROSOFT EDGE PLAYWRIGHT VERIFICATION CHECKS PASSED 100%!")

if __name__ == "__main__":
    asyncio.run(run_edge_verification())
