import sqlite3
import json
import uuid
from pathlib import Path
import sys

# Ensure running from backend
db_path = Path("se_intelliplatform.db")
if not db_path.exists():
    db_path = Path("backend/se_intelliplatform.db")

print("Checking db_path:", db_path.resolve())
conn = sqlite3.connect(str(db_path.resolve()))
cur = conn.cursor()
pid_s = "51458fe8-776f-4325-9e5a-bfc33dce112d"
pid_h = pid_s.replace("-", "")
cur.execute("SELECT name, description, settings FROM projects WHERE id = ? OR id = ?", (pid_s, pid_h))
row = cur.fetchone()
print("DB row:", row)

sys.path.insert(0, ".")
sys.path.insert(0, "backend")
from app.runtime.preview_server import get_app_html_for_project

html = get_app_html_for_project(pid_s)
print("HTML length:", len(html))
print("Contains 'new-task-input':", "new-task-input" in html)
print("Contains 'Executive':", "Executive" in html)
print("Contains 'Analytics':", "Analytics" in html)
print("First 300 chars:\n", html[:300])