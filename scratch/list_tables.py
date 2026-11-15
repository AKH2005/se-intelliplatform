import sqlite3

conn = sqlite3.connect("backend/se_intelliplatform.db")
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [r[0] for r in cur.fetchall()]
print(f"Total tables: {len(tables)}")
for t in tables:
    print(f"  - {t}")
conn.close()
