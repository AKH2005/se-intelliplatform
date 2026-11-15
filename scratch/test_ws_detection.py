import sys
import uuid
from pathlib import Path
sys.path.insert(0, "backend")

from app.runtime.preview_server import get_db_conn, DB_PATH, detect_mode

pid = "51458fe8-776f-4325-9e5a-bfc33dce112d"
conn = get_db_conn()
cur = conn.cursor()
pid_s = str(pid)
pid_h = pid_s.replace("-", "")
cur.execute("SELECT name, description, settings FROM projects WHERE id = ? OR id = ?", (pid_s, pid_h))
row = cur.fetchone()
print("Row:", row)
p_name = row[0] or ""
p_desc = row[1] or ""
import json
settings = json.loads(row[2]) if row[2] else {}
arch = settings.get("archetype")
print("arch from settings:", arch)
mode = arch or detect_mode(p_name, p_desc)
print("computed mode:", mode)

clean_pid = str(uuid.UUID(str(pid)))
ws_dir = DB_PATH.parent / ".runtime_workspaces" / clean_pid
cand = ws_dir / "frontend" / "index.html"
print("cand exists:", cand.exists())
if cand.exists():
    c_text = cand.read_text(encoding="utf-8", errors="replace")
    markers = ["new-task-input", "loadTasks()", "task-form", "KanbanFlow Board"]
    found = [m for m in markers if m in c_text]
    print("Kanban markers found in cand:", found)
    is_bad = mode not in ("taskflow", "custom") and any(m in c_text for m in markers)
    print("is_bad condition:", is_bad)
