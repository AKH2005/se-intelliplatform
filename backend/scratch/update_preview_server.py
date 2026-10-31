"""Script to update backend/app/runtime/preview_server.py with TaskFlow full QA features."""
import sys
import re

file_path = r"backend/app/runtime/preview_server.py"
with open(file_path, "r", encoding="utf-8") as f:
    code = f.read()

# 1. Update runtime_features: dark_mode = False initially
code = code.replace(
    '"dark_mode": True,',
    '"dark_mode": False,'
)

# 2. Add is_dark_mode_active and sync_tasks_from_db
if "def is_dark_mode_active" not in code:
    insertion_marker = "# ==============================================================================\n# FAST-PATH RUNTIME FEATURE STATE & AUTHENTICATION ENDPOINTS"
    if insertion_marker not in code:
        insertion_marker = "# FAST-PATH RUNTIME FEATURE STATE & AUTHENTICATION ENDPOINTS"
    
    helper_code = '''def is_dark_mode_active(project_id: Optional[str] = None) -> bool:
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
    return False

def sync_tasks_from_db():
    global tasks_db
    try:
        import sqlite3
        conn = sqlite3.connect("se_intelliplatform.db")
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS preview_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                priority TEXT DEFAULT 'MEDIUM',
                status TEXT DEFAULT 'PENDING',
                due_date TEXT DEFAULT '2026-12-31'
            )
        """)
        cur.execute("SELECT id, title, description, priority, status, due_date FROM preview_tasks ORDER BY id ASC")
        rows = cur.fetchall()
        if not rows:
            initial = [
                ("Setup Project Scaffolding", "Initialize database models and API routes.", "HIGH", "COMPLETED", "2026-10-15"),
                ("Design Task Management UI", "Create responsive task dashboard and action cards.", "MEDIUM", "PENDING", "2026-10-20")
            ]
            cur.executemany("INSERT INTO preview_tasks (title, description, priority, status, due_date) VALUES (?, ?, ?, ?, ?)", initial)
            conn.commit()
            cur.execute("SELECT id, title, description, priority, status, due_date FROM preview_tasks ORDER BY id ASC")
            rows = cur.fetchall()
        conn.close()
        tasks_db = [{"id": r[0], "title": r[1], "description": r[2], "priority": r[3], "status": r[4], "due_date": r[5]} for r in rows]
    except Exception:
        pass
    return tasks_db

'''
    code = code.replace(insertion_marker, helper_code + insertion_marker)

# 3. In set_project_context, reset dark_mode = False for new context
if 'runtime_features["dark_mode"] = False' not in code:
    code = code.replace(
        'active_project_context.update(ctx)',
        'active_project_context.update(ctx)\n    runtime_features["dark_mode"] = False'
    )

# 4. In API tasks endpoints, use sync_tasks_from_db and persist changes
old_task_crud = '''@app.get("/api/tasks")
def get_tasks():
    return tasks_db

@app.post("/api/tasks", status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate):
    new_id = max([t["id"] for t in tasks_db], default=0) + 1
    new_task = {
        "id": new_id,
        "title": task.title,
        "description": task.description or "",
        "priority": task.priority,
        "status": task.status,
        "due_date": task.due_date or "2026-12-31"
    }
    tasks_db.append(new_task)
    return new_task

@app.get("/api/tasks/{task_id}")
def get_task(task_id: int):
    for t in tasks_db:
        if t["id"] == task_id:
            return t
    raise HTTPException(status_code=404, detail="Task not found")

@app.put("/api/tasks/{task_id}")
def update_task(task_id: int, task: TaskUpdate):
    for t in tasks_db:
        if t["id"] == task_id:
            if task.title is not None:
                t["title"] = task.title
            if task.description is not None:
                t["description"] = task.description
            if task.priority is not None:
                t["priority"] = task.priority
            if task.status is not None:
                t["status"] = task.status
            if task.due_date is not None:
                t["due_date"] = task.due_date
            return t
    raise HTTPException(status_code=404, detail="Task not found")

@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: int):
    global tasks_db
    tasks_db = [t for t in tasks_db if t["id"] != task_id]
    return {"status": "DELETED", "id": task_id}'''

