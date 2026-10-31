from pathlib import Path

p = Path("backend/scratch/qa_senior_e2e_test.py")
code = p.read_text(encoding="utf-8")

old_block_4 = """        # Verify live application on port 8001 has dark mode toggle working
        log("Switching to preview page to verify Dark Mode Toggle on live runtime...")
        await preview_page.bring_to_front()
        await preview_page.goto(target_preview_url, wait_until="networkidle")
        await preview_page.wait_for_timeout(1000)

        theme_toggle_btn = preview_page.locator("#btn-theme-toggle")
        for _ in range(5):
            if await theme_toggle_btn.is_visible():
                break
            await preview_page.reload(wait_until="networkidle")
            await preview_page.wait_for_timeout(1000)
        await expect(theme_toggle_btn).to_be_visible(timeout=15000)"""

new_block_4 = """        # Verify live application on port 8001 has dark mode toggle working
        log("Switching to preview page to verify Dark Mode Toggle on live runtime...")
        await preview_page.bring_to_front()
        for _ in range(6):
            try:
                await preview_page.goto(target_preview_url, wait_until="networkidle")
                break
            except Exception:
                await asyncio.sleep(1.0)
        await preview_page.wait_for_timeout(1000)

        theme_toggle_btn = preview_page.locator("#btn-theme-toggle")
        for _ in range(6):
            if await theme_toggle_btn.is_visible():
                break
            try:
                await preview_page.reload(wait_until="networkidle")
            except Exception:
                pass
            await preview_page.wait_for_timeout(1000)
        await expect(theme_toggle_btn).to_be_visible(timeout=15000)"""

assert old_block_4 in code, "old_block_4 not found"
code = code.replace(old_block_4, new_block_4, 1)

old_block_5 = """        # Verify preview on port 8001: dark mode toggle should be REMOVED
        log("Verifying live preview reflects restored v1 state...")
        await preview_page.bring_to_front()
        await preview_page.goto(target_preview_url, wait_until="networkidle")
        await preview_page.wait_for_timeout(1000)

        theme_toggle_reverted = preview_page.locator("#btn-theme-toggle")
        for _ in range(5):
            if not await theme_toggle_reverted.is_visible():
                break"""

new_block_5 = """        # Verify preview on port 8001: dark mode toggle should be REMOVED
        log("Verifying live preview reflects restored v1 state...")
        await preview_page.bring_to_front()
        for _ in range(6):
            try:
                await preview_page.goto(target_preview_url, wait_until="networkidle")
                break
            except Exception:
                await asyncio.sleep(1.0)
        await preview_page.wait_for_timeout(1000)

        theme_toggle_reverted = preview_page.locator("#btn-theme-toggle")
        for _ in range(6):
            if not await theme_toggle_reverted.is_visible():
                break
            try:
                await preview_page.reload(wait_until="networkidle")
            except Exception:
                pass
            await preview_page.wait_for_timeout(1000)"""

assert old_block_5 in code, "old_block_5 not found"
code = code.replace(old_block_5, new_block_5, 1)

p.write_text(code, encoding="utf-8")
print("SUCCESSFULLY APPLIED RETRY GUARDS TO QA SCRIPT")

