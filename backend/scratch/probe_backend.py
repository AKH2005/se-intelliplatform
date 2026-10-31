import subprocess
import sys
import time
import urllib.request
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
python_bin = backend_dir / ".venv" / "Scripts" / "python.exe"
log_file = backend_dir / "test_run.log"

cmd = [
    str(python_bin), "-m", "uvicorn", "app.main:app",
    "--host", "127.0.0.1", "--port", "8000", "--log-level", "info"
]

with open(log_file, "w", encoding="utf-8") as out:
    proc = subprocess.Popen(cmd, cwd=str(backend_dir), stdout=out, stderr=out)
    print("Spawned backend PID:", proc.pid)
    
    # Probe for 10 seconds
    start = time.time()
    healthy = False
    while time.time() - start < 10.0:
        time.sleep(0.5)
        try:
            req = urllib.request.Request("http://127.0.0.1:8000/health")
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                print("Response code:", resp.status)
                if resp.status == 200:
                    healthy = True
                    break
        except Exception as e:
            print("Probe error:", type(e), e)

    proc.terminate()
    try:
        proc.wait(timeout=2.0)
    except Exception:
        proc.kill()

print("Result healthy:", healthy)
print("Log output:")
print(log_file.read_text(encoding="utf-8"))

