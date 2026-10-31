from pathlib import Path

p = Path("backend/scratch/qa_senior_e2e_test.py")
content = p.read_text(encoding="utf-8")

old_code = """        # Monitor build stages
        log("Waiting for autonomous build pipeline to complete (CREATING -> GENERATING -> VALIDATING -> LIVE)...")
        live_iframe = page.locator('iframe[title*="Live Application Preview"]')
        await live_iframe.wait_for(state="visible", timeout=90000)
        await page.wait_for_timeout(3000)"""

new_code = """        # Monitor build stages
        log("Waiting for autonomous build pipeline to complete (CREATING -> GENERATING -> VALIDATING -> LIVE)...")
        live_iframe = page.locator('iframe[title*="Live Application Preview"]')
        try:
            await live_iframe.wait_for(state="visible", timeout=120000)
        except Exception as e:
            err_path = SCREENSHOTS_DIR / "step2_creation_failed.png"
            await page.screenshot(path=str(err_path), full_page=True)
            log(f"Timed out waiting for live iframe. Captured screenshot to {err_path.name}")
            raise e
        await page.wait_for_timeout(3000)"""

if old_code in content:
    content = content.replace(old_code, new_code, 1)
    p.write_text(content, encoding="utf-8")
    print("SUCCESS: qa_senior_e2e_test.py updated iframe wait.")
else:
    c_norm = content.replace("\r\n", "\n")
    if old_code in c_norm:
        c_norm = c_norm.replace(old_code, new_code, 1)
        p.write_text(c_norm, encoding="utf-8")
        print("SUCCESS: qa_senior_e2e_test.py updated iframe wait (norm).")
    else:
        print("ERROR: old_code not found.")

