import sqlite3
import json

conn = sqlite3.connect('se_intelliplatform.db')
cursor = conn.cursor()
pid_hex = '68289eab12f44602a4b7143f29c52c58'
cursor.execute("SELECT metadata FROM development_versions WHERE project_id = ? AND version_number = 2", (pid_hex,))
row = cursor.fetchone()
meta = json.loads(row[0]) if row else {}
idx = meta.get("files", {}).get("frontend/index.html", "")
print("Version 2 index length:", len(idx))
with open('backend/scratch/v2_index.html', 'w', encoding='utf-8') as f:
    f.write(idx)
print("Saved v2_index.html")

conn.close()
