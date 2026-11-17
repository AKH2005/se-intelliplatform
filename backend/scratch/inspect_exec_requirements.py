import sqlite3
import json

conn = sqlite3.connect('se_intelliplatform.db')
c = conn.cursor()
pid_hex = 'd8dc84956b8a4fe3940a2b436d475454'

c.execute("select id, name, description, settings from projects where id = ?", (pid_hex,))
proj = c.fetchone()
print("Project:", proj)

c.execute("select id, title, description, category from requirements where project_id = ?", (pid_hex,))
reqs = c.fetchall()
print(f"\nRequirements ({len(reqs)}):")
for r in reqs:
    print(f"  {r[0]}: {r[1]} - {r[2]} ({r[3]})")

conn.close()
