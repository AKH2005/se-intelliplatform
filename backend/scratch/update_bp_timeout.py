from pathlib import Path

p = Path("backend/scratch/qa_senior_e2e_test.py")
content = p.read_text(encoding="utf-8")

old_console = """        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()

        # Step 2.1: Login"""

new_console = """        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()
        page.on("console", lambda msg: log(f"BROWSER: [{msg.type}] {msg.text}"))
        page.on("pageerror", lambda err: log(f"BROWSER ERROR: {err}"))

        # Step 2.1: Login"""

content = content.replace(old_console, new_console, 1)

old_bp = """        # Wait for blueprint section
        create_now_btn = page.locator('button:has-text("Create Application Now")')
        await create_now_btn.wait_for(state="visible", timeout=30000)
        log("Blueprint generated successfully!")"""

new_bp = """        # Wait for blueprint section
        create_now_btn = page.locator('button:has-text("Create Application Now")')
        try:
            await create_now_btn.wait_for(state="visible", timeout=60000)
        except Exception as e:
            err_path = SCREENSHOTS_DIR / "step2_blueprint_timeout.png"
            await page.screenshot(path=str(err_path), full_page=True)
            log(f"Timed out waiting for blueprint card. Screenshot captured to {err_path.name}")
            raise e
        log("Blueprint generated successfully!")"""

content = content.replace(old_bp, new_bp, 1)

p.write_text(content, encoding="utf-8")
print("SUCCESS: qa_senior_e2e_test.py updated with console logging and 60s blueprint timeout.")

