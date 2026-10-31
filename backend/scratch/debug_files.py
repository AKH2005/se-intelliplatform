import sqlite3
import json

conn = sqlite3.connect("backend/se_intelliplatform.db")
cur = conn.cursor()
cur.execute("SELECT project_id, version_number, files_manifest, status FROM development_versions WHERE status IN ('VERIFIED', 'SUPERSEDED') ORDER BY version_number DESC LIMIT 3")
for r in cur.fetchall():
    print(f"Proj: {r[0]} | v{r[1]} | status={r[3]}")
    if r[2]:
        manifest = json.loads(r[2])
        print("Files:", [m["path"] for m in manifest if isinstance(m, dict)])

