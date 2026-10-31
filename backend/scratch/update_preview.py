from pathlib import Path

p = Path("backend/app/runtime/preview_server.py")
content = p.read_text(encoding="utf-8")

target = """def is_dark_mode_active(project_id: Optional[str] = None) -> bool:
    target_pid = project_id or active_project_context.get("project_id")"""

replacement = """def is_dark_mode_active(project_id: Optional[str] = None) -> bool:
    target_pid = project_id or active_project_context.get("project_id")
    if not target_pid:
        try:
            import sqlite3
            conn_p = sqlite3.connect("se_intelliplatform.db")
            cur_p = conn_p.cursor()
            cur_p.execute("SELECT id FROM projects ORDER BY created_at DESC LIMIT 1")
            p_row = cur_p.fetchone()
            conn_p.close()
            if p_row and p_row[0]:
                target_pid = str(p_row[0])
        except Exception:
            pass"""

if target in content:
    new_content = content.replace(target, replacement, 1)
    p.write_text(new_content, encoding="utf-8")
    print("SUCCESS: preview_server.py updated.")
else:
    # Try normalized newlines
    c_norm = content.replace("\r\n", "\n")
    if target in c_norm:
        new_content = c_norm.replace(target, replacement, 1)
        p.write_text(new_content, encoding="utf-8")
        print("SUCCESS: preview_server.py updated (normalized newlines).")
    else:
        print("ERROR: target not found.")

