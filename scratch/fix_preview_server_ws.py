import ast
import re
from pathlib import Path

target_file = Path("backend/app/runtime/preview_server.py")
content = target_file.read_text(encoding="utf-8")

old_func_start = content.find("def get_app_html_for_project(")
old_func_end = content.find('@app.get("/", response_class=HTMLResponse)')

new_func = '''def get_app_html_for_project(project_id: Optional[str] = None, app_type: Optional[str] = None) -> str:
    mode = app_type
    p_name = ""
    p_desc = ""

    # 1. Resolve project metadata and canonical archetype FIRST
    if not mode and project_id:
        if str(project_id) in project_contexts:
            ctx = project_contexts[str(project_id)]
            mode = ctx.get("mode")
            p_name = ctx.get("project_name", "")
            p_desc = ctx.get("project_description", "")
        else:
            try:
                import sqlite3
                conn = get_db_conn()
                cur = conn.cursor()
                pid_s = str(project_id)
                pid_h = pid_s.replace("-", "")
                cur.execute("SELECT name, description, settings FROM projects WHERE id = ? OR id = ?", (pid_s, pid_h))
                row = cur.fetchone()
                if row:
                    p_name = row[0] or ""
                    p_desc = row[1] or ""
                    settings = {}
                    if row[2]:
                        try:
                            import json
                            settings = json.loads(row[2])
                        except Exception:
                            pass
                    arch = settings.get("archetype")
                    if arch:
                        mode = arch
                    else:
                        mode = detect_mode(p_name, p_desc)
            except Exception:
                pass

    if not mode:
        mode = "custom"

    # 2. Check local workspace files with strict archetype anti-collision filters
    if project_id and not app_type:
        try:
            import os
            import uuid
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
                            return c_text
        except Exception:
            pass

    # 3. Serve specialized archetype starter prototype or domain-adaptive custom engine
    if mode == "analytics":
        return get_analytics_dashboard_html(p_name or "Executive Analytics", p_desc, project_id=project_id)
    elif mode == "eventhub":
        return EVENTHUB_HTML
    elif mode == "taskflow":
        return get_taskflow_html(project_id)
    elif mode == "snake_game":
        return get_snake_game_html(p_name or "Arcade Snake")
    elif mode == "carrom":
        return get_carrom_game_html(p_name or "Carrom Master", p_desc)
    elif mode == "shadow_master":
        return get_shadow_master_game_html(p_name or "Shadow Master Skill Builder", p_desc)
    elif mode == "chess":
        return get_chess_game_html(p_name or "Chess Master Pro", p_desc)
    elif mode == "platformer":
        return get_platformer_game_html(p_name or "Skyline Jump Platformer", p_desc)
    elif mode == "racing":
        return get_racing_game_html(p_name or "Turbo Nitro Racing", p_desc)
    elif mode == "puzzle":
        return get_puzzle_game_html(p_name or "Tile Shift Puzzle", p_desc)
    elif mode == "educational":
        return get_educational_app_html(p_name or "StudyDeck Flashcards & Quiz", p_desc)
    elif mode == "ecommerce":
        return get_ecommerce_html(p_name or "ShopSphere", p_desc)
    elif mode == "management":
        return get_management_html(p_name or "Enterprise Management System", p_desc)
    elif mode == "custom":
        return get_custom_interactive_html(p_name or "Domain Application Platform", p_desc)
    return get_custom_interactive_html(p_name or "Domain Application Platform", p_desc)


'''

content = content[:old_func_start] + new_func + content[old_func_end:]
ast.parse(content, filename="preview_server.py")
target_file.write_text(content, encoding="utf-8")
print("SUCCESS: Updated get_app_html_for_project with mode-first anti-collision checks!")
