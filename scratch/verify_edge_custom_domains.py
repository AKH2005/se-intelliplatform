import asyncio
import os
import sys
import urllib.parse
from playwright.async_api import async_playwright

async def run_edge_custom_domain_verification():
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
        # 1. MEDICAL / HEALTHCARE APPLICATION
        # -------------------------------------------------------------
        print("\n--- 1. Testing Medical Application ---")
        try:
            url = "http://127.0.0.1:8001/custom?name=" + urllib.parse.quote("MediCare Clinical Health Portal") + "&desc=" + urllib.parse.quote("Electronic medical records and patient clinic tracker")
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(500)
            title = await page.title()
            content = await page.content()
            assert "MediCare" in title or "Health" in title, f"Unexpected title: {title}"
            assert "Patient" in content
            assert "Prescription" in content or "Clinical" in content or "Admit" in content
            assert "Interactive Application Playground" not in content
            assert "spawnFood" not in content

            # Click Admit Patient modal button
            admit_btn = page.locator("button:has-text('Admit Patient'), button:has-text('New Patient'), button:has-text('Add Patient')").first
            if await admit_btn.count() > 0:
                await admit_btn.click()
                await page.wait_for_timeout(300)

            shot_path = os.path.join(screenshot_dir, "qa_custom_medical_interactive.png")
            await page.screenshot(path=shot_path)
            print(f"PASS: Medical application verified. Screenshot: {shot_path}")
            results.append(("Medical Application", "PASS", shot_path))
        except Exception as e:
            print(f"FAIL: Medical Application -> {e}")
            results.append(("Medical Application", f"FAIL: {e}", ""))

        # -------------------------------------------------------------
        # 2. MUSIC PLAYER APPLICATION
        # -------------------------------------------------------------
        print("\n--- 2. Testing Music Player Application ---")
        try:
            url = "http://127.0.0.1:8001/custom?name=" + urllib.parse.quote("SoundWave Studio Music Player") + "&desc=" + urllib.parse.quote("Digital audio streaming playlist and equalizer deck")
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(500)
            title = await page.title()
            content = await page.content()
            assert "SoundWave" in title or "Music" in title, f"Unexpected title: {title}"
            assert "Playlist" in content or "Track" in content
            assert "Play" in content or "Equalizer" in content
            assert "Interactive Application Playground" not in content

            # Click play/pause button or a track item
            play_btn = page.locator("button:has-text('Play'), #playBtn, .play-btn, button:has-text('▶')").first
            if await play_btn.count() > 0:
                await play_btn.click()
                await page.wait_for_timeout(300)

            shot_path = os.path.join(screenshot_dir, "qa_custom_music_interactive.png")
            await page.screenshot(path=shot_path)
            print(f"PASS: Music Player verified. Screenshot: {shot_path}")
            results.append(("Music Player", "PASS", shot_path))
        except Exception as e:
            print(f"FAIL: Music Player -> {e}")
            results.append(("Music Player", f"FAIL: {e}", ""))

        # -------------------------------------------------------------
        # 3. FOOD DELIVERY APPLICATION
        # -------------------------------------------------------------
        print("\n--- 3. Testing Food Delivery Application ---")
        try:
            url = "http://127.0.0.1:8001/custom?name=" + urllib.parse.quote("CraveDrop Food Delivery") + "&desc=" + urllib.parse.quote("Restaurant menu ordering cart and realtime delivery tracker")
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(500)
            title = await page.title()
            content = await page.content()
            assert "CraveDrop" in title or "Food" in title or "Delivery" in title
            assert "Menu" in content or "Burger" in content or "Pizza" in content
            assert "Cart" in content or "Delivery Tracker" in content
            assert "Interactive Application Playground" not in content

            # Click Add to Cart button
            add_btn = page.locator("button:has-text('Add to Cart'), button:has-text('Order Now'), .add-to-cart").first
            if await add_btn.count() > 0:
                await add_btn.click()
                await page.wait_for_timeout(300)

            shot_path = os.path.join(screenshot_dir, "qa_custom_food_interactive.png")
            await page.screenshot(path=shot_path)
            print(f"PASS: Food Delivery verified. Screenshot: {shot_path}")
            results.append(("Food Delivery", "PASS", shot_path))
        except Exception as e:
            print(f"FAIL: Food Delivery -> {e}")
            results.append(("Food Delivery", f"FAIL: {e}", ""))

        # -------------------------------------------------------------
        # 4. LEARNING MANAGEMENT SYSTEM (LMS)
        # -------------------------------------------------------------
        print("\n--- 4. Testing Learning Management System (LMS) ---")
        try:
            url = "http://127.0.0.1:8001/custom?name=" + urllib.parse.quote("EduMaster Learning Management System") + "&desc=" + urllib.parse.quote("Online course curriculum modules and quiz platform")
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(500)
            title = await page.title()
            content = await page.content()
            assert "EduMaster" in title or "Learning" in title or "LMS" in title
            assert "Course" in content or "Curriculum" in content or "Module" in content
            assert "Interactive Application Playground" not in content

            # Click Start Course or Next Module button
            learn_btn = page.locator("button:has-text('Start Course'), button:has-text('Resume Lesson'), button:has-text('View Module')").first
            if await learn_btn.count() > 0:
                await learn_btn.click()
                await page.wait_for_timeout(300)

            shot_path = os.path.join(screenshot_dir, "qa_custom_lms_interactive.png")
            await page.screenshot(path=shot_path)
            print(f"PASS: Learning Management System verified. Screenshot: {shot_path}")
            results.append(("LMS", "PASS", shot_path))
        except Exception as e:
            print(f"FAIL: LMS -> {e}")
            results.append(("LMS", f"FAIL: {e}", ""))

        await browser.close()

    print("\n=== SUMMARY OF CUSTOM DOMAIN VERIFICATION ===")
    all_ok = True
    for name, st, path in results:
        print(f"[{st}] {name} -> {path}")
        if "FAIL" in st:
            all_ok = False

    if all_ok:
        print("\nALL CUSTOM APPLICATION DOMAINS VERIFIED SUCCESSFULLY IN BROWSER!")
    else:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_edge_custom_domain_verification())