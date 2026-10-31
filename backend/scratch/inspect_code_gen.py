import sqlite3
import json

conn = sqlite3.connect("backend/se_intelliplatform.db")
cur = conn.cursor()
cur.execute("SELECT artifacts FROM workflow_executions WHERE status = 'COMPLETED' AND workflow_id = 'code-generation-workflow' ORDER BY completed_at DESC LIMIT 1")
row = cur.fetchone()
if row and row[0]:
    art = json.loads(row[0])
    code_gen = art.get('code-generation') or art.get('code_generation') or {}
    files = code_gen.get('generated_files', [])
    for f in files:
        if f.get('path') == 'frontend/src/App.tsx':
            print("--- App.tsx ---")
            print(f.get('content'))
        elif f.get('path') == 'frontend/src/styles/App.css':
            print("--- App.css ---")
            print(f.get('content'))
