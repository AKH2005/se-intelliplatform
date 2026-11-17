import sqlite3
import json

conn = sqlite3.connect('se_intelliplatform.db')
cursor = conn.cursor()
vid_hex = '56d21523d24145e2a1a357c667e56fe4'
cursor.execute("SELECT metadata FROM development_versions WHERE id = ?", (vid_hex,))
row = cursor.fetchone()
if row and row[0]:
    meta = json.loads(row[0])
    idx = meta.get("files", {}).get("frontend/index.html", "")
    lines = idx.splitlines()
    for i, l in enumerate(lines):
        if "<header" in l or "<body" in l:
            print(f"Match at line {i+1}: {l}")
            for j in range(max(0, i-2), min(len(lines), i+15)):
                print(f"  {j+1}: {lines[j]}")
            break
conn.close()
