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
    print(f"Total lines in index.html: {len(lines)}")
    print("=== Lines 30 to 80 ===")
    for i, l in enumerate(lines[30:80], 31):
        print(f"{i}: {l}")
conn.close()
