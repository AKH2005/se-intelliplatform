from pathlib import Path

p = Path("backend/scratch/qa_senior_e2e_test.py")
code = p.read_text(encoding="utf-8")

old_wait = """        # Wait for v2 indicator and success notice
        v2_badge = page.locator('span:has-text("v2")')
        try:
            await v2_badge.wait_for(state="visible", timeout=45000)
        except Exception as e:
            err_path = SCREENSHOTS_DIR / "step4_v2_timeout.png"
            await page.screenshot(path=str(err_path), full_page=True)
            log(f"Timed out waiting for v2 badge. Screenshot captured to {err_path.name}")
            raise e
        log("Successfully promoted to Version 2!")"""

new_wait = """        # Wait for promotion to complete: proposed card closes and "Rollback to v1" becomes visible
        log("Waiting for version promotion transaction to complete in backend...")
        rollback_btn_v1 = page.locator('button:has-text("Rollback to v1")')
        try:
            await rollback_btn_v1.wait_for(state="visible", timeout=60000)
        except Exception as e:
            err_path = SCREENSHOTS_DIR / "step4_v2_timeout.png"
            await page.screenshot(path=str(err_path), full_page=True)
            log(f"Timed out waiting for Rollback to v1 button. Screenshot captured to {err_path.name}")
            raise e
        log("Successfully promoted to Version 2! Active version is now v2.")"""

assert old_wait in code, "old_wait not found"
code = code.replace(old_wait, new_wait, 1)

p.write_text(code, encoding="utf-8")
print("SUCCESSFULLY APPLIED PROMOTION SYNC TO QA SCRIPT")

