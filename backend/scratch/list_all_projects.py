import sqlite3
import json

conn = sqlite3.connect('se_intelliplatform.db')
cursor = conn.cursor()
cursor.execute("SELECT id, name, slug FROM projects")
rows = cursor.fetchall()
for r in rows:
    print(r)
conn.close()
