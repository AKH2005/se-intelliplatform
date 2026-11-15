from pathlib import Path

# 1. Patch set_project_context in preview_server.py
ps_path = Path("backend/app/runtime/preview_server.py")
if not ps_path.exists():
    ps_path = Path("app/runtime/preview_server.py")

content = ps_path.read_text(encoding="utf-8")

old_ctx = '''@app.post("/api/runtime/context")
def set_project_context(payload: dict):
    p_id = str(payload.get("project_id") or "")
    p_name = payload.get("project_name") or ""
    p_desc = payload.get("project_description") or ""

    # If project_id is provided but name is missing, look up from database
    if p_id and not p_name:
        try:
            import json as _j
            conn = get_db_conn()
            cur = conn.cursor()
            pid_s = str(p_id)
            pid_h = pid_s.replace("-", "")
            cur.execute("SELECT name, description, settings FROM projects WHERE id = ? OR id = ?", (pid_s, pid_h))
            row = cur.fetchone()
            conn.close()
            if row:
                p_name = row[0] or ""
                p_desc = row[1] or ""
                try:
                    s_dict = _j.loads(row[2]) if isinstance(row[2], str) else (row[2] or {})
                    cat = s_dict.get("category", "")
                    if cat:
                        p_desc = f"{p_desc} {cat}"
                except Exception:
                    pass
        except Exception:
            pass

    mode = detect_mode(p_name, p_desc)'''

new_ctx = '''@app.post("/api/runtime/context")
def set_project_context(payload: dict):
    p_id = str(payload.get("project_id") or "")
    p_name = payload.get("project_name") or ""
    p_desc = payload.get("project_description") or ""
    mode = payload.get("mode")

    if p_id:
        try:
            import json as _j, uuid
            conn = get_db_conn()
            cur = conn.cursor()
            clean_pid = str(uuid.UUID(str(p_id)))
            pid_h = clean_pid.replace("-", "")
            cur.execute("SELECT name, description, settings FROM projects WHERE id = ? OR id = ?", (clean_pid, pid_h))
            row = cur.fetchone()
            conn.close()
            if row:
                p_name = p_name or row[0] or ""
                p_desc = p_desc or row[1] or ""
                try:
                    s_dict = _j.loads(row[2]) if isinstance(row[2], str) else (row[2] or {})
                    if not mode:
                        mode = s_dict.get("archetype")
                except Exception:
                    pass
        except Exception:
            pass

    if not mode:
        mode = detect_mode(p_name, p_desc)'''

if old_ctx in content:
    content = content.replace(old_ctx, new_ctx, 1)
    print("Replaced LF set_project_context in preview_server.py")
elif old_ctx.replace("\n", "\r\n") in content:
    content = content.replace(old_ctx.replace("\n", "\r\n"), new_ctx.replace("\n", "\r\n"), 1)
    print("Replaced CRLF set_project_context in preview_server.py")
else:
    print("ERROR: old_ctx not found in preview_server.py")
    exit(1)

ps_path.write_text(content, encoding="utf-8")

# 2. Patch preview_runtime_manager.py
prm_path = Path("backend/app/runtime/preview_runtime_manager.py")
if not prm_path.exists():
    prm_path = Path("app/runtime/preview_runtime_manager.py")

prm_content = prm_path.read_text(encoding="utf-8")

old_sync = '''    async def sync_context(
        self,
        project_id: Optional[str] = None,
        project_name: Optional[str] = None,
        project_description: Optional[str] = None,
    ) -> None:
        """Inform the preview server of the currently active project context."""
        payload = {
            "project_id": str(project_id) if project_id else None,
            "project_name": project_name or "",
            "project_description": project_description or "",
        }'''

new_sync = '''    async def sync_context(
        self,
        project_id: Optional[str] = None,
        project_name: Optional[str] = None,
        project_description: Optional[str] = None,
        mode: Optional[str] = None,
    ) -> None:
        """Inform the preview server of the currently active project context."""
        payload = {
            "project_id": str(project_id) if project_id else None,
            "project_name": project_name or "",
            "project_description": project_description or "",
            "mode": mode,
        }'''

if old_sync in prm_content:
    prm_content = prm_content.replace(old_sync, new_sync, 1)
    print("Replaced LF sync_context in preview_runtime_manager.py")
elif old_sync.replace("\n", "\r\n") in prm_content:
    prm_content = prm_content.replace(old_sync.replace("\n", "\r\n"), new_sync.replace("\n", "\r\n"), 1)
    print("Replaced CRLF sync_context in preview_runtime_manager.py")
else:
    print("ERROR: old_sync not found in preview_runtime_manager.py")
    exit(1)

prm_path.write_text(prm_content, encoding="utf-8")
print("Successfully updated preview_server.py and preview_runtime_manager.py!")
