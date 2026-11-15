import sys
sys.path.insert(0, "backend")
from app.runtime.preview_server import get_db_conn, DB_PATH, get_app_html_for_project

print("DB_PATH:", DB_PATH)
conn = get_db_conn()
cur = conn.cursor()
cur.execute("SELECT id, name, settings FROM projects WHERE id LIKE '%51458fe8%'")
rows = cur.fetchall()
print("Rows found:", len(rows))
for r in rows:
    print(r)

res = get_app_html_for_project("51458fe8-776f-4325-9e5a-bfc33dce112d")
print("res length:", len(res))
print("has new-task-input:", "new-task-input" in res)