new_task_crud = '''@app.get("/api/tasks")
def get_tasks():
    return sync_tasks_from_db()

@app.post("/api/tasks", status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate):
    sync_tasks_from_db()
    new_id = max([t["id"] for t in tasks_db], default=0) + 1
    new_task = {
        "id": new_id,
        "title": task.title,
        "description": task.description or "",
        "priority": task.priority,
        "status": task.status,
        "due_date": task.due_date or "2026-12-31"
    }
    tasks_db.append(new_task)
    try:
        import sqlite3
        conn = sqlite3.connect("se_intelliplatform.db")
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO preview_tasks (id, title, description, priority, status, due_date) VALUES (?, ?, ?, ?, ?, ?)",
            (new_id, new_task["title"], new_task["description"], new_task["priority"], new_task["status"], new_task["due_date"])
        )
        conn.commit()
        conn.close()
    except Exception:
        pass
    return new_task

@app.get("/api/tasks/{task_id}")
def get_task(task_id: int):
    sync_tasks_from_db()
    for t in tasks_db:
        if t["id"] == task_id:
            return t
    raise HTTPException(status_code=404, detail="Task not found")

@app.put("/api/tasks/{task_id}")
def update_task(task_id: int, task: TaskUpdate):
    sync_tasks_from_db()
    for t in tasks_db:
        if t["id"] == task_id:
            if task.title is not None:
                t["title"] = task.title
            if task.description is not None:
                t["description"] = task.description
            if task.priority is not None:
                t["priority"] = task.priority
            if task.status is not None:
                t["status"] = task.status
            if task.due_date is not None:
                t["due_date"] = task.due_date
            try:
                import sqlite3
                conn = sqlite3.connect("se_intelliplatform.db")
                cur = conn.cursor()
                cur.execute(
                    "UPDATE preview_tasks SET title = ?, description = ?, priority = ?, status = ?, due_date = ? WHERE id = ?",
                    (t["title"], t["description"], t["priority"], t["status"], t["due_date"], task_id)
                )
                conn.commit()
                conn.close()
            except Exception:
                pass
            return t
    raise HTTPException(status_code=404, detail="Task not found")

@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: int):
    global tasks_db
    sync_tasks_from_db()
    tasks_db = [t for t in tasks_db if t["id"] != task_id]
    try:
        import sqlite3
        conn = sqlite3.connect("se_intelliplatform.db")
        cur = conn.cursor()
        cur.execute("DELETE FROM preview_tasks WHERE id = ?", (task_id,))
        conn.commit()
        conn.close()
    except Exception:
        pass
    return {"status": "DELETED", "id": task_id}'''

if old_task_crud in code:
    code = code.replace(old_task_crud, new_task_crud)
else:
    # Try normalizing CRLF
    old_norm = old_task_crud.replace("\r\n", "\n")
    code_norm = code.replace("\r\n", "\n")
    if old_norm in code_norm:
        code_norm = code_norm.replace(old_norm, new_task_crud)
        code = code_norm

# 5. Replace get_taskflow_html function completely
start_idx = code.find("def get_taskflow_html")
end_idx = code.find("# 4. ADDITIONAL GENERATED APPLICATION TEMPLATES", start_idx)
if end_idx == -1:
    end_idx = code.find("# ==============================================================================\n# 4.", start_idx)

