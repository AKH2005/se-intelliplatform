import sqlite3
import json

conn = sqlite3.connect('se_intelliplatform.db')
cursor = conn.cursor()
pid_hex = '68289eab12f44602a4b7143f29c52c58'
cursor.execute("SELECT metadata FROM development_versions WHERE project_id = ? ORDER BY version_number ASC LIMIT 1", (pid_hex,))
row = cursor.fetchone()
meta = json.loads(row[0]) if row else {}
idx = meta.get("files", {}).get("frontend/index.html", "")
print("index length:", len(idx))
print("Last 300 chars of index.html:")
print(repr(idx[-300:]))
conn.close()
