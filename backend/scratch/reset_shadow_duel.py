import sqlite3
import json

conn = sqlite3.connect('se_intelliplatform.db')
cursor = conn.cursor()
pid_hex = '68289eab12f44602a4b7143f29c52c58'
v1_id = '56d21523-d241-45e2-a1a3-57c667e56fe4'
v1_hex = v1_id.replace('-', '')

# 1. Delete test versions > 1
cursor.execute("DELETE FROM development_versions WHERE project_id = ? AND version_number > 1", (pid_hex,))
deleted_v = cursor.rowcount
print(f"Deleted {deleted_v} test versions")

# 2. Reset project settings active_version_id to v1
cursor.execute("SELECT settings FROM projects WHERE id = ?", (pid_hex,))
row = cursor.fetchone()
settings = json.loads(row[0]) if row and row[0] else {}
settings["active_version_id"] = v1_id
cursor.execute("UPDATE projects SET settings = ? WHERE id = ?", (json.dumps(settings), pid_hex))

# 3. Ensure v1 status is VERIFIED
cursor.execute("UPDATE development_versions SET status = 'VERIFIED' WHERE id = ?", (v1_hex,))

conn.commit()
conn.close()
print("Reset Shadow Duel to v1 baseline successfully.")
