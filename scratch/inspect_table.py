import sqlite3
conn = sqlite3.connect('backend/se_intelliplatform.db')
cur = conn.cursor()
cur.execute("PRAGMA table_info(development_versions)")
for col in cur.fetchall():
    print(col)
