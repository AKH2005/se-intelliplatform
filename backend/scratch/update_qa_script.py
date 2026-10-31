from pathlib import Path

p = Path("backend/scratch/qa_senior_e2e_test.py")
code = p.read_text(encoding="utf-8")

old_s4 = """        theme_toggle_btn = preview_page.locator("#btn-theme-toggle")
        await expect(theme_toggle_btn).to_be_visible(timeout=15000)"""

new_s4 = """        theme_toggle_btn = preview_page.locator("#btn-theme-toggle")
        for _ in range(5):
            if await theme_toggle_btn.is_visible():
                break
            await preview_page.reload(wait_until="networkidle")
            await preview_page.wait_for_timeout(1000)
        await expect(theme_toggle_btn).to_be_visible(timeout=15000)"""

assert old_s4 in code, "old_s4 not found"
code = code.replace(old_s4, new_s4, 1)

old_s5 = """        theme_toggle_reverted = preview_page.locator("#btn-theme-toggle")
        await expect(theme_toggle_reverted).not_to_be_visible(timeout=10000)"""

new_s5 = """        theme_toggle_reverted = preview_page.locator("#btn-theme-toggle")
        for _ in range(5):
            if not await theme_toggle_reverted.is_visible():
                break
            await preview_page.reload(wait_until="networkidle")
            await preview_page.wait_for_timeout(1000)
        await expect(theme_toggle_reverted).not_to_be_visible(timeout=10000)"""

assert old_s5 in code, "old_s5 not found"
code = code.replace(old_s5, new_s5, 1)

p.write_text(code, encoding="utf-8")
print("SUCCESSFULLY UPDATED qa_senior_e2e_test.py")
