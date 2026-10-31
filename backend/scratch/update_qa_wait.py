from pathlib import Path

p = Path("backend/scratch/qa_senior_e2e_test.py")
content = p.read_text(encoding="utf-8")

old_wait = """async def wait_for_http(url: str, timeout: float = 35.0) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "QA-Probe"})
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                if resp.status in (200, 304, 302):
                    return True
        except Exception:
            pass
        await asyncio.sleep(0.5)
    return False"""

new_wait = """async def wait_for_http(url: str, timeout: float = 85.0) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        urls_to_try = [url]
        if "/health" in url and not "/api/v1/health" in url:
            urls_to_try.append(url.replace("/health", "/api/v1/health"))
        for probe_url in urls_to_try:
            try:
                req = urllib.request.Request(probe_url, headers={"User-Agent": "QA-Probe"})
                with urllib.request.urlopen(req, timeout=3.5) as resp:
                    if resp.status in (200, 304, 302):
                        return True
            except Exception:
                pass
        await asyncio.sleep(0.5)
    return False"""

if old_wait in content:
    content = content.replace(old_wait, new_wait, 1)
    p.write_text(content, encoding="utf-8")
    print("SUCCESS: wait_for_http updated.")
else:
    c_norm = content.replace("\r\n", "\n")
    if old_wait in c_norm:
        c_norm = c_norm.replace(old_wait, new_wait, 1)
        p.write_text(c_norm, encoding="utf-8")
        print("SUCCESS: wait_for_http updated (norm).")
    else:
        print("ERROR: old_wait not found.")

# Also add log printing if failed
c_now = p.read_text(encoding="utf-8")
old_fail = """    if not (b_ok and p_ok and f_ok):
        test_results["step1_prep"]["status"] = "FAIL"
        test_results["step1_prep"]["details"] = f"Services failed to become healthy: Backend={b_ok}, Preview={p_ok}, Frontend={f_ok}"
        _terminate_all(backend_proc, preview_proc, frontend_proc)
        return test_results"""

new_fail = """    if not (b_ok and p_ok and f_ok):
        backend_log.flush()
        try:
            with open(BACKEND_DIR / "backend_startup.log", "r", encoding="utf-8", errors="replace") as f:
                log(f"Backend startup log:\n{f.read()[:1000]}")
        except Exception as e:
            log(f"Could not read backend startup log: {e}")
        log(f"Backend process poll status: {backend_proc.poll()}")
        test_results["step1_prep"]["status"] = "FAIL"
        test_results["step1_prep"]["details"] = f"Services failed to become healthy: Backend={b_ok}, Preview={p_ok}, Frontend={f_ok}"
        _terminate_all(backend_proc, preview_proc, frontend_proc)
        return test_results"""

if old_fail in c_now:
    c_now = c_now.replace(old_fail, new_fail, 1)
    p.write_text(c_now, encoding="utf-8")
    print("SUCCESS: fail logging updated.")
else:
    c_norm = c_now.replace("\r\n", "\n")
    if old_fail in c_norm:
        c_norm = c_norm.replace(old_fail, new_fail, 1)
        p.write_text(c_norm, encoding="utf-8")
        print("SUCCESS: fail logging updated (norm).")
    else:
        print("ERROR: old_fail not found.")

