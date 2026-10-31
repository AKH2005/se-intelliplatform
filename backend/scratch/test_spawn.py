import os
import subprocess
import time
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
python_bin = backend_dir / ".venv" / "Scripts" / "python.exe"

env = os.environ.copy()
env["PYTHONUNBUFFERED"] = "1"

cmd = [
    str(python_bin), "-u", "-m", "uvicorn", "app.main:app",
    "--host", "127.0.0.1", "--port", "8000", "--log-level", "info"
]

proc = subprocess.Popen(cmd, cwd=str(backend_dir), env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
print("Spawned PID:", proc.pid)

for _ in range(25):
    line = proc.stdout.readline()
    if line:
        print("Uvicorn line:", line.strip())
        if "Application startup complete" in line or "Uvicorn running on" in line:
            print("SERVER IS READY!")
            break
    time.sleep(0.5)

proc.terminate()
try:
    proc.wait(timeout=2.0)
except Exception:
    proc.kill()

