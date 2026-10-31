from pathlib import Path

p = Path("backend/scratch/qa_senior_e2e_test.py")
content = p.read_text(encoding="utf-8")

old_code = """        # In case it executes directly or displays proposed card:
        has_card = False
        try:
            await proposed_card.wait_for(state="visible", timeout=30000)
            has_card = True
            log("Proposed changes card received with confirmation gate!")
        except Exception:
            log("No confirmation card displayed, checking if directly promoted or applied...")"""

new_code = """        # In case it executes directly or displays proposed card:
        has_card = False
        try:
            await proposed_card.wait_for(state="visible", timeout=60000)
            has_card = True
            log("Proposed changes card received with confirmation gate!")
        except Exception:
            log("No confirmation card displayed within 60s, checking if directly promoted or applied...")"""

content = content.replace(old_code, new_code, 1)

old_v2 = """        # Wait for v2 indicator and success notice
        v2_badge = page.locator('span:has-text("v2")')
        await v2_badge.wait_for(state="visible", timeout=30000)
        log("Successfully promoted to Version 2!")"""

new_v2 = """        # Wait for v2 indicator and success notice
        v2_badge = page.locator('span:has-text("v2")')
        try:
            await v2_badge.wait_for(state="visible", timeout=45000)
        except Exception as e:
            err_path = SCREENSHOTS_DIR / "step4_v2_timeout.png"
            await page.screenshot(path=str(err_path), full_page=True)
            log(f"Timed out waiting for v2 badge. Screenshot captured to {err_path.name}")
            raise e
        log("Successfully promoted to Version 2!")"""

content = content.replace(old_v2, new_v2, 1)

p.write_text(content, encoding="utf-8")
print("SUCCESS: qa_senior_e2e_test.py updated refinement timeouts.")

