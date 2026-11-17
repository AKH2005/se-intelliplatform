import sqlite3
import json
import difflib

conn = sqlite3.connect('se_intelliplatform.db')
cursor = conn.cursor()
pid_hex = '68289eab12f44602a4b7143f29c52c58'

cursor.execute("SELECT metadata FROM development_versions WHERE project_id = ? AND version_number = 1", (pid_hex,))
v1_meta = json.loads(cursor.fetchone()[0])
v1_html = v1_meta.get("files", {}).get("frontend/index.html", "")

cursor.execute("SELECT metadata FROM development_versions WHERE project_id = ? AND version_number = 2", (pid_hex,))
v2_meta = json.loads(cursor.fetchone()[0])
v2_html = v2_meta.get("files", {}).get("frontend/index.html", "")

diff = list(difflib.unified_diff(v1_html.splitlines(), v2_html.splitlines()))
print("Diff lines count:", len(diff))
for line in diff[:50]:
    print(line)

conn.close()
