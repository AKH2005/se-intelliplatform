import sqlite3
import json

conn = sqlite3.connect('se_intelliplatform.db')
cursor = conn.cursor()
vid_hex = '56d21523d24145e2a1a357c667e56fe4'
cursor.execute("SELECT metadata FROM development_versions WHERE id = ?", (vid_hex,))
row = cursor.fetchone()
if row and row[0]:
    meta = json.loads(row[0])
    files = meta.get("files", {})
    app_tsx = files.get("frontend/src/App.tsx", "")
    print("=== App.tsx ===")
    print(app_tsx)
    print("\n=== index.html head & title ===")
    idx = files.get("frontend/index.html", "")
    print(idx[:1000])

conn.close()
