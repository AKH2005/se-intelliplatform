import sqlite3
import json

conn = sqlite3.connect('se_intelliplatform.db')
c = conn.cursor()
c.execute("select id, name, settings from projects where id = '68289eab12f44602a4b7143f29c52c58'")
proj = c.fetchone()
print("Project:", proj[0], proj[1], proj[2])
c.execute("select id, project_id, version_number, status, source_reason from development_versions order by created_at desc limit 10")
for row in c.fetchall():
    print("Version:", row)
conn.close()

import urllib.request

try:
    with urllib.request.urlopen("http://127.0.0.1:8001/preview?project_id=68289eab-12f4-4602-a4b7-143f29c52c58") as resp:
        html = resp.read().decode('utf-8')
        print("Preview HTTP Status:", resp.status)
        print("btn-open-login in HTML:", "btn-open-login" in html)
        print("auth-modal-overlay in HTML:", "auth-modal-overlay" in html)
        print("HTML length:", len(html))
except Exception as e:
    print("Preview request failed:", e)
