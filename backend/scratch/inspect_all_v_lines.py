import sqlite3
import json

conn = sqlite3.connect('se_intelliplatform.db')
cursor = conn.cursor()
pid_hex = '68289eab12f44602a4b7143f29c52c58'
cursor.execute("SELECT version_number, metadata FROM development_versions WHERE project_id = ? ORDER BY version_number ASC", (pid_hex,))
for v_num, meta_str in cursor.fetchall():
    meta = json.loads(meta_str) if meta_str else {}
    files = meta.get("files", {})
    idx = files.get("frontend/index.html") or files.get("index.html") or ""
    print(f"--- Version {v_num} index.html (len={len(idx)}) ---")
    for i, line in enumerate(idx.splitlines()):
        if any(term in line for term in ["auth-card", "modal", "login", "password", "btn-"]):
            print(f"  Line {i+1}: {line.strip()[:100]}")
conn.close()
