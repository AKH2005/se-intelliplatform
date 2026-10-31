import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
python_bin = backend_dir / ".venv" / "Scripts" / "python.exe"

env = os.environ.copy()
env["PYTHONUNBUFFERED"] = "1"

cmd = [
    str(python_bin), "-m", "uvicorn", "app.main:app",
    "--host", "127.0.0.1", "--port", "8000", "--log-level", "info"
]

proc = subprocess.Popen(cmd, cwd=str(backend_dir), env=env)
print("Started backend PID:", proc.pid)

start = time.time()
healthy = False
while time.time() - start < 60.0:
    time.sleep(2)
    elapsed = int(time.time() - start)
    try:
        req = urllib.request.Request("http://127.0.0.1:8000/health")
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            print(f"[{elapsed}s] Connected! Status:", resp.status)
            healthy = True
            break
    except Exception as e:
        print(f"[{elapsed}s] Waiting... ({type(e).__name__})")

proc.terminate()
try:
    proc.wait(timeout=2.0)
except Exception:
    proc.kill()

print("Result healthy:", healthy)