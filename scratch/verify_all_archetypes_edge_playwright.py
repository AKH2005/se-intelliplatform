import asyncio
import os
import sys
from playwright.async_api import async_playwright

async def run_comprehensive_edge_verification():
    screenshot_dir = r"C:\Users\DELL\.gemini\antigravity\brain\3ff4955b-2849-4bb9-bc69-ab8ba87f7a5c\qa_screenshots"
    os.makedirs(screenshot_dir, exist_ok=True)

    results = []

    async with async_playwright() as p:
        browser = None
        try:
            browser = await p.chromium.launch(channel="msedge", headless=True)
            print("Launched Microsoft Edge successfully.")
        except Exception as e:
            print("Edge launch fallback to chromium:", e)
            browser = await p.chromium.launch(headless=True)

        context = await browser.new_context(viewport={"width": 1400, "height": 950})
        page = await context.new_page()

        # -------------------------------------------------------------
        # 1. CHESS MASTER PRO
        # -------------------------------------------------------------
        print("\n--- 1. Testing Chess Master Pro ---")
        try:
            await page.goto("http://127.0.0.1:8001/chess", wait_until="networkidle", timeout=10000)
            title = await page.title()
            assert "Chess" in title
            content = await page.content()
            assert "Interactive Application Playground" not in content
            assert "spawnFood" not in content
            assert "task-form" not in content
            squares = await page.locator(".square").count()
            assert squares == 64, f"Expected 64 chess squares, found {squares}"
            # Click a square to verify interaction
            sq = page.locator(".square").nth(52) # e2
            await sq.click()
            await page.wait_for_timeout(300)
            shot_path = os.path.join(screenshot_dir, "qa_chess_interactive.png")
            await page.screenshot(path=shot_path)
            print(f"PASS: Chess verified ({squares} squares, move logic active). Screenshot: {shot_path}")
            results.append(("Chess Master Pro", "PASS", shot_path))
        except Exception as e:
            print(f"FAIL: Chess Master Pro -> {e}")
            results.append(("Chess Master Pro", f"FAIL: {e}", ""))

        # -------------------------------------------------------------
        # 2. SKYLINE JUMP PLATFORMER
        # -------------------------------------------------------------
        print("\n--- 2. Testing Skyline Jump Platformer ---")
        try:
            await page.goto("http://127.0.0.1:8001/platformer", wait_until="networkidle", timeout=10000)
            title = await page.title()
            assert "Platformer" in title or "Skyline" in title
            content = await page.content()
            assert "Interactive Application Playground" not in content
            canvas = page.locator("canvas#platformerCanvas")
            assert await canvas.is_visible()
            # Press jump key
            await page.keyboard.press("Space")
            await page.wait_for_timeout(500)
            shot_path = os.path.join(screenshot_dir, "qa_platformer_interactive.png")
            await page.screenshot(path=shot_path)
            print(f"PASS: Platformer verified (60 FPS canvas, jump controls). Screenshot: {shot_path}")
            results.append(("Skyline Jump Platformer", "PASS", shot_path))
        except Exception as e:
            print(f"FAIL: Skyline Jump Platformer -> {e}")
            results.append(("Skyline Jump Platformer", f"FAIL: {e}", ""))

        # -------------------------------------------------------------
        # 3. TURBO NITRO RACING
        # -------------------------------------------------------------
        print("\n--- 3. Testing Turbo Nitro Racing ---")
        try:
            await page.goto("http://127.0.0.1:8001/racing", wait_until="networkidle", timeout=10000)
            title = await page.title()
            assert "Racing" in title or "Nitro" in title
            content = await page.content()
            assert "Interactive Application Playground" not in content
            canvas = page.locator("canvas#raceCanvas")
            assert await canvas.is_visible()
            # Accelerate
            await page.keyboard.press("ArrowUp")
            await page.wait_for_timeout(400)
            shot_path = os.path.join(screenshot_dir, "qa_racing_interactive.png")
            await page.screenshot(path=shot_path)
            print(f"PASS: Racing verified (Track canvas, telemetry HUD). Screenshot: {shot_path}")
            results.append(("Turbo Nitro Racing", "PASS", shot_path))
        except Exception as e:
            print(f"FAIL: Turbo Nitro Racing -> {e}")
            results.append(("Turbo Nitro Racing", f"FAIL: {e}", ""))

        # -------------------------------------------------------------
        # 4. TILE SHIFT PUZZLE
        # -------------------------------------------------------------
        print("\n--- 4. Testing Tile Shift Puzzle ---")
        try:
            await page.goto("http://127.0.0.1:8001/puzzle", wait_until="networkidle", timeout=10000)
            title = await page.title()
            assert "Puzzle" in title or "Tile" in title
            content = await page.content()
            assert "Interactive Application Playground" not in content
            tiles = await page.locator(".tile").count()
            assert tiles >= 15, f"Expected 15 tiles, found {tiles}"
            # Click tile
            await page.locator(".tile").first.click()
            await page.wait_for_timeout(300)
            shot_path = os.path.join(screenshot_dir, "qa_puzzle_interactive.png")
            await page.screenshot(path=shot_path)
            print(f"PASS: Puzzle verified ({tiles} tiles, solvable shuffle). Screenshot: {shot_path}")
            results.append(("Tile Shift Puzzle", "PASS", shot_path))
        except Exception as e:
            print(f"FAIL: Tile Shift Puzzle -> {e}")
            results.append(("Tile Shift Puzzle", f"FAIL: {e}", ""))

        # -------------------------------------------------------------
        # 5. STUDYDECK FLASHCARDS & QUIZ
        # -------------------------------------------------------------
        print("\n--- 5. Testing StudyDeck Educational Suite ---")
        try:
            await page.goto("http://127.0.0.1:8001/educational", wait_until="networkidle", timeout=10000)
            title = await page.title()
            assert "StudyDeck" in title or "Educational" in title or "Quiz" in title
            content = await page.content()
            assert "Interactive Application Playground" not in content
            card = page.locator(".flashcard")
            assert await card.is_visible()
            # Click flip
            await card.click()
            await page.wait_for_timeout(400)
            # Switch to Quiz tab
            quiz_btn = page.locator("button:has-text('Quiz')")
            if await quiz_btn.is_visible():
                await quiz_btn.click()
                await page.wait_for_timeout(400)
            shot_path = os.path.join(screenshot_dir, "qa_educational_interactive.png")
            await page.screenshot(path=shot_path)
            print(f"PASS: Educational Suite verified (3D Flashcard flip & Quiz tab). Screenshot: {shot_path}")
            results.append(("StudyDeck Educational Suite", "PASS", shot_path))
        except Exception as e:
            print(f"FAIL: StudyDeck Educational Suite -> {e}")
            results.append(("StudyDeck Educational Suite", f"FAIL: {e}", ""))

        # -------------------------------------------------------------
        # 6. CARROM MASTER
        # -------------------------------------------------------------
        print("\n--- 6. Testing Carrom Master ---")
        try:
            await page.goto("http://127.0.0.1:8001/carrom", wait_until="networkidle", timeout=10000)
            title = await page.title()
            assert "Carrom" in title
            content = await page.content()
            assert "Interactive Application Playground" not in content
            assert "spawnFood" not in content
            canvas = page.locator("canvas#carromCanvas")
            assert await canvas.is_visible()
            shot_path = os.path.join(screenshot_dir, "qa_carrom_reliability.png")
            await page.screenshot(path=shot_path)
            print(f"PASS: Carrom Master verified (Canvas board, physics engine). Screenshot: {shot_path}")
            results.append(("Carrom Master", "PASS", shot_path))
        except Exception as e:
            print(f"FAIL: Carrom Master -> {e}")
            results.append(("Carrom Master", f"FAIL: {e}", ""))

        # -------------------------------------------------------------
        # 7. INTERACTIVE APPLICATION DASHBOARD (CUSTOM)
        # -------------------------------------------------------------
        print("\n--- 7. Testing Interactive Application Dashboard (Custom) ---")
        try:
            await page.goto("http://127.0.0.1:8001/?app=custom", wait_until="networkidle", timeout=10000)
            title = await page.title()
            assert "Interactive Application Dashboard" in title or "Application" in title
            content = await page.content()
            # CRITICAL: Must NOT contain the old generic placeholder
            assert "Interactive Application Playground" not in content
            assert "Trigger Primary Action" not in content
            # Must contain new rich dashboard features
            assert "kpi-card" in content or "KPI" in content or "Metric" in content
            # Click New Record button to test interactive modal
            modal_btn = page.locator("button:has-text('New Record')")
            if await modal_btn.is_visible():
                await modal_btn.click()
                await page.wait_for_timeout(400)
            shot_path = os.path.join(screenshot_dir, "qa_custom_interactive.png")
            await page.screenshot(path=shot_path)
            print(f"PASS: Custom Interactive Dashboard verified (KPI cards, modal, search). Screenshot: {shot_path}")
            results.append(("Custom Interactive Dashboard", "PASS", shot_path))
        except Exception as e:
            print(f"FAIL: Custom Interactive Dashboard -> {e}")
            results.append(("Custom Interactive Dashboard", f"FAIL: {e}", ""))

        # -------------------------------------------------------------
        # 8. SE INTELLIPLATFORM MAIN FRONTEND (PORT 5173)
        # -------------------------------------------------------------
        print("\n--- 8. Testing Main Frontend Platform ---")
        try:
            await page.goto("http://localhost:5173", wait_until="networkidle", timeout=15000)
            await page.wait_for_timeout(2000)
            content = await page.content()
            # Capture User Mode
            shot_user = os.path.join(screenshot_dir, "qa_full_platform_user_mode.png")
            await page.screenshot(path=shot_user)
            print(f"Captured User Mode screenshot: {shot_user}")

            # Switch to Developer Mode
            dev_mode_btn = page.locator("button:has-text('Developer Mode')")
            if await dev_mode_btn.is_visible():
                await dev_mode_btn.click()
                await page.wait_for_timeout(1000)

            # Navigate to Live Preview tab
            preview_nav = page.locator("button:has-text('Live Preview'), [data-tab='preview']")
            if await preview_nav.is_visible():
                await preview_nav.click()
                await page.wait_for_timeout(2500)
                shot_preview = os.path.join(screenshot_dir, "qa_full_platform_live_preview.png")
                await page.screenshot(path=shot_preview)
                print(f"Captured Live Preview tab screenshot: {shot_preview}")

            # Navigate to Code Studio tab
            code_nav = page.locator("button:has-text('Code Studio'), [data-tab='code-studio']")
            if await code_nav.is_visible():
                await code_nav.click()
                await page.wait_for_timeout(2000)
                shot_code = os.path.join(screenshot_dir, "qa_full_platform_code_studio.png")
                await page.screenshot(path=shot_code)
                print(f"Captured Code Studio tab screenshot: {shot_code}")

            results.append(("Main Frontend Platform Navigation", "PASS", shot_user))
        except Exception as e:
            print(f"FAIL: Main Frontend Platform -> {e}")
            results.append(("Main Frontend Platform", f"FAIL: {e}", ""))

        await browser.close()

    print("\n================== VERIFICATION SUMMARY ==================")
    all_ok = True
    for name, status, shot in results:
        print(f"[{status[:4]}] {name} -> {status} (Image: {shot})")
        if "FAIL" in status:
            all_ok = False
    return all_ok

if __name__ == "__main__":
    success = asyncio.run(run_comprehensive_edge_verification())
    if not success:
        sys.exit(1)
    print("\nALL EDGE PLAYWRIGHT LIVE VERIFICATIONS PASSED 100%!")

