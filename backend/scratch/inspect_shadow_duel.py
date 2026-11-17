import sqlite3
import json
import uuid

conn = sqlite3.connect('se_intelliplatform.db')
cursor = conn.cursor()
pid_str = "68289eab-12f4-4602-a4b7-143f29c52c58"
pid_hex = pid_str.replace("-", "")

cursor.execute("SELECT id, name, slug, settings, description FROM projects WHERE id = ? OR id = ?", (pid_str, pid_hex))
row = cursor.fetchone()
print("Project:", row[0], row[1], row[2], row[4])
settings_dict = json.loads(row[3]) if row[3] else {}
print("Settings:", settings_dict)

cursor.execute("SELECT id, version_number, status, content_hash FROM development_versions WHERE project_id = ? OR project_id = ? ORDER BY version_number ASC", (pid_str, pid_hex))
versions = cursor.fetchall()
for v in versions:
    print("Version:", v)

conn.close()
