from pathlib import Path

prev_path = Path("backend/app/runtime/preview_server.py")
if not prev_path.exists():
    prev_path = Path("app/runtime/preview_server.py")

content = prev_path.read_text(encoding="utf-8")

old_func_start = "def get_app_html_for_project(project_id: Optional[str] = None, app_type: Optional[str] = None) -> str:"
end_anchor = "    # 3. Serve specialized archetype starter prototype or domain-adaptive custom engine"

start_idx = content.find(old_func_start)
end_idx = content.find(end_anchor)

if start_idx == -1 or end_idx == -1:
    print(f"ERROR: Anchors not found: start_idx={start_idx}, end_idx={end_idx}")
    exit(1)

new_func_top = '''def get_app_html_for_project(project_id: Optional[str] = None, app_type: Optional[str] = None) -> str:
    mode = None
    p_name = ""
    p_desc = ""
    act_ver_id = None

    # 1. Resolve project metadata and active DevelopmentVersion FIRST
    if project_id:
        try:
            import sqlite3, json, uuid
            conn = get_db_conn()
            cur = conn.cursor()
            clean_pid = str(uuid.UUID(str(project_id)))
            pid_h = clean_pid.replace("-", "")
            cur.execute("SELECT name, description, settings FROM projects WHERE id = ? OR id = ?", (clean_pid, pid_h))
            row = cur.fetchone()
            if row:
                p_name = row[0] or ""
                p_desc = row[1] or ""
                settings = {}
                if row[2]:
                    try:
                        settings = json.loads(row[2])
                    except Exception:
                        pass
                mode = settings.get("archetype")
                act_ver_id = settings.get("active_version_id")

            # Check active_project_context / project_contexts if mode still not set
            if not mode:
                if str(clean_pid) in project_contexts:
                    ctx = project_contexts[str(clean_pid)]
                    mode = ctx.get("mode")
                    p_name = p_name or ctx.get("project_name", "")
                    p_desc = p_desc or ctx.get("project_description", "")
                else:
                    mode = detect_mode(p_name, p_desc)
        except Exception:
            pass

    # Only fall back to app_type if project_id was not provided or mode could not be resolved
    if not mode:
        mode = app_type or "custom"

    # 2. Check active DevelopmentVersion directly from database FIRST
    if project_id:
        try:
            import sqlite3, json, uuid
            conn = get_db_conn()
            cur = conn.cursor()
            clean_pid = str(uuid.UUID(str(project_id)))
            pid_h = clean_pid.replace("-", "")

            # If act_ver_id not resolved, query the latest active or highest version
            if not act_ver_id:
                cur.execute("SELECT id FROM development_versions WHERE project_id = ? OR project_id = ? ORDER BY version_number DESC LIMIT 1", (clean_pid, pid_h))
                v_res = cur.fetchone()
                if v_res:
                    act_ver_id = str(v_res[0])

            if act_ver_id:
                clean_vid = str(uuid.UUID(str(act_ver_id)))
                vid_h = clean_vid.replace("-", "")
                cur.execute("SELECT metadata FROM development_versions WHERE id = ? OR id = ?", (clean_vid, vid_h))
                v_row = cur.fetchone()
                if v_row and v_row[0]:
                    v_meta = json.loads(v_row[0]) if isinstance(v_row[0], str) else v_row[0]
                    v_files = v_meta.get("files", {})
                    h_cand = v_files.get("frontend/index.html") or v_files.get("index.html")
                    if h_cand:
                        is_stale = False
                        # Anti-collision check for Kanban
                        if mode not in ("taskflow", "custom") and any(m in h_cand for m in ["new-task-input", "loadTasks()", "task-form", "KanbanFlow Board"]):
                            is_stale = True
                        # Anti-collision check for Snake
                        if mode != "snake_game" and any(m in h_cand for m in ["spawnFood()", "snake_high_score", "Arcade Snake"]):
                            is_stale = True
                        # Anti-collision check for Shadow Master
                        if mode != "shadow_master" and any(m in h_cand for m in ["combatCanvas", "Katana Slash", "Shadow Master Skill Builder", "The Shadow Master"]):
                            is_stale = True

                        if not is_stale:
                            return h_cand
        except Exception:
            pass

    # 3. Check local workspace files with strict archetype anti-collision filters (even if app_type passed)
    if project_id:
        try:
            import os, uuid
            from pathlib import Path
            clean_pid = str(uuid.UUID(str(project_id)))
            ws_dir = DB_PATH.parent / ".runtime_workspaces" / clean_pid
            if ws_dir.exists():
                candidates = [
                    ws_dir / "index.html",
                    ws_dir / "frontend" / "index.html",
                    ws_dir / "public" / "index.html",
                ]
                for cand in candidates:
                    if cand.is_file():
                        c_text = cand.read_text(encoding="utf-8", errors="replace")
                        # Anti-collision check for Kanban
                        if mode not in ("taskflow", "custom") and any(m in c_text for m in ["new-task-input", "loadTasks()", "task-form", "KanbanFlow Board"]):
                            continue
                        # Anti-collision check for Snake
                        if mode != "snake_game" and any(m in c_text for m in ["spawnFood()", "snake_high_score", "Arcade Snake"]):
                            continue
                        # Anti-collision check for Shadow Master
                        if mode != "shadow_master" and any(m in c_text for m in ["combatCanvas", "Katana Slash", "Shadow Master Skill Builder", "The Shadow Master"]):
                            continue
                        if "Interactive Application Playground" not in c_text or mode == "custom":
                            return c_text
                for root, _, files in os.walk(str(ws_dir)):
                    for f in files:
                        if f.endswith(".html"):
                            c_text = Path(root, f).read_text(encoding="utf-8", errors="replace")
                            if mode not in ("taskflow", "custom") and any(m in c_text for m in ["new-task-input", "loadTasks()", "task-form", "KanbanFlow Board"]):
                                continue
                            if mode != "snake_game" and any(m in c_text for m in ["spawnFood()", "snake_high_score", "Arcade Snake"]):
                                continue
                            if mode != "shadow_master" and any(m in c_text for m in ["combatCanvas", "Katana Slash", "Shadow Master Skill Builder", "The Shadow Master"]):
                                continue
                            return c_text
        except Exception:
            pass

'''

# Stitch new implementation
content = content[:start_idx] + new_func_top + content[end_idx:]

prev_path.write_text(content, encoding="utf-8")
print("Successfully patched preview_server.py get_app_html_for_project!")
