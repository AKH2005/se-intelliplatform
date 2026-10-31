import sqlite3
import json

conn = sqlite3.connect("backend/se_intelliplatform.db")
cur = conn.cursor()

cur.execute("SELECT agent_id, status, error_code, error_message, started_at FROM agent_execution_audits ORDER BY started_at DESC LIMIT 10")
for r in cur.fetchall():
    print("Agent Audit:", r)

cur.execute("SELECT workflow_id, status, errors, warnings, started_at FROM workflow_executions ORDER BY started_at DESC LIMIT 5")
for r in cur.fetchall():
    print("WF Execution:", r)
