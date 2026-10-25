"""Capture authentic screenshots for 36, 37, and 39."""
from pathlib import Path
from playwright.sync_api import sync_playwright

ARTIFACTS_DIR = Path(r"C:\Users\DELL\.gemini\antigravity-ide\brain\922d928e-a9d5-49ee-bd75-1a72d9ef9507")

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=False, slow_mo=300)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto("http://localhost:5173", wait_until="networkidle")
        page.wait_for_timeout(2000)

        # Select TaskFlow project
        proj_sel = page.locator('select[aria-label="Select active project"]')
        options = page.locator('select[aria-label="Select active project"] option')
        taskflow_val = None
        for i in range(options.count()):
            opt_text = options.nth(i).inner_text()
            if "TaskFlow" in opt_text:
                taskflow_val = options.nth(i).get_attribute("value")
                break
        if taskflow_val:
            proj_sel.select_option(taskflow_val)
            page.wait_for_timeout(1500)

        # Go to Environments
        page.click('aside button:has-text("Environments")')
        page.wait_for_timeout(2000)

        # 1. Deploy Modal (36)
        deploy_btn = page.locator('button:has-text("Deploy")').first
        if deploy_btn.is_visible() and deploy_btn.is_enabled():
            deploy_btn.click()
            page.wait_for_timeout(800)
            
            # Select first version in modal dropdown
            v_select = page.locator('.modal-body select, select.input')
            if v_select.is_visible():
                opts = v_select.locator('option')
                if opts.count() > 1:
                    v_select.select_option(index=1)
                    page.wait_for_timeout(500)

            page.screenshot(path=str(ARTIFACTS_DIR / "36_deploy_to_development.png"), full_page=True)
            print("Captured 36_deploy_to_development")

            # Deploy it
            confirm_btn = page.locator('.modal-footer button:has-text("Deploy Version")')
            if confirm_btn.is_visible() and confirm_btn.is_enabled():
                confirm_btn.click()
                print("Deployed version to DEVELOPMENT.")
                page.wait_for_timeout(2500)
            else:
                page.locator('.modal-footer button:has-text("Cancel")').click()
                page.wait_for_timeout(500)

        # 2. Promote Modal (37)
        promote_btn = page.locator('button:has-text("Promote")').first
        if promote_btn.is_visible() and promote_btn.is_enabled():
            promote_btn.click()
            page.wait_for_timeout(1000)
            page.screenshot(path=str(ARTIFACTS_DIR / "37_promote_to_staging.png"), full_page=True)
            print("Captured 37_promote_to_staging")
            cancel_btn = page.locator('.modal-footer button:has-text("Cancel")')
            if cancel_btn.is_visible():
                cancel_btn.click()
                page.wait_for_timeout(500)
        else:
            page.screenshot(path=str(ARTIFACTS_DIR / "37_promote_to_staging.png"), full_page=True)
            print("Captured 37_promote_to_staging (env view)")

        # 3. Rollback Modal (39)
        rollback_btn = page.locator('button:has-text("Rollback")').first
        if rollback_btn.is_visible() and rollback_btn.is_enabled():
            rollback_btn.click()
            page.wait_for_timeout(1000)
            page.screenshot(path=str(ARTIFACTS_DIR / "39_rollback_environment.png"), full_page=True)
            print("Captured 39_rollback_environment")
            cancel_btn = page.locator('.modal-footer button:has-text("Cancel")')
            if cancel_btn.is_visible():
                cancel_btn.click()
                page.wait_for_timeout(500)
        else:
            page.screenshot(path=str(ARTIFACTS_DIR / "39_rollback_environment.png"), full_page=True)
            print("Captured 39_rollback_environment (env view)")

        browser.close()
        print("Done!")

if __name__ == "__main__":
    main()
