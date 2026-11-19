"""KanbanFlow Task & Project Management Domain Template.

Provides complete, production-grade implementations for all 16 planned taskflow files:
- 4 Kanban Columns (Backlog, In Progress, Review, Done), Task Creation, Priority Tags, Move Controls
- SQLite-backed persistence for tasks and status transitions
- RESTful FastAPI endpoints with Pydantic validation
- Complete React 18 TypeScript components, board, cards, modals, and API service
"""

from typing import Optional


def get_taskflow_file(path: str, project_name: str, project_desc: str) -> Optional[str]:
    norm = path.replace("\\", "/").strip()
    slug = project_name.lower().replace(" ", "-")

    if norm == "frontend/package.json":
        return f"""{{
  "name": "{slug}-frontend",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {{
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  }},
  "dependencies": {{
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "lucide-react": "^0.344.0"
  }},
  "devDependencies": {{
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.1",
    "typescript": "^5.5.3",
    "vite": "^5.4.1"
  }}
}}"""

    if norm == "frontend/index.html":
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{project_name} — Kanban Taskflow</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    body {{ margin: 0; font-family: 'Plus Jakarta Sans', sans-serif; background: #070b14; color: #f8fafc; }}
    .app-root {{ max-width: 1400px; margin: 0 auto; padding: 2rem; }}
  </style>
</head>
<body>
  <div id="root">
    <div class="app-root">
      <header style="border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:1rem; display:flex; justify-content:space-between; align-items:center;">
        <div>
          <span style="color:#38bdf8; font-size:0.8rem; font-weight:700;">KANBANFLOW PRO</span>
          <h1 id="app-title" data-testid="app-title" style="margin:0.25rem 0;">{project_name}</h1>
          <p style="color:#94a3b8; margin:0;">{project_desc}</p>
        </div>
        <button onclick="promptCreateTask()" data-testid="btn-new-task" style="background:#38bdf8; color:#090d16; border:none; padding:0.6rem 1.2rem; border-radius:8px; font-weight:700; cursor:pointer;">+ Create Task</button>
      </header>
      <main style="display:grid; grid-template-columns:repeat(4, 1fr); gap:1.25rem; margin-top:2rem;">
        <div style="background:#111827; border-radius:10px; padding:1rem; border:1px solid rgba(255,255,255,0.06);">
          <h3 style="font-size:0.9rem; text-transform:uppercase; color:#94a3b8; margin-top:0;">Backlog</h3>
          <div id="col-backlog" data-testid="column-backlog"></div>
        </div>
        <div style="background:#111827; border-radius:10px; padding:1rem; border:1px solid rgba(255,255,255,0.06);">
          <h3 style="font-size:0.9rem; text-transform:uppercase; color:#38bdf8; margin-top:0;">In Progress</h3>
          <div id="col-in-progress" data-testid="column-in-progress"></div>
        </div>
        <div style="background:#111827; border-radius:10px; padding:1rem; border:1px solid rgba(255,255,255,0.06);">
          <h3 style="font-size:0.9rem; text-transform:uppercase; color:#fbbf24; margin-top:0;">In Review</h3>
          <div id="col-review" data-testid="column-review"></div>
        </div>
        <div style="background:#111827; border-radius:10px; padding:1rem; border:1px solid rgba(255,255,255,0.06);">
          <h3 style="font-size:0.9rem; text-transform:uppercase; color:#34d399; margin-top:0;">Completed</h3>
          <div id="col-done" data-testid="column-done"></div>
        </div>
      </main>
    </div>
  </div>
  <script>
    let tasks = [
      {{ id: "TSK-1", title: "Implement Auth Guard & JWT Validator", status: "in_progress", priority: "HIGH", assignee: "Marcus Vance" }},
      {{ id: "TSK-2", title: "Design High-Density SKU Data Grid", status: "done", priority: "MEDIUM", assignee: "Elena Rostova" }},
      {{ id: "TSK-3", title: "Configure Isolated Docker Preview Runtime", status: "backlog", priority: "HIGH", assignee: "System Architect" }},
      {{ id: "TSK-4", title: "Database Migration Script for v2.0", status: "review", priority: "LOW", assignee: "DevOps Engineer" }}
    ];

    function renderTasks() {{
      const cols = {{
        'backlog': document.getElementById('col-backlog'),
        'in_progress': document.getElementById('col-in-progress'),
        'review': document.getElementById('col-review'),
        'done': document.getElementById('col-done')
      }};

      Object.values(cols).forEach(c => c.innerHTML = '');

      tasks.forEach(t => {{
        const c = cols[t.status] || cols['backlog'];
        const card = document.createElement('div');
        card.style = 'background:#1a2234; border:1px solid rgba(255,255,255,0.08); border-radius:8px; padding:0.9rem; margin-bottom:0.75rem;';
        card.setAttribute('data-testid', 'task-card-' + t.id);
        card.innerHTML = `
          <div style="display:flex; justify-content:space-between; font-size:0.75rem; margin-bottom:0.4rem;">
            <span style="color:#38bdf8; font-weight:700;">${{t.id}}</span>
            <span style="color:${{t.priority === 'HIGH' ? '#f87171' : '#34d399'}}">${{t.priority}}</span>
          </div>
          <div style="font-size:0.95rem; font-weight:600; margin-bottom:0.5rem;">${{t.title}}</div>
          <div style="display:flex; justify-content:space-between; align-items:center; font-size:0.8rem; color:#94a3b8;">
            <span>👤 ${{t.assignee}}</span>
            <select onchange="moveTask('${{t.id}}', this.value)" style="background:#090d16; border:1px solid rgba(255,255,255,0.2); color:#fff; font-size:0.75rem; border-radius:4px; padding:0.15rem 0.3rem;">
              <option value="backlog" ${{t.status==='backlog'?'selected':''}}>Backlog</option>
              <option value="in_progress" ${{t.status==='in_progress'?'selected':''}}>In Progress</option>
              <option value="review" ${{t.status==='review'?'selected':''}}>Review</option>
              <option value="done" ${{t.status==='done'?'selected':''}}>Done</option>
            </select>
          </div>
        `;
        c.appendChild(card);
      }});
    }}

    function moveTask(id, newStatus) {{
      const t = tasks.find(x => x.id === id);
      if (t) {{
        t.status = newStatus;
        renderTasks();
      }}
    }}

    function promptCreateTask() {{
      const title = prompt("Enter task title:");
      if (title) {{
        const newId = "TSK-" + (tasks.length + 1);
        tasks.push({{ id: newId, title, status: "backlog", priority: "MEDIUM", assignee: "Developer" }});
        renderTasks();
      }}
    }}

    renderTasks();
  </script>
</body>
</html>"""

    if norm == "frontend/src/main.tsx":
        return """import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './styles/App.css';

const root = document.getElementById('root');
if (root) {
  ReactDOM.createRoot(root).render(<App />);
}
"""

    if norm == "frontend/src/App.tsx":
        return f"""import React, {{ useState, useEffect }} from 'react';
import {{ KanbanBoard }} from './components/KanbanBoard';
import {{ TaskForm }} from './components/TaskForm';
import {{ getTasks, createTask, updateTaskStatus, Task }} from './services/api';
import './styles/App.css';

export default function App() {{
  const [tasks, setTasks] = useState<Task[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const loadTasks = async () => {{
    try {{
      const data = await getTasks();
      setTasks(data);
    }} catch (err) {{}}
  }};

  useEffect(() => {{
    loadTasks();
  }}, []);

  const handleCreate = async (title: string, priority: string, assignee: string) => {{
    try {{
      await createTask({{ title, priority, assignee, status: 'backlog' }});
      setIsModalOpen(false);
      await loadTasks();
    }} catch (err: any) {{
      alert(err.message || 'Failed to create task');
    }}
  }};

  const handleMove = async (taskId: string, newStatus: string) => {{
    try {{
      await updateTaskStatus(taskId, newStatus);
      await loadTasks();
    }} catch (err) {{}}
  }};

  return (
    <div className="taskflow-container">
      <header className="board-header">
        <div>
          <span className="brand-tag">KanbanFlow</span>
          <h1 data-testid="app-title">{project_name}</h1>
          <p className="subtitle">{project_desc}</p>
        </div>
        <button
          className="btn btn-primary"
          onClick={{() => setIsModalOpen(true)}}
          data-testid="btn-create-task"
        >
          + Add Task
        </button>
      </header>

      <main className="board-main" data-testid="kanban-board-view">
        <KanbanBoard tasks={{tasks}} onMoveTask={{handleMove}} />
      </main>

      {{isModalOpen && (
        <TaskForm onClose={{() => setIsModalOpen(false)}} onSubmit={{handleCreate}} />
      )}}
    </div>
  );
}}
"""

    if norm == "frontend/src/components/KanbanBoard.tsx":
        return """import React from 'react';
import { Task } from '../services/api';
import { TaskCard } from './TaskCard';

interface KanbanBoardProps {
  tasks: Task[];
  onMoveTask: (taskId: string, status: string) => void;
}

const COLUMNS = [
  { id: 'backlog', title: 'Backlog' },
  { id: 'in_progress', title: 'In Progress' },
  { id: 'review', title: 'In Review' },
  { id: 'done', title: 'Completed' },
];

export const KanbanBoard: React.FC<KanbanBoardProps> = ({ tasks, onMoveTask }) => {
  return (
    <div className="kanban-grid" data-testid="kanban-columns-grid">
      {COLUMNS.map((col) => {
        const colTasks = tasks.filter((t) => t.status === col.id);
        return (
          <div key={col.id} className="kanban-column" data-testid={`column-${col.id}`}>
            <div className="column-header">
              <h3>{col.title}</h3>
              <span className="task-count">{colTasks.length}</span>
            </div>
            <div className="column-tasks">
              {colTasks.map((t) => (
                <TaskCard key={t.id} task={t} onMove={onMoveTask} />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
};
"""

    if norm == "frontend/src/components/TaskCard.tsx":
        return """import React from 'react';
import { Task } from '../services/api';

interface TaskCardProps {
  task: Task;
  onMove: (taskId: string, status: string) => void;
}

export const TaskCard: React.FC<TaskCardProps> = ({ task, onMove }) => {
  return (
    <div className="task-card" data-testid={`task-card-${task.id}`}>
      <div className="card-top">
        <span className="task-id">{task.id}</span>
        <span className={`priority-tag priority-${task.priority.toLowerCase()}`}>
          {task.priority}
        </span>
      </div>
      <h4 className="task-title">{task.title}</h4>
      <div className="card-bottom">
        <span className="assignee">👤 {task.assignee || 'Unassigned'}</span>
        <select
          value={task.status}
          onChange={(e) => onMove(task.id, e.target.value)}
          className="status-selector"
        >
          <option value="backlog">Backlog</option>
          <option value="in_progress">In Progress</option>
          <option value="review">Review</option>
          <option value="done">Done</option>
        </select>
      </div>
    </div>
  );
};
"""

    if norm == "frontend/src/components/TaskForm.tsx":
        return """import React, { useState } from 'react';

interface TaskFormProps {
  onClose: () => void;
  onSubmit: (title: string, priority: string, assignee: string) => void;
}

export const TaskForm: React.FC<TaskFormProps> = ({ onClose, onSubmit }) => {
  const [title, setTitle] = useState('');
  const [priority, setPriority] = useState('MEDIUM');
  const [assignee, setAssignee] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    onSubmit(title.trim(), priority, assignee.trim() || 'Team Member');
  };

  return (
    <div className="modal-backdrop">
      <div className="modal-card" data-testid="task-form-modal">
        <div className="modal-header">
          <h3>Create New Task</h3>
          <button className="btn-close" onClick={onClose}>
            &times;
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Task Title</label>
            <input
              type="text"
              className="form-control"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              data-testid="input-task-title"
            />
          </div>

          <div className="form-group">
            <label>Priority</label>
            <select
              className="form-control"
              value={priority}
              onChange={(e) => setPriority(e.target.value)}
            >
              <option value="LOW">Low</option>
              <option value="MEDIUM">Medium</option>
              <option value="HIGH">High</option>
            </select>
          </div>

          <div className="form-group">
            <label>Assignee</label>
            <input
              type="text"
              className="form-control"
              value={assignee}
              onChange={(e) => setAssignee(e.target.value)}
              placeholder="e.g. Developer Name"
            />
          </div>

          <div className="modal-actions">
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" data-testid="btn-confirm-task">
              Create Task
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
"""

    if norm == "frontend/src/services/api.ts":
        return """/**
 * REST API Client for KanbanFlow Backend.
 */

export interface Task {
  id: string;
  title: string;
  status: string;
  priority: string;
  assignee: string;
}

const API_BASE = '/api/tasks';

export async function getTasks(): Promise<Task[]> {
  const res = await fetch(`${API_BASE}`);
  if (!res.ok) throw new Error('Failed to fetch tasks');
  return res.json();
}

export async function createTask(task: Partial<Task>): Promise<Task> {
  const res = await fetch(`${API_BASE}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(task),
  });
  if (!res.ok) throw new Error('Failed to create task');
  return res.json();
}

export async function updateTaskStatus(taskId: string, status: string): Promise<any> {
  const res = await fetch(`${API_BASE}/${taskId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status }),
  });
  if (!res.ok) throw new Error('Failed to update task status');
  return res.json();
}
"""

    if norm == "frontend/src/styles/App.css":
        return """:root {
  --bg: #070b14;
  --card: #111827;
  --card-subtle: #1a2234;
  --accent: #38bdf8;
  --text: #f8fafc;
  --muted: #94a3b8;
}

body {
  margin: 0;
  font-family: sans-serif;
  background: var(--bg);
  color: var(--text);
}

.taskflow-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
}

.board-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(255,255,255,0.1);
  padding-bottom: 1.5rem;
}

.brand-tag {
  color: var(--accent);
  font-weight: 700;
  font-size: 0.8rem;
  text-transform: uppercase;
}

.kanban-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1.25rem;
  margin-top: 2rem;
}

.kanban-column {
  background: var(--card);
  border-radius: 10px;
  padding: 1rem;
  border: 1px solid rgba(255,255,255,0.06);
  min-height: 480px;
}

.column-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(255,255,255,0.05);
  padding-bottom: 0.5rem;
  margin-bottom: 1rem;
}

.column-header h3 {
  font-size: 0.85rem;
  text-transform: uppercase;
  color: var(--muted);
  margin: 0;
}

.task-count {
  background: rgba(255,255,255,0.1);
  padding: 0.1rem 0.5rem;
  border-radius: 9999px;
  font-size: 0.75rem;
}

.task-card {
  background: var(--card-subtle);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 8px;
  padding: 0.9rem;
  margin-bottom: 0.75rem;
}

.card-top {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  margin-bottom: 0.4rem;
}

.task-id {
  color: var(--accent);
  font-weight: 700;
}

.priority-tag {
  font-weight: 700;
  font-size: 0.7rem;
}

.priority-high { color: #f87171; }
.priority-medium { color: #fbbf24; }
.priority-low { color: #34d399; }

.task-title {
  font-size: 0.95rem;
  margin: 0.25rem 0 0.5rem 0;
}

.card-bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.8rem;
  color: var(--muted);
}

.status-selector {
  background: #090d16;
  border: 1px solid rgba(255,255,255,0.2);
  color: #fff;
  font-size: 0.75rem;
  border-radius: 4px;
}

.btn {
  padding: 0.5rem 1rem;
  border-radius: 6px;
  border: none;
  font-weight: 600;
  cursor: pointer;
}

.btn-primary {
  background: var(--accent);
  color: #090d16;
}

.btn-secondary {
  background: rgba(255,255,255,0.1);
  color: #fff;
}

.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.6);
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-card {
  background: var(--card);
  border: 1px solid var(--accent);
  border-radius: 12px;
  padding: 1.5rem;
  width: 100%;
  max-width: 440px;
}
"""

    if norm == "backend/requirements.txt":
        return """fastapi>=0.110.0
uvicorn>=0.28.0
pydantic>=2.6.0
pydantic-settings>=2.2.0
"""

    if norm == "backend/app/main.py":
        return f"""\"\"\"FastAPI Application Entrypoint for {project_name}.\"\"\"

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.api import router as tasks_router

settings = get_settings()

app = FastAPI(title="{project_name}", description="{project_desc}", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {{"status": "ok", "app": "{project_name}"}}

app.include_router(tasks_router, prefix="/api/tasks", tags=["tasks"])
"""

    if norm == "backend/app/config.py":
        return """\"\"\"Application configuration using Pydantic Settings.\"\"\"

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    app_name: str = "KanbanFlow Task Manager"
    allowed_origins: List[str] = ["*"]
    database_url: str = "sqlite:///./tasks.db"

    class Config:
        env_file = ".env"


def get_settings() -> Settings:
    return Settings()
"""

    if norm == "backend/app/models.py":
        return """\"\"\"Domain Models & Pydantic Schemas for Task Operations.\"\"\"

from pydantic import BaseModel
from typing import Optional


class Task(BaseModel):
    id: str
    title: str
    status: str
    priority: str = "MEDIUM"
    assignee: str = "Developer"


class TaskCreate(BaseModel):
    title: str
    priority: str = "MEDIUM"
    assignee: Optional[str] = "Developer"
    status: Optional[str] = "backlog"


class TaskUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    assignee: Optional[str] = None
"""

    if norm == "backend/app/api.py":
        return """\"\"\"REST API Router for Tasks.\"\"\"

from fastapi import APIRouter
from typing import List
from app.models import Task, TaskCreate, TaskUpdate
from app.persistence import repository

router = APIRouter()


@router.get("", response_model=List[Task])
def list_tasks():
    return repository.list_tasks()


@router.post("", response_model=Task)
def create_task(payload: TaskCreate):
    return repository.create_task(payload)


@router.put("/{task_id}")
def update_task(task_id: str, payload: TaskUpdate):
    return repository.update_task_status(task_id, payload.status or "backlog")
"""

    if norm == "backend/app/persistence.py":
        return """\"\"\"SQLite-backed Persistent Repository for Tasks.\"\"\"

import sqlite3
import uuid
from typing import List
from app.models import Task, TaskCreate


class TaskRepository:
    def __init__(self, db_path: str = "tasks.db"):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                status TEXT NOT NULL,
                priority TEXT NOT NULL,
                assignee TEXT NOT NULL
            )
        ''')
        conn.commit()

        cur.execute('SELECT COUNT(*) FROM tasks')
        if cur.fetchone()[0] == 0:
            seed = [
                ("TSK-1", "Implement Auth Guard & JWT Validator", "in_progress", "HIGH", "Marcus Vance"),
                ("TSK-2", "Design High-Density SKU Data Grid", "done", "MEDIUM", "Elena Rostova"),
                ("TSK-3", "Configure Isolated Docker Preview Runtime", "backlog", "HIGH", "System Architect"),
                ("TSK-4", "Database Migration Script for v2.0", "review", "LOW", "DevOps Engineer"),
            ]
            for t in seed:
                cur.execute('INSERT INTO tasks VALUES (?, ?, ?, ?, ?)', t)
            conn.commit()
        conn.close()

    def list_tasks(self) -> List[Task]:
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute('SELECT * FROM tasks')
        rows = cur.fetchall()
        conn.close()
        return [
            Task(
                id=r['id'],
                title=r['title'],
                status=r['status'],
                priority=r['priority'],
                assignee=r['assignee'],
            )
            for r in rows
        ]

    def create_task(self, t: TaskCreate) -> Task:
        conn = self._get_conn()
        cur = conn.cursor()
        new_id = f"TSK-{uuid.uuid4().hex[:4].upper()}"
        cur.execute('INSERT INTO tasks VALUES (?, ?, ?, ?, ?)', (new_id, t.title, t.status or "backlog", t.priority, t.assignee or "Developer"))
        conn.commit()
        conn.close()
        return Task(id=new_id, title=t.title, status=t.status or "backlog", priority=t.priority, assignee=t.assignee or "Developer")

    def update_task_status(self, task_id: str, new_status: str) -> dict:
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute('UPDATE tasks SET status = ? WHERE id = ?', (new_status, task_id))
        conn.commit()
        conn.close()
        return {"status": "updated", "task_id": task_id, "new_status": new_status}


repository = TaskRepository()
"""

    if norm == "README.md":
        return f"""# {project_name}

{project_desc}

## Overview
KanbanFlow provides agile sprint management, 4-stage Kanban columns, and task lifecycle tracking.
"""

    return None
