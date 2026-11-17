import sqlite3
import json

conn = sqlite3.connect('se_intelliplatform.db')
cursor = conn.cursor()
pid_hex = '68289eab12f44602a4b7143f29c52c58'
cursor.execute("SELECT settings FROM projects WHERE id = ?", (pid_hex,))
row = cursor.fetchone()
print("Project settings:", row[0] if row else None)

cursor.execute("SELECT id, version_number, status, metadata FROM development_versions WHERE project_id = ? ORDER BY version_number DESC", (pid_hex,))
for r in cursor.fetchall():
    meta = json.loads(r[3]) if r[3] else {}
    files = meta.get("files", {})
    idx = files.get("frontend/index.html") or files.get("index.html")
    print(f"Version {r[1]} (id={r[0]}, status={r[2]}):")
    print("  files count:", len(files))
    print("  has index.html:", idx is not None)
    if idx:
        print("  index.html len:", len(idx))
        print("  index has btn-open-login:", "btn-open-login" in idx)
        print("  index has auth-modal-overlay:", "auth-modal-overlay" in idx)

conn.close()
