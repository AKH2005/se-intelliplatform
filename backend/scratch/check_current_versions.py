import sqlite3

conn = sqlite3.connect('se_intelliplatform.db')
cursor = conn.cursor()
pid_hex = '68289eab12f44602a4b7143f29c52c58'
cursor.execute("SELECT id, version_number, status, source_reason, created_at FROM development_versions WHERE project_id = ? ORDER BY version_number ASC", (pid_hex,))
for r in cursor.fetchall():
    print(r)
cursor.execute("SELECT settings FROM projects WHERE id = ?", (pid_hex,))
print("Settings:", cursor.fetchone()[0])
conn.close()
