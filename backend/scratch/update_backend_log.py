from pathlib import Path

p = Path("backend/scratch/qa_senior_e2e_test.py")
content = p.read_text(encoding="utf-8")

old_code = """    log(f"Spawning backend on port 8000...")
    backend_proc = subprocess.Popen(backend_cmd, cwd=str(BACKEND_DIR), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)"""

new_code = """    log(f"Spawning backend on port 8000...")
    backend_log = open(BACKEND_DIR / "backend_startup.log", "w", encoding="utf-8")
    backend_proc = subprocess.Popen(backend_cmd, cwd=str(BACKEND_DIR), stdout=backend_log, stderr=backend_log)"""

if old_code in content:
    content = content.replace(old_code, new_code, 1)
    p.write_text(content, encoding="utf-8")
    print("SUCCESS: qa_senior_e2e_test.py updated with log file.")
else:
    c_norm = content.replace("\r\n", "\n")
    if old_code in c_norm:
        c_norm = c_norm.replace(old_code, new_code, 1)
        p.write_text(c_norm, encoding="utf-8")
        print("SUCCESS: qa_senior_e2e_test.py updated with log file (norm).")
    else:
        print("ERROR: old_code not found.")

