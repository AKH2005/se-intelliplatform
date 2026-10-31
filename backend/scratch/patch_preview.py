from pathlib import Path

target_file = Path("backend/app/runtime/preview_server.py")
code = target_file.read_text(encoding="utf-8")

old_db = """DB_PATH = Path(__file__).resolve().parent.parent.parent / 'se_intelliplatform.db'
import uvicorn"""

new_db = """DB_PATH = Path(__file__).resolve().parent.parent.parent / 'se_intelliplatform.db'
import sqlite3

def get_db_conn():
    conn = sqlite3.connect(str(DB_PATH), timeout=30.0)
    try:
        conn.execute("PRAGMA busy_timeout = 30000")
        conn.execute("PRAGMA journal_mode = WAL")
    except Exception:
        pass
    return conn

import uvicorn"""

if old_db in code:
    code = code.replace(old_db, new_db, 1)

old_fn_start = "def is_dark_mode_active(project_id: Optional[str] = None) -> bool:"
old_fn_end = 'return bool(runtime_features.get("dark_mode", False))'

idx1 = code.find(old_fn_start)
idx2 = code.find(old_fn_end, idx1) + len(old_fn_end)

if idx1 != -1 and idx2 != -1:
    new_fn = '''def is_dark_mode_active(project_id: Optional[str] = None) -> bool:
    if runtime_features.get("dark_mode", False):
        return True
    target_pid = project_id or active_project_context.get("project_id")
    try:
        import json
        conn = get_db_conn()
        cur = conn.cursor()
        if not target_pid:
            cur.execute("SELECT id FROM projects ORDER BY created_at DESC LIMIT 1")
            p_row = cur.fetchone()
            if p_row and p_row[0]:
                target_pid = str(p_row[0])
        
        if target_pid:
            pid_str = str(target_pid)
            pid_hex = pid_str.replace("-", "")
            cur.execute("SELECT settings FROM projects WHERE id = ? OR id = ?", (pid_str, pid_hex))
            row = cur.fetchone()
            if row and row[0]:
                settings_dict = json.loads(row[0]) if isinstance(row[0], str) else row[0]
                active_vid = settings_dict.get("active_version_id")
                if active_vid:
                    vid_str = str(active_vid)
                    vid_hex = vid_str.replace("-", "")
                    cur.execute("SELECT version_number FROM development_versions WHERE id = ? OR id = ?", (vid_str, vid_hex))
                    v_row = cur.fetchone()
                    if v_row and v_row[0] is not None:
                        v_num = int(v_row[0])
                        conn.close()
                        return v_num > 1
            cur.execute("SELECT version_number FROM development_versions WHERE project_id = ? OR project_id = ? ORDER BY version_number DESC LIMIT 1", (pid_str, pid_hex))
            v_latest = cur.fetchone()
            if v_latest and v_latest[0] is not None:
                v_num = int(v_latest[0])
                conn.close()
                return v_num > 1
        conn.close()
    except Exception:
        pass
    return bool(runtime_features.get("dark_mode", False))'''
    code = code[:idx1] + new_fn + code[idx2:]

code = code.replace("sqlite3.connect(str(DB_PATH))", "get_db_conn()")

target_file.write_text(code, encoding="utf-8")
print("SUCCESSFULLY PATCHED PREVIEW SERVER")

