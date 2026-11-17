import sqlite3

conn = sqlite3.connect('se_intelliplatform.db')
cursor = conn.cursor()
cursor.execute("SELECT id, email, hashed_password FROM users")
for row in cursor.fetchall():
    print(row[0], row[1])
conn.close()
