from pathlib import Path

path = Path("backend/app/runtime/preview_server.py")
text = path.read_text(encoding="utf-8")

old_func = """def is_dark_mode_active(project_id: Optional[str] = None) -> bool:
    target_pid = project_id or active_project_context.get("project_id")
    if not target_pid:
        try:
            import sqlite3
            conn_p = sqlite3.connect(str(DB_PATH))
            cur_p = conn_p.cursor()
            cur_p.execute("SELECT id FROM projects ORDER BY created_at DESC LIMIT 1")
            p_row = cur_p.fetchone()
            conn_p.close()
            if p_row and p_row[0]:
                target_pid = str(p_row[0])
        except Exception:
            pass
    if target_pid:
        try:
            import sqlite3, json
            conn = sqlite3.connect(str(DB_PATH))
            cur = conn.cursor()
            cur.execute("SELECT settings FROM projects WHERE id = ?", (str(target_pid),))
            row = cur.fetchone()
            if row and row[0]:
                settings_dict = json.loads(row[0]) if isinstance(row[0], str) else row[0]
                active_vid = settings_dict.get("active_version_id")
                if active_vid:
                    cur.execute("SELECT version_number FROM development_versions WHERE id = ?", (str(active_vid),))
                    v_row = cur.fetchone()
                    if v_row and v_row[0] is not None:
                        v_num = int(v_row[0])
                        conn.close()
                        if v_num <= 1:
                            return False
                        return True
            conn.close()
        except Exception:
            pass
    return bool(runtime_features.get("dark_mode", False))"""

new_func = """def is_dark_mode_active(project_id: Optional[str] = None) -> bool:
    target_pid = project_id or active_project_context.get("project_id")
    if not target_pid:
        try:
            import sqlite3
            conn_p = sqlite3.connect(str(DB_PATH))
            cur_p = conn_p.cursor()
            cur_p.execute("SELECT id FROM projects ORDER BY created_at DESC LIMIT 1")
            p_row = cur_p.fetchone()
            conn_p.close()
            if p_row and p_row[0]:
                target_pid = str(p_row[0])
        except Exception:
            pass
    if target_pid:
        try:
            import sqlite3, json
            conn = sqlite3.connect(str(DB_PATH))
            cur = conn.cursor()
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
                        if v_num <= 1:
                            return False
                        return True
            conn.close()
        except Exception:
            pass
    return bool(runtime_features.get("dark_mode", False))"""

old_lookup = 'cur.execute("SELECT name, description FROM projects WHERE id = ?", (str(project_id),))'
new_lookup = 'pid_s = str(project_id)\n                pid_h = pid_s.replace("-", "")\n                cur.execute("SELECT name, description FROM projects WHERE id = ? OR id = ?", (pid_s, pid_h))'

if old_func in text:
    text = text.replace(old_func, new_func)
    print("Patched is_dark_mode_active")
else:
    print("WARNING: old_func not found")

if old_lookup in text:
    text = text.replace(old_lookup, new_lookup)
    print("Patched project lookup in preview_server")
else:
    print("WARNING: old_lookup not found")

path.write_text(text, encoding="utf-8")
print("Done writing preview_server.py")

