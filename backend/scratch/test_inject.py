import sqlite3
import json
from app.services.application_developer_service import ApplicationDeveloperService

conn = sqlite3.connect('se_intelliplatform.db')
cursor = conn.cursor()
pid_hex = '68289eab12f44602a4b7143f29c52c58'
cursor.execute("SELECT metadata FROM development_versions WHERE project_id = ? AND version_number = 1", (pid_hex,))
row = cursor.fetchone()
meta = json.loads(row[0]) if row else {}
v1_html = meta.get("files", {}).get("frontend/index.html", "")
conn.close()

svc = ApplicationDeveloperService(None, None, None)
res_html = svc._inject_login_into_html(v1_html, "Shadow Duel")
print("Original length:", len(v1_html))
print("Result length:", len(res_html))
print("Has 'auth-modal-overlay':", "auth-modal-overlay" in res_html)
print("Has 'btn-open-login':", "btn-open-login" in res_html)
print("Has 'auth-header-bar':", "auth-header-bar" in res_html)
