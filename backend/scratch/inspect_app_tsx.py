import sqlite3
import json

conn = sqlite3.connect('se_intelliplatform.db')
c = conn.cursor()
pid_hex = 'd8dc84956b8a4fe3940a2b436d475454'
c.execute("select metadata from development_versions where project_id = ? and version_number = 4", (pid_hex,))
row = c.fetchone()
meta = json.loads(row[0]) if row and row[0] else {}
files = meta.get("files", {})

print("=== App.tsx ===")
print(files.get("frontend/src/App.tsx", "NOT FOUND"))

print("\n=== LoginPage.tsx (first 100 lines) ===")
lp = files.get("frontend/src/components/LoginPage.tsx", "NOT FOUND")
for i, line in enumerate(lp.splitlines()[:100], 1):
    print(f"{i:3d}: {line}")

conn.close()
