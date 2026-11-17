import httpx
import sqlite3
import json

PID = "d8dc8495-6b8a-4fe3-940a-2b436d475454"
r = httpx.get(f"http://127.0.0.1:8001/preview?project_id={PID}")
print("Status:", r.status_code)
html = r.text
print("Length:", len(html))
print("First 300 chars of served preview:")
print(html[:300])

# Now check preview_server logic directly:
# What does get_app_html_for_project do?
from app.runtime.preview_server import get_app_html_for_project
res_html = get_app_html_for_project(PID)
print("\nDirect call get_app_html_for_project length:", len(res_html) if res_html else 0)

# Check database settings and versions
conn = sqlite3.connect('se_intelliplatform.db')
c = conn.cursor()
c.execute("select id, name, settings from projects where id = ?", (PID.replace('-', ''),))
proj = c.fetchone()
print("\nDB Project:", proj[0], proj[1], proj[2])
settings = json.loads(proj[2]) if proj[2] else {}
active_vid = settings.get("active_version_id")
print("Active version ID from DB settings:", active_vid)

c.execute("select id, version_number, status, source_reason, metadata from development_versions where id = ?", (active_vid.replace('-', ''),))
v_row = c.fetchone()
if v_row:
    print(f"Active Version in DB: v{v_row[1]}, status={v_row[2]}, reason={v_row[3]}")
    v_meta = json.loads(v_row[4]) if v_row[4] else {}
    files_map = v_meta.get("files", {})
    print("Files in active version metadata:", list(files_map.keys()))
    if "frontend/index.html" in files_map:
        f_html = files_map["frontend/index.html"]
        print("HTML in metadata files length:", len(f_html))
        print("HTML in metadata has btn-open-login:", "btn-open-login" in f_html)
else:
    print("Active version row not found!")

conn.close()