new_taskflow_func = '''def get_taskflow_html(project_id: Optional[str] = None):
    has_auth = runtime_features.get("auth", False)
    is_modern = runtime_features.get("modern_ui", False)
    has_search = runtime_features.get("search", False)
    has_dark_mode = is_dark_mode_active(project_id)

    dark_mode_header_html = """
      <button id="btn-theme-toggle" class="btn btn-secondary" onclick="toggleTheme()" style="display: inline-flex; align-items: center; gap: 0.4rem; padding: 0.45rem 0.85rem; border-radius: 6px; font-size: 0.82rem; font-weight: 600; cursor: pointer;">
        <span id="theme-icon">🌙</span> <span id="theme-text">Dark Mode</span>
      </button>
    """ if has_dark_mode else ""

    auth_header_html = """
      <div class="auth-bar" id="auth-header-bar" style="display: flex; align-items: center; gap: 0.5rem;">
        <span id="user-badge" style="display: none; font-size: 0.8rem; color: #34d399; background: rgba(16,185,129,0.15); border: 1px solid rgba(16,185,129,0.3); padding: 0.25rem 0.6rem; border-radius: 9999px;">● Logged in as Developer User</span>
        <button id="btn-login" class="btn" style="background: linear-gradient(135deg, #6366f1, #06b6d4);" onclick="openLoginModal()">Sign In</button>
        <button id="btn-logout" class="btn btn-secondary" style="display: none;" onclick="logoutUser()">Sign Out</button>
      </div>
    """ if has_auth else ""

    hero_stats_html = """
    <div id="hero-stats" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; margin-bottom: 1.5rem; padding: 1.25rem; background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; backdrop-filter: blur(8px);">
      <div><div style="font-size: 0.72rem; color: var(--text-muted); text-transform: uppercase; font-weight: 600;">Active Tasks</div><div style="font-size: 1.5rem; font-weight: 700; color: #fff;" id="stat-active-tasks">2</div></div>
      <div><div style="font-size: 0.72rem; color: var(--text-muted); text-transform: uppercase; font-weight: 600;">Completed</div><div style="font-size: 1.5rem; font-weight: 700; color: #34d399;" id="stat-completed-tasks">1</div></div>
      <div><div style="font-size: 0.72rem; color: var(--text-muted); text-transform: uppercase; font-weight: 600;">Runtime Port</div><div style="font-size: 1.5rem; font-weight: 700; color: #60a5fa;">8001</div></div>
      <div><div style="font-size: 0.72rem; color: var(--text-muted); text-transform: uppercase; font-weight: 600;">System Health</div><div style="font-size: 1.5rem; font-weight: 700; color: #a78bfa;">99.9%</div></div>
    </div>
    """ if is_modern else ""

    search_bar_html = """
    <div style="margin-bottom: 1.25rem; display: flex; gap: 0.5rem;">
      <input id="task-search-input" class="form-input" placeholder="🔍 Search tasks by title or description..." oninput="handleTaskSearch(this.value)" style="max-width: 400px;" />
    </div>
    """ if has_search else ""

    login_modal_html = """
  <div id="login-modal" class="modal-overlay">
    <div class="modal">
      <h2 style="font-size: 1.2rem; font-weight: 700;">Sign In to TaskFlow</h2>
      <p style="font-size: 0.82rem; color: var(--text-muted); margin: 0;">Access your tasks with developer credentials.</p>
      <div class="form-group">
        <label class="form-label">Email</label>
        <input id="login-email" class="form-input" placeholder="developer@se-intelliplatform.local" value="developer@se-intelliplatform.local" />
      </div>
      <div class="form-group">
        <label class="form-label">Password</label>
        <input id="login-password" type="password" class="form-input" placeholder="••••••••" value="password123" />
      </div>
      <div class="modal-actions">
        <button class="btn btn-secondary" onclick="closeLoginModal()">Cancel</button>
        <button id="btn-submit-login" class="btn" onclick="submitLogin()">Sign In</button>
      </div>
    </div>
  </div>
    """ if has_auth else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>TaskFlow — Live Application</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #0b1120;
      --card-bg: #151d30;
      --border: rgba(255, 255, 255, 0.08);
      --accent: #3b82f6;
      --accent-hover: #2563eb;
      --text: #f8fafc;
      --text-muted: #94a3b8;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Plus Jakarta Sans', sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      padding: 2rem;
      transition: background 0.25s, color 0.25s;
    }}
    body.light-theme {{
      --bg: #f8fafc;
      --card-bg: #ffffff;
      --border: rgba(0, 0, 0, 0.1);
      --accent: #2563eb;
      --accent-hover: #1d4ed8;
      --text: #0f172a;
      --text-muted: #64748b;
    }}
    body.light-theme .logo h1 {{ color: #0f172a; }}
    body.light-theme .btn-secondary {{ background: #e2e8f0; color: #0f172a; border-color: #cbd5e1; }}
    body.light-theme .btn-secondary:hover {{ background: #cbd5e1; }}
    body.light-theme .card {{ background: #ffffff; border-color: #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); }}
    body.light-theme .modal {{ background: #ffffff; color: #0f172a; border-color: #cbd5e1; }}
    body.light-theme .modal h2 {{ color: #0f172a; }}
    body.light-theme .form-input, body.light-theme .form-select, body.light-theme .form-textarea {{
      background: #f1f5f9;
      border-color: #cbd5e1;
      color: #0f172a;
    }}
    .header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 1.5rem;
      border-bottom: 1px solid var(--border);
      margin-bottom: 2rem;
    }}
    .logo {{
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }}
    .logo h1 {{ font-size: 1.5rem; font-weight: 700; color: #fff; }}
    .badge {{
      font-size: 0.7rem;
      font-weight: 600;
      padding: 0.2rem 0.5rem;
      border-radius: 4px;
      background: rgba(59, 130, 246, 0.15);
      color: #60a5fa;
      border: 1px solid rgba(59, 130, 246, 0.3);
    }}
    .btn {{
      background: var(--accent);
      color: #fff;
      border: none;
      padding: 0.5rem 1rem;
      border-radius: 6px;
      font-weight: 600;
      cursor: pointer;
      font-size: 0.875rem;
      transition: background 0.2s;
    }}
    .btn:hover {{ background: var(--accent-hover); }}
    .btn-secondary {{ background: rgba(255, 255, 255, 0.08); color: var(--text); border: 1px solid var(--border); }}
    .btn-secondary:hover {{ background: rgba(255, 255, 255, 0.12); }}
    .btn-danger {{ background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }}
    .btn-danger:hover {{ background: rgba(239, 68, 68, 0.25); }}
    .toolbar {{
      display: flex;
      gap: 0.75rem;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 1.5rem;
      flex-wrap: wrap;
    }}
    .filter-btn {{
      padding: 0.45rem 0.95rem;
      border-radius: 6px;
      font-size: 0.82rem;
      font-weight: 600;
      cursor: pointer;
      border: 1px solid var(--border);
      background: rgba(255, 255, 255, 0.06);
      color: var(--text);
      transition: all 0.2s;
    }}
    .filter-btn.active {{
      background: var(--accent);
      color: #ffffff;
      border-color: var(--accent);
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      gap: 1.25rem;
    }}
    .card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1.25rem;
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
    }}
    .card-header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 0.5rem;
    }}
    .card-title {{ font-weight: 600; font-size: 1rem; }}
    .card-desc {{ font-size: 0.85rem; color: var(--text-muted); line-height: 1.4; }}
    .card-meta {{
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-size: 0.75rem;
    }}
    .tag {{ padding: 0.15rem 0.5rem; border-radius: 4px; font-weight: 600; text-transform: uppercase; }}
    .tag-high {{ background: rgba(239, 68, 68, 0.2); color: #f87171; }}
    .tag-med {{ background: rgba(245, 158, 11, 0.2); color: #fbbf24; }}
    .tag-status {{ background: rgba(16, 185, 129, 0.2); color: #34d399; }}
    .tag-pending {{ background: rgba(148, 163, 184, 0.2); color: #94a3b8; }}
    .card-actions {{
      margin-top: auto;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding-top: 0.75rem;
      border-top: 1px solid var(--border);
    }}
    .modal-overlay {{
      display: none;
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(0, 0, 0, 0.7);
      backdrop-filter: blur(4px);
      align-items: center;
      justify-content: center;
      z-index: 1000;
    }}
    .modal {{
      background: #151d30;
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 1.5rem;
      width: 100%;
      max-width: 450px;
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }}
    .form-group {{ display: flex; flex-direction: column; gap: 0.35rem; }}
    .form-label {{ font-size: 0.8rem; font-weight: 600; color: var(--text-muted); }}
    .form-input, .form-select, .form-textarea {{
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 0.5rem 0.75rem;
      color: #fff;
      font-family: inherit;
      font-size: 0.875rem;
    }}
    .modal-actions {{ display: flex; justify-content: flex-end; gap: 0.5rem; margin-top: 0.5rem; }}
  </style>
</head>
<body>
  <div class="header">
    <div class="logo">
      <h1>TaskFlow</h1>
      <span class="badge">Generated v1.0.0</span>
      <span style="font-size: 0.8rem; color: var(--text-muted);">Runtime: Active (Port 8001)</span>
      <a href="/eventhub" class="badge" style="text-decoration: none; background: rgba(99,102,241,0.2); color: #a5b4fc;">Switch to EventHub</a>
    </div>
    <div style="display: flex; align-items: center; gap: 0.75rem;">
      {dark_mode_header_html}
      {auth_header_html}
      <button id="btn-add-task" class="btn" onclick="openModal()">+ Add New Task</button>
    </div>
  </div>

  {hero_stats_html}
  {search_bar_html}

  <div class="toolbar">
    <div style="display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap;">
      <button id="filter-all" class="filter-btn active" onclick="setFilter('ALL', this)">All (<span id="count-all">0</span>)</button>
      <button id="filter-active" class="filter-btn" onclick="setFilter('ACTIVE', this)">Active (<span id="count-active">0</span>)</button>
      <button id="filter-completed" class="filter-btn" onclick="setFilter('COMPLETED', this)">Completed (<span id="count-completed">0</span>)</button>
    </div>
    <div id="task-counter" style="font-size: 0.85rem; color: var(--text-muted); font-weight: 600;">
      <span id="counter-text">0 remaining</span>
    </div>
  </div>

  <div id="tasks-container" class="grid"></div>

  <div id="task-modal" class="modal-overlay">
    <div class="modal">
      <h2 style="font-size: 1.15rem; font-weight: 600;">Create Task</h2>
      <div class="form-group">
        <label class="form-label">Task Title</label>
        <input id="modal-title" class="form-input" placeholder="e.g. Complete Project Documentation" />
      </div>
      <div class="form-group">
        <label class="form-label">Description</label>
        <textarea id="modal-desc" class="form-textarea" placeholder="Detailed acceptance criteria..."></textarea>
      </div>
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem;">
        <div class="form-group">
          <label class="form-label">Priority</label>
          <select id="modal-priority" class="form-select">
            <option value="HIGH">High</option>
            <option value="MEDIUM" selected>Medium</option>
            <option value="LOW">Low</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">Status</label>
          <select id="modal-status" class="form-select">
            <option value="PENDING" selected>Pending</option>
            <option value="IN_PROGRESS">In Progress</option>
            <option value="COMPLETED">Completed</option>
          </select>
        </div>
      </div>
      <div class="form-group">
        <label class="form-label">Due Date</label>
        <input id="modal-due" type="date" class="form-input" value="2026-12-31" />
      </div>
      <div class="modal-actions">
        <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
        <button id="modal-submit" class="btn" onclick="saveTask()">Save Task</button>
      </div>
    </div>
  </div>

  {login_modal_html}

  <script>
    let allTasks = [];
    let currentFilter = 'ALL';

    function setFilter(filter, btn) {{
      currentFilter = filter;
      document.querySelectorAll('#filter-all, #filter-active, #filter-completed').forEach(b => {{
        b.classList.remove('active');
      }});
      if (btn) {{
        btn.classList.add('active');
      }}
      applyFilter();
    }}

    function updateCounters() {{
      const total = allTasks.length;
      const completed = allTasks.filter(t => t.status === 'COMPLETED').length;
      const active = allTasks.filter(t => t.status !== 'COMPLETED').length;

      const cAll = document.getElementById('count-all');
      const cActive = document.getElementById('count-active');
      const cComp = document.getElementById('count-completed');
      const cText = document.getElementById('counter-text');
      if (cAll) cAll.textContent = total;
      if (cActive) cActive.textContent = active;
      if (cComp) cComp.textContent = completed;
      if (cText) cText.textContent = `${{active}} task${{active === 1 ? '' : 's'}} remaining`;

      const statActive = document.getElementById('stat-active-tasks');
      const statComp = document.getElementById('stat-completed-tasks');
      if (statActive) statActive.textContent = active;
      if (statComp) statComp.textContent = completed;
    }}

    function applyFilter() {{
      let filtered = allTasks;
      if (currentFilter === 'ACTIVE') {{
        filtered = allTasks.filter(t => t.status !== 'COMPLETED');
      }} else if (currentFilter === 'COMPLETED') {{
        filtered = allTasks.filter(t => t.status === 'COMPLETED');
      }}
      const q = document.getElementById('task-search-input')?.value.toLowerCase().trim();
      if (q) {{
        filtered = filtered.filter(t => (t.title || '').toLowerCase().includes(q) || (t.description || '').toLowerCase().includes(q));
      }}
      renderTasks(filtered);
    }}

    function toggleTheme() {{
      const isLight = document.body.classList.toggle('light-theme');
      const icon = document.getElementById('theme-icon');
      const text = document.getElementById('theme-text');
      if (isLight) {{
        if (icon) icon.textContent = '☀️';
        if (text) text.textContent = 'Light Mode';
        localStorage.setItem('taskflow_theme', 'light');
      }} else {{
        if (icon) icon.textContent = '🌙';
        if (text) text.textContent = 'Dark Mode';
        localStorage.setItem('taskflow_theme', 'dark');
      }}
    }}

    if (localStorage.getItem('taskflow_theme') === 'light') {{
      document.body.classList.add('light-theme');
      const icon = document.getElementById('theme-icon');
      const text = document.getElementById('theme-text');
      if (icon) icon.textContent = '☀️';
      if (text) text.textContent = 'Light Mode';
    }}

    function showToast(msg, isErr = false) {{
      let t = document.getElementById('toast');
      if (!t) {{
        t = document.createElement('div');
        t.id = 'toast';
        t.style.position = 'fixed';
        t.style.bottom = '20px';
        t.style.right = '20px';
        t.style.background = '#1e293b';
        t.style.border = '1px solid ' + (isErr ? '#ef4444' : '#3b82f6');
        t.style.color = '#fff';
        t.style.padding = '0.75rem 1.25rem';
        t.style.borderRadius = '8px';
        t.style.fontSize = '0.85rem';
        t.style.zIndex = '9999';
        t.style.boxShadow = '0 10px 25px rgba(0,0,0,0.5)';
        document.body.appendChild(t);
      }}
      t.textContent = msg;
      t.style.border = '1px solid ' + (isErr ? '#ef4444' : '#3b82f6');
      t.style.display = 'block';
      setTimeout(() => {{ if (t) t.style.display = 'none'; }}, 3000);
    }}

    function openLoginModal() {{
      const m = document.getElementById('login-modal');
      if (m) m.style.display = 'flex';
      showToast('Opened sign in modal.');
    }}

    function closeLoginModal() {{
      const m = document.getElementById('login-modal');
      if (m) m.style.display = 'none';
    }}

    async function submitLogin() {{
      const email = document.getElementById('login-email')?.value || 'developer@se-intelliplatform.local';
      try {{
        const res = await fetch('/api/auth/login', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ email: email, password: 'password123' }})
        }});
        const data = await res.json();
        closeLoginModal();
        const bLogin = document.getElementById('btn-login');
        const bLogout = document.getElementById('btn-logout');
        const badge = document.getElementById('user-badge');
        if (bLogin) bLogin.style.display = 'none';
        if (bLogout) bLogout.style.display = 'inline-block';
        if (badge) {{
          badge.style.display = 'inline-block';
          badge.textContent = '● Logged in as ' + data.user.name;
        }}
        showToast('Successfully signed in as ' + data.user.name);
      }} catch (err) {{
        showToast('Sign in error: ' + err.message, true);
      }}
    }}

    async function logoutUser() {{
      await fetch('/api/auth/logout', {{ method: 'POST' }});
      const bLogin = document.getElementById('btn-login');
      const bLogout = document.getElementById('btn-logout');
      const badge = document.getElementById('user-badge');
      if (bLogin) bLogin.style.display = 'inline-block';
      if (bLogout) bLogout.style.display = 'none';
      if (badge) badge.style.display = 'none';
      showToast('Signed out successfully.');
    }}

    function handleTaskSearch(query) {{
      applyFilter();
    }}

    function renderTasks(tasks) {{
      const container = document.getElementById('tasks-container');
      container.innerHTML = tasks.map(t => `
        <div class="card" id="task-card-${{t.id}}">
          <div class="card-header">
            <div style="display: flex; align-items: center; gap: 0.6rem;">
              <input type="checkbox" id="check-task-${{t.id}}" ${{t.status === 'COMPLETED' ? 'checked' : ''}} onchange="toggleComplete(${{t.id}}, this.checked)" style="width: 17px; height: 17px; cursor: pointer; accent-color: var(--accent);" />
              <div class="card-title" id="task-title-${{t.id}}" style="${{t.status === 'COMPLETED' ? 'text-decoration: line-through; opacity: 0.65;' : ''}}">${{t.title}}</div>
            </div>
            <span class="tag ${{t.priority === 'HIGH' ? 'tag-high' : 'tag-med'}}">${{t.priority}}</span>
          </div>
          <div class="card-desc">${{t.description || 'No description provided.'}}</div>
          <div class="card-meta">
            <span class="tag ${{t.status === 'COMPLETED' ? 'tag-status' : 'tag-pending'}}">${{t.status}}</span>
            <span style="color: var(--text-muted);">Due: ${{t.due_date || 'N/A'}}</span>
          </div>
          <div class="card-actions">
            <select style="background: rgba(255,255,255,0.06); border: 1px solid var(--border); color: #fff; padding: 0.3rem; border-radius: 4px; font-size: 0.75rem;"
              onchange="updateStatus(${{t.id}}, this.value)" id="select-status-${{t.id}}">
              <option value="PENDING" ${{t.status === 'PENDING' ? 'selected' : ''}}>Pending</option>
              <option value="IN_PROGRESS" ${{t.status === 'IN_PROGRESS' ? 'selected' : ''}}>In Progress</option>
              <option value="COMPLETED" ${{t.status === 'COMPLETED' ? 'selected' : ''}}>Completed</option>
            </select>
            <button class="btn btn-danger" style="padding: 0.3rem 0.6rem; font-size: 0.75rem;" onclick="deleteTask(${{t.id}})" id="btn-delete-${{t.id}}">Delete</button>
          </div>
        </div>
      `).join('');
    }}

    async function toggleComplete(id, isCompleted) {{
      const newStatus = isCompleted ? 'COMPLETED' : 'PENDING';
      await updateStatus(id, newStatus);
    }}

    async function fetchTasks() {{
      const res = await fetch('/api/tasks');
      allTasks = await res.json();
      updateCounters();
      applyFilter();
    }}

    function openModal() {{ document.getElementById('task-modal').style.display = 'flex'; }}
    function closeModal() {{ document.getElementById('task-modal').style.display = 'none'; }}

    async function saveTask() {{
      const title = document.getElementById('modal-title').value.trim();
      if (!title) return alert('Title is required');
      const desc = document.getElementById('modal-desc').value.trim();
      const priority = document.getElementById('modal-priority').value;
      const status = document.getElementById('modal-status').value;
      const due_date = document.getElementById('modal-due').value;
      await fetch('/api/tasks', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ title, description: desc, priority, status, due_date }})
      }});
      closeModal();
      document.getElementById('modal-title').value = '';
      document.getElementById('modal-desc').value = '';
      fetchTasks();
    }}

    async function updateStatus(id, newStatus) {{
      await fetch(`/api/tasks/${{id}}`, {{
        method: 'PUT',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ status: newStatus }})
      }});
      fetchTasks();
    }}

    async function deleteTask(id) {{
      await fetch(`/api/tasks/${{id}}`, {{ method: 'DELETE' }});
      fetchTasks();
    }}

    fetch('/api/auth/me').then(r => r.json()).then(data => {{
      if (data.authenticated && data.user) {{
        const bLogin = document.getElementById('btn-login');
        const bLogout = document.getElementById('btn-logout');
        const badge = document.getElementById('user-badge');
        if (bLogin) bLogin.style.display = 'none';
        if (bLogout) bLogout.style.display = 'inline-block';
        if (badge) {{
          badge.style.display = 'inline-block';
          badge.textContent = '● Logged in as ' + data.user.name;
        }}
      }}
    }}).catch(() => {{}});

    window.addEventListener('DOMContentLoaded', () => {{
      const b = document.getElementById('btn-login');
      if (b) {{
        b.addEventListener('click', (e) => {{
          e.preventDefault();
          openLoginModal();
        }});
      }}
    }});

    fetchTasks();
  </script>
</body>
</html>
"""

'''

code = code[:start_idx] + new_taskflow_func + code[end_idx:]

# 6. In get_app_html_for_project, pass project_id to get_taskflow_html
code = code.replace("return get_taskflow_html()", "return get_taskflow_html(project_id)")

# Verify AST parse
import ast
try:
    ast.parse(code)
    print("AST parse successful!")
except Exception as e:
    print("AST parse error:", e)
    sys.exit(1)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(code)

print("preview_server.py successfully updated!")

