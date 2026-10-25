"""Playwright Runner Script Template for Phase 11J (Stage 3).

Generates the self-contained deterministic Python script that executes inside
the isolated Playwright/Chromium container.

Key Security & Isolation Controls:
1. Strict origin routing: any request URL outside allowed_origin is aborted.
2. Allowlisted actions only (click, fill, assert_text, assert_visible, screenshot).
3. Zero arbitrary user code evaluation (no eval, no exec, no page.evaluate with user scripts).
4. Bounded console error capture (max 10 per test, max 1000 chars per message).
5. Bounded network failure capture (max 10 per test, no credentials/cookies persisted).
6. Bounded screenshot capture directly into mounted workspace.
7. Produces deterministic structured JSON output (/workspace/results.json).
"""

RUNNER_SCRIPT = """# Safe deterministic Playwright test runner executed inside browser container
import asyncio
import json
import os
import sys
import time
from pathlib import Path

async def run_smoke_suite():
    config_path = Path("/workspace/config.json")
    if not config_path.exists():
        print(f"ERROR: Config file {config_path} missing", file=sys.stderr)
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    base_url = config.get("base_url", "").rstrip("/")
    allowed_origin = config.get("allowed_origin", "").rstrip("/")
    tests = config.get("tests", [])
    limits = config.get("limits", {})

    page_timeout = float(limits.get("page_load_timeout_seconds", 15.0)) * 1000.0
    action_timeout = float(limits.get("action_timeout_seconds", 5.0)) * 1000.0

    screenshots_dir = Path("/workspace/screenshots")
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    results = []

    try:
        from playwright.async_api import async_playwright, ConsoleMessage, Request, Response
    except ImportError as ie:
        print(f"ERROR: Playwright import failed: {ie}", file=sys.stderr)
        with open("/workspace/results.json", "w", encoding="utf-8") as out_fp:
            json.dump({"error": f"Playwright not available: {ie}", "test_cases": []}, out_fp)
        sys.exit(2)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-setuid-sandbox",
                "--no-zygote",
            ],
        )

        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            ignore_https_errors=True,
        )

        for test in tests:
            test_id = test.get("test_id", "unknown_test")
            test_name = test.get("name", test_id)
            target_path = test.get("target_path", "/")
            if not target_path.startswith("/"):
                target_path = "/" + target_path

            target_url = f"{base_url}{target_path}"
            expected_status = test.get("expected_status", 200)
            expected_elements = test.get("expected_elements", ["body"])
            expected_title = test.get("expected_title_contains")
            interactions = test.get("interactions", [])
            capture_screenshot = test.get("capture_screenshot", True)

            console_errors = []
            network_records = []
            test_status = "PASSED"
            failed_step = None
            assertion_summary = ""
            test_screenshots = []
            start_time = time.monotonic()

            page = await context.new_page()

            # 1. Console listener
            def handle_console(msg: ConsoleMessage):
                if msg.type in ("error", "warning"):
                    if len(console_errors) < 10:
                        console_errors.append({
                            "level": msg.type,
                            "message": msg.text[:1000],
                            "source": msg.location.get("url") if msg.location else None,
                            "line_number": msg.location.get("lineNumber") if msg.location else None,
                        })
            page.on("console", handle_console)

            # 2. Page error listener (uncaught exceptions)
            def handle_page_error(err):
                if len(console_errors) < 10:
                    console_errors.append({
                        "level": "error",
                        "message": str(err)[:1000],
                        "source": "uncaught_exception",
                    })
            page.on("pageerror", handle_page_error)

            # 3. Route allowlist enforcement
            async def handle_route(route):
                req = route.request
                req_url = req.url
                # Allow only if URL is within allowed internal origin
                if not req_url.startswith(allowed_origin):
                    if len(network_records) < 10:
                        network_records.append({
                            "method": req.method,
                            "url": req_url[:500],
                            "status_code": None,
                            "failed": True,
                            "error_message": f"Blocked by client security policy: target outside allowed origin",
                        })
                    await route.abort("blockedbyclient")
                else:
                    await route.continue_()

            await page.route("**/*", handle_route)

            # 4. Response listener for HTTP errors
            def handle_response(resp: Response):
                if resp.status >= 400:
                    if len(network_records) < 10:
                        network_records.append({
                            "method": resp.request.method,
                            "url": resp.url[:500],
                            "status_code": resp.status,
                            "failed": True,
                            "error_message": f"HTTP {resp.status} response",
                        })
            page.on("response", handle_response)

            # 5. Request failure listener
            def handle_req_failed(req: Request):
                if len(network_records) < 10 and not any(r.get("url") == req.url for r in network_records):
                    network_records.append({
                        "method": req.method,
                        "url": req.url[:500],
                        "status_code": None,
                        "failed": True,
                        "error_message": req.failure or "Request failed",
                    })
            page.on("requestfailed", handle_req_failed)

            # Execution steps
            try:
                # Step A: Navigation
                try:
                    response = await page.goto(target_url, timeout=page_timeout, wait_until="domcontentloaded")
                except Exception as nav_exc:
                    test_status = "FAILED"
                    failed_step = f"Navigation to '{target_url}' failed: {nav_exc}"
                    assertion_summary = f"Expected status {expected_status}, but navigation raised: {nav_exc}"
                    raise

                status_code = response.status if response else None
                if expected_status and status_code != expected_status:
                    test_status = "FAILED"
                    failed_step = f"Expected HTTP status {expected_status}, received {status_code}"
                    assertion_summary = f"HTTP status mismatch: expected {expected_status}, got {status_code}"
                    raise AssertionError(failed_step)

                # Step B: Elements verification
                for sel in expected_elements:
                    try:
                        el = await page.wait_for_selector(sel, timeout=action_timeout, state="attached")
                        if not el:
                            raise AssertionError(f"Selector '{sel}' missing")
                    except Exception as sel_exc:
                        test_status = "FAILED"
                        failed_step = f"Verification of element '{sel}' failed: {sel_exc}"
                        assertion_summary = f"Expected visible element '{sel}', but timed out or missing"
                        raise

                # Step C: Title check
                if expected_title:
                    actual_title = await page.title()
                    if expected_title.lower() not in actual_title.lower():
                        test_status = "FAILED"
                        failed_step = f"Title assertion failed: '{expected_title}' not in '{actual_title}'"
                        assertion_summary = f"Expected title to contain '{expected_title}', got '{actual_title}'"
                        raise AssertionError(failed_step)

                # Step D: Interactions
                for idx, item in enumerate(interactions):
                    action = item.get("action")
                    sel = item.get("selector")
                    val = item.get("value")
                    exp_text = item.get("expected_text")

                    if action == "click":
                        await page.click(sel, timeout=action_timeout)
                    elif action == "fill":
                        await page.fill(sel, val or "", timeout=action_timeout)
                    elif action == "select":
                        await page.select_option(sel, val or "", timeout=action_timeout)
                    elif action == "wait":
                        wait_secs = min(max(float(val or 1.0), 0.1), 15.0)
                        await asyncio.sleep(wait_secs)
                    elif action == "navigate":
                        nav_path = val or "/"
                        if not nav_path.startswith("/"):
                            nav_path = "/" + nav_path
                        nav_url = f"{base_url}{nav_path}"
                        if page.url.rstrip("/") != nav_url.rstrip("/"):
                            await page.goto(nav_url, timeout=page_timeout, wait_until="domcontentloaded")
                    elif action == "assert_text":
                        el = await page.wait_for_selector(sel, timeout=action_timeout)
                        text = await el.inner_text() if el else ""
                        if exp_text and exp_text not in text:
                            raise AssertionError(f"Expected text '{exp_text}' not in '{text}'")
                    elif action == "assert_visible":
                        await page.wait_for_selector(sel, timeout=action_timeout, state="visible")
                    elif action == "assert_url":
                        exp_route = val or ""
                        current_url = page.url
                        if exp_route not in current_url:
                            raise AssertionError(f"Expected URL to contain '{exp_route}', got '{current_url}'")
                    elif action == "screenshot":
                        ss_file = f"screenshots/{test_id}_step_{idx+1}.png"
                        ss_abs = f"/workspace/{ss_file}"
                        await page.screenshot(path=ss_abs)
                        sz = Path(ss_abs).stat().st_size if Path(ss_abs).exists() else 0
                        test_screenshots.append({
                            "artifact_type": "SCREENSHOT",
                            "file_path": ss_file,
                            "size_bytes": sz,
                            "content_type": "image/png",
                            "caption": f"Step {idx+1} screenshot",
                        })

                if not assertion_summary:
                    assertion_summary = f"Page loaded successfully at '{target_url}' (HTTP {status_code}). Document checks passed."

            except Exception as step_exc:
                if test_status == "PASSED":
                    test_status = "FAILED"
                if not failed_step:
                    failed_step = str(step_exc)

            finally:
                # Capture final test screenshot
                if capture_screenshot:
                    try:
                        ss_file = f"screenshots/{test_id}.png"
                        ss_abs = f"/workspace/{ss_file}"
                        await page.screenshot(path=ss_abs)
                        sz = Path(ss_abs).stat().st_size if Path(ss_abs).exists() else 0
                        test_screenshots.append({
                            "artifact_type": "SCREENSHOT",
                            "file_path": ss_file,
                            "size_bytes": sz,
                            "content_type": "image/png",
                            "caption": f"Terminal screenshot for {test_id}",
                        })
                    except Exception as ss_err:
                        pass

                duration = round(time.monotonic() - start_time, 3)
                await page.close()

                results.append({
                    "test_id": test_id,
                    "name": test_name,
                    "status": test_status,
                    "duration_seconds": duration,
                    "failed_step": failed_step,
                    "assertion_summary": assertion_summary,
                    "screenshots": test_screenshots,
                    "console_errors": console_errors,
                    "network_errors": network_records,
                    "metadata": test.get("metadata", {}),
                })

        await context.close()
        await browser.close()

    with open("/workspace/results.json", "w", encoding="utf-8") as out_fp:
        json.dump({"test_cases": results}, out_fp, indent=2)

if __name__ == "__main__":
    asyncio.run(run_smoke_suite())
"""


def get_runner_script_content() -> str:
    """Return the static Python runner script executed inside the container."""
    return RUNNER_SCRIPT
