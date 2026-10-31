from pathlib import Path

p = Path("backend/scratch/qa_senior_e2e_test.py")
content = p.read_text(encoding="utf-8")

old_code = """    # Launch Backend (Port 8000)
    python_bin = BACKEND_DIR / ".venv" / "Scripts" / "python.exe"
    env_backend = os.environ.copy()
    env_backend["PYTHONUNBUFFERED"] = "1"
    env_backend["PYTHONPATH"] = str(BACKEND_DIR)
    backend_cmd = [
        str(python_bin), "-u", "-m", "uvicorn", "app.main:app",
        "--host", "127.0.0.1", "--port", "8000", "--log-level", "info"
    ]
    log(f"Spawning backend on port 8000...")
    backend_log = open(BACKEND_DIR / "backend_startup.log", "w", encoding="utf-8")
    backend_proc = subprocess.Popen(backend_cmd, cwd=str(BACKEND_DIR), env=env_backend, stdout=backend_log, stderr=backend_log)

    # Launch Frontend (Port 5173)
    frontend_dir = ROOT_DIR / "frontend"
    frontend_cmd = "npx vite --host 127.0.0.1 --port 5173"
    log(f"Spawning frontend on port 5173...")
    frontend_proc = subprocess.Popen(frontend_cmd, cwd=str(frontend_dir), shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Wait for services concurrently with generous timeout
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

new_code = """    # 1. Launch Backend (Port 8000)
    uvicorn_bin = BACKEND_DIR / ".venv" / "Scripts" / "uvicorn.exe"
    env_backend = os.environ.copy()
    env_backend["PYTHONUNBUFFERED"] = "1"
    env_backend["PYTHONPATH"] = str(BACKEND_DIR)
    backend_cmd = [
        str(uvicorn_bin), "app.main:app",
        "--host", "127.0.0.1", "--port", "8000", "--log-level", "info"
    ]
    log(f"Spawning backend on port 8000...")
    backend_log = open(BACKEND_DIR / "backend_startup.log", "w", encoding="utf-8")
    backend_proc = subprocess.Popen(backend_cmd, cwd=str(BACKEND_DIR), env=env_backend, stdout=backend_log, stderr=backend_log)

    log("Waiting for backend to become healthy on port 8000...")
    b_ok = await wait_for_http("http://127.0.0.1:8000/health", timeout=95.0)
    log(f"Backend (8000) health status: {b_ok}")

    # 2. Check/Start Preview Runtime (Port 8001)
    p_ok = await wait_for_http("http://127.0.0.1:8001/health", timeout=15.0)
    preview_proc = None
    if not p_ok:
        log("Starting preview server explicitly on port 8001...")
        preview_cmd = [
            str(uvicorn_bin), "app.runtime.preview_server:app",
            "--host", "127.0.0.1", "--port", "8001", "--log-level", "warning"
        ]
        preview_proc = subprocess.Popen(preview_cmd, cwd=str(BACKEND_DIR), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        p_ok = await wait_for_http("http://127.0.0.1:8001/health", timeout=30.0)
    log(f"Preview (8001) health status: {p_ok}")

    # 3. Launch Frontend (Port 5173)
    frontend_dir = ROOT_DIR / "frontend"
    vite_bin = frontend_dir / "node_modules" / ".bin" / "vite.cmd"
    frontend_cmd = f'"{vite_bin}" --host 127.0.0.1 --port 5173'
    log(f"Spawning frontend on port 5173 via vite.cmd...")
    frontend_proc = subprocess.Popen(frontend_cmd, cwd=str(frontend_dir), shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    f_ok = await wait_for_http("http://127.0.0.1:5173/", timeout=30.0)
    log(f"Frontend (5173) health status: {f_ok}")"""

if old_code in content:
    content = content.replace(old_code, new_code, 1)
    p.write_text(content, encoding="utf-8")
    print("SUCCESS: qa_senior_e2e_test.py updated sequential start.")
else:
    c_norm = content.replace("\r\n", "\n")
    if old_code in c_norm:
        c_norm = c_norm.replace(old_code, new_code, 1)
        p.write_text(c_norm, encoding="utf-8")
        print("SUCCESS: qa_senior_e2e_test.py updated sequential start (norm).")
    else:
        print("ERROR: old_code not found.")

