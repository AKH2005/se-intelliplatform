from pathlib import Path

p = Path("backend/scratch/qa_senior_e2e_test.py")
content = p.read_text(encoding="utf-8")

old_code = """    # Launch Backend (Port 8000)
    python_bin = BACKEND_DIR / ".venv" / "Scripts" / "python.exe"
    backend_cmd = [
        str(python_bin), "-m", "uvicorn", "app.main:app",
        "--host", "127.0.0.1", "--port", "8000", "--log-level", "warning"
    ]
    log(f"Spawning backend on port 8000...")
    backend_log = open(BACKEND_DIR / "backend_startup.log", "w", encoding="utf-8")
    backend_proc = subprocess.Popen(backend_cmd, cwd=str(BACKEND_DIR), stdout=backend_log, stderr=backend_log)"""

new_code = """    # Launch Backend (Port 8000)
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
    backend_proc = subprocess.Popen(backend_cmd, cwd=str(BACKEND_DIR), env=env_backend, stdout=backend_log, stderr=backend_log)"""

if old_code in content:
    content = content.replace(old_code, new_code, 1)
    p.write_text(content, encoding="utf-8")
    print("SUCCESS: qa_senior_e2e_test.py updated unbuffered.")
else:
    c_norm = content.replace("\r\n", "\n")
    if old_code in c_norm:
        c_norm = c_norm.replace(old_code, new_code, 1)
        p.write_text(c_norm, encoding="utf-8")
        print("SUCCESS: qa_senior_e2e_test.py updated unbuffered (norm).")
    else:
        print("ERROR: old_code not found.")

