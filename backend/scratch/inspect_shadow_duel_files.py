import sqlite3
import json

conn = sqlite3.connect('se_intelliplatform.db')
cursor = conn.cursor()
vid_hex = '56d21523d24145e2a1a357c667e56fe4'
cursor.execute("SELECT files_manifest, metadata FROM development_versions WHERE id = ?", (vid_hex,))
row = cursor.fetchone()
if row:
    manifest = json.loads(row[0]) if row[0] else []
    print(f"Total files in manifest: {len(manifest)}")
    for f in manifest:
        print("  -", f.get("path"), f.get("size_bytes"))
conn.close()
