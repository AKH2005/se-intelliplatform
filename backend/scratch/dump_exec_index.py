import sqlite3
import json

conn = sqlite3.connect('se_intelliplatform.db')
c = conn.cursor()
pid_hex = 'd8dc84956b8a4fe3940a2b436d475454'
c.execute("select metadata from development_versions where project_id = ? and version_number = 4", (pid_hex,))
row = c.fetchone()
meta = json.loads(row[0]) if row and row[0] else {}
files = meta.get("files", {})

html = files.get("frontend/index.html", "")
print("\n=== INDEX.HTML (lines 400-550) ===")
for i, line in enumerate(html.splitlines()[400:550], 401):
    print(f"{i:3d}: {line}")

print("\n=== INDEX.HTML (lines 550 to end) ===")
for i, line in enumerate(html.splitlines()[550:], 551):
    print(f"{i:3d}: {line}")

conn.close()
