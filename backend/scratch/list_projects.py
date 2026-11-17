import sqlite3

conn = sqlite3.connect("se_intelliplatform.db")
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(projects)")
cols = cursor.fetchall()
print("Columns:", [c[1] for c in cols])
cursor.execute("SELECT id, name, slug FROM projects")
rows = cursor.fetchall()
for r in rows:
    print(r)
conn.close()
