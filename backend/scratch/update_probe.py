from pathlib import Path

p = Path("backend/scratch/qa_senior_e2e_test.py")
content = p.read_text(encoding="utf-8")

old_probe = """    # Wait for services
    log("Probing service health endpoints (Backend: 8000, Preview: 8001, Frontend: 5173)...")
    b_ok = await wait_for_http("http://127.0.0.1:8000/health", timeout=40.0)
    p_ok = await wait_for_http("http://127.0.0.1:8001/health", timeout=15.0)
    f_ok = await wait_for_http("http://127.0.0.1:5173/", timeout=25.0)

    # If preview server on 8001 didn't start automatically, start it explicitly
    preview_proc = None
    if not p_ok:
        log("Starting preview server explicitly on port 8001...")
        preview_cmd = [
            str(python_bin), "-m", "uvicorn", "app.runtime.preview_server:app",
            "--host", "127.0.0.1", "--port", "8001", "--log-level", "warning"
        ]
        preview_proc = subprocess.Popen(preview_cmd, cwd=str(BACKEND_DIR), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        p_ok = await wait_for_http("http://127.0.0.1:8001/health", timeout=15.0)"""

new_probe = """    # Wait for services concurrently with generous timeout
    log("Probing service health endpoints concurrently (Backend: 8000, Preview: 8001, Frontend: 5173)...")
    b_task = asyncio.create_task(wait_for_http("http://127.0.0.1:8000/health", timeout=75.0))
    p_task = asyncio.create_task(wait_for_http("http://127.0.0.1:8001/health", timeout=75.0))
    f_task = asyncio.create_task(wait_for_http("http://127.0.0.1:5173/", timeout=75.0))
    b_ok, p_ok, f_ok = await asyncio.gather(b_task, p_task, f_task)

    # If preview server on 8001 didn't start automatically, start it explicitly
    preview_proc = None
    if not p_ok:
        log("Starting preview server explicitly on port 8001...")
        preview_cmd = [
            str(python_bin), "-m", "uvicorn", "app.runtime.preview_server:app",
            "--host", "127.0.0.1", "--port", "8001", "--log-level", "warning"
        ]
        preview_proc = subprocess.Popen(preview_cmd, cwd=str(BACKEND_DIR), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        p_ok = await wait_for_http("http://127.0.0.1:8001/health", timeout=30.0)"""

if old_probe in content:
    content = content.replace(old_probe, new_probe, 1)
    p.write_text(content, encoding="utf-8")
    print("SUCCESS: qa_senior_e2e_test.py updated probe.")
else:
    c_norm = content.replace("\r\n", "\n")
    if old_probe in c_norm:
        c_norm = c_norm.replace(old_probe, new_probe, 1)
        p.write_text(c_norm, encoding="utf-8")
        print("SUCCESS: qa_senior_e2e_test.py updated probe (norm).")
    else:
        print("ERROR: old_probe not found.")

