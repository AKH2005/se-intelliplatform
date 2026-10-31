import subprocess
import time
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
python_bin = backend_dir / ".venv" / "Scripts" / "python.exe"
log_path = backend_dir / "backend_startup.log"

cmd = [
    str(python_bin), "-m", "uvicorn", "app.main:app",
    "--host", "127.0.0.1", "--port", "8000", "--log-level", "info"
]

log_f = open(log_path, "w", encoding="utf-8")
proc = subprocess.Popen(cmd, cwd=str(backend_dir), stdout=log_f, stderr=log_f)
print("Spawned PID:", proc.pid)

time.sleep(12)
proc.terminate()
try:
    proc.wait(timeout=2.0)
except Exception:
    proc.kill()
log_f.close()

print("Log content:")
print(log_path.read_text(encoding="utf-8"))

