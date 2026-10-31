import sys
import ast

file_path = r"backend/app/runtime/preview_server.py"
with open(file_path, "r", encoding="utf-8") as f:
    code = f.read()

old_func = '''def is_dark_mode_active(project_id: Optional[str] = None) -> bool:
    if runtime_features.get("dark_mode", False):
        return True
    target_pid = project_id or active_project_context.get("project_id")
    if target_pid:
        try:
            import sqlite3, json
            conn = sqlite3.connect("se_intelliplatform.db")
            cur = conn.cursor()
            cur.execute("SELECT settings FROM projects WHERE id = ?", (str(target_pid),))
            row = cur.fetchone()
            if row and row[0]:
                settings_dict = json.loads(row[0]) if isinstance(row[0], str) else row[0]
                active_vid = settings_dict.get("active_version_id")
                if active_vid:
                    cur.execute("SELECT version_number FROM development_versions WHERE id = ?", (str(active_vid),))
                    v_row = cur.fetchone()
                    if v_row and v_row[0] and int(v_row[0]) >= 2:
                        conn.close()
                        return True
            conn.close()
        except Exception:
            pass
    return False'''

new_func = '''def is_dark_mode_active(project_id: Optional[str] = None) -> bool:
    target_pid = project_id or active_project_context.get("project_id")
    if target_pid:
        try:
            import sqlite3, json
            conn = sqlite3.connect("se_intelliplatform.db")
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
    return bool(runtime_features.get("dark_mode", False))'''

assert old_func in code, "old_func must be in preview_server.py"
code = code.replace(old_func, new_func)

ast.parse(code)
with open(file_path, "w", encoding="utf-8") as f:
    f.write(code)
print("is_dark_mode_active updated successfully!")

