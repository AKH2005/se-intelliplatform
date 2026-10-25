"""SE IntelliPlatform Generated Application Preview Server.

Serves live interactive preview applications on Port 8001:
- EventHub: Modern event management, search, category filters, seat capacity constraints, registration & cancellation.
- TaskFlow: Modern task management, status transitions, priorities, due dates.
"""

import sys
import uvicorn
from fastapi import FastAPI, HTTPException, status, Query
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import date

app = FastAPI(title="SE IntelliPlatform - Live Application Preview", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================================================================
# 1. EVENTHUB APPLICATION DATA & CONTRACTS
# ==============================================================================

events_db = [
    {
        "id": 1,
        "title": "Tech Innovation Summit 2026",
        "description": "Annual flagship conference on AI agents, modern cloud architectures, and autonomous software intelligence.",
        "category": "Technology",
        "location": "Hyderabad",
        "date": "2026-11-15",
        "time": "09:30 AM",
        "total_seats": 50,
        "available_seats": 49,
    },
    {
        "id": 2,
        "title": "Global Cloud & AI Architecture Expo",
        "description": "Deep-dive workshop on microservices, event-driven scalability, and production resilience.",
        "category": "Technology",
        "location": "Bengaluru",
        "date": "2026-12-05",
        "time": "10:00 AM",
        "total_seats": 120,
        "available_seats": 118,
    },
    {
        "id": 3,
        "title": "Modern Design Systems & UX Conference",
        "description": "Hands-on masterclass in building sleek design systems, micro-animations, and accessible user experiences.",
        "category": "Design",
        "location": "Mumbai",
        "date": "2026-10-28",
        "time": "11:00 AM",
        "total_seats": 30,
        "available_seats": 15,
    },
    {
        "id": 4,
        "title": "Enterprise Engineering Leadership Forum",
        "description": "Executive roundtable on engineering velocity, developer autonomy, and scaling tech teams.",
        "category": "Business",
        "location": "Delhi",
        "date": "2026-11-20",
        "time": "02:00 PM",
        "total_seats": 25,
        "available_seats": 0,  # Sold out to demonstrate capacity constraint enforcement (REQ-6)
    },
]

registrations_db = []

class EventRegisterRequest(BaseModel):
    user_name: str = "Developer User"
    user_email: str = "developer@se-intelliplatform.local"

@app.get("/api/events")
def get_events(
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
):
    results = events_db
    if category and category.lower() != "all":
        results = [e for e in results if e["category"].lower() == category.lower()]
    if search:
        q = search.lower()
        results = [
            e for e in results
            if q in e["title"].lower() or q in e["description"].lower() or q in e["location"].lower()
        ]
    return results

@app.get("/api/events/{event_id}")
def get_event(event_id: int):
    for e in events_db:
        if e["id"] == event_id:
            return e
    raise HTTPException(status_code=404, detail="Event not found")

@app.post("/api/events/{event_id}/register", status_code=status.HTTP_201_CREATED)
def register_for_event(event_id: int, req: EventRegisterRequest = EventRegisterRequest()):
    for e in events_db:
        if e["id"] == event_id:
            # Capacity check (REQ-6)
            if e["available_seats"] <= 0:
                raise HTTPException(status_code=400, detail="Event has no available seats. Registration prevented.")
            # Check if already registered
            for reg in registrations_db:
                if reg["event_id"] == event_id and reg["user_email"] == req.user_email:
                    raise HTTPException(status_code=400, detail="Already registered for this event.")
            
            # Decrement seat count and save registration
            e["available_seats"] -= 1
            new_reg = {
                "registration_id": len(registrations_db) + 1,
                "event_id": event_id,
                "event_title": e["title"],
                "category": e["category"],
                "location": e["location"],
                "date": e["date"],
                "user_name": req.user_name,
                "user_email": req.user_email,
                "registered_at": "2026-10-06 23:45",
            }
            registrations_db.append(new_reg)
            return {"status": "SUCCESS", "registration": new_reg, "remaining_seats": e["available_seats"]}
    raise HTTPException(status_code=404, detail="Event not found")

@app.delete("/api/events/{event_id}/registration")
def cancel_registration(event_id: int):
    global registrations_db
    reg_to_cancel = None
    for reg in registrations_db:
        if reg["event_id"] == event_id:
            reg_to_cancel = reg
            break
    
    if not reg_to_cancel:
        raise HTTPException(status_code=404, detail="No active registration found for this event.")
    
    # Free up seat
    for e in events_db:
        if e["id"] == event_id:
            e["available_seats"] += 1
            break
            
    registrations_db = [r for r in registrations_db if r["event_id"] != event_id]
    return {"status": "CANCELLED", "message": "Event registration successfully cancelled."}

@app.get("/api/registrations")
def get_registrations():
    return registrations_db

# ==============================================================================
# 2. TASKFLOW APPLICATION DATA & APIS (PRESERVED)
# ==============================================================================

tasks_db = [
    {
        "id": 1,
        "title": "Setup Project Scaffolding",
        "description": "Initialize database models and API routes.",
        "priority": "HIGH",
        "status": "COMPLETED",
        "due_date": "2026-10-15"
    },
    {
        "id": 2,
        "title": "Design Task Management UI",
        "description": "Create responsive task dashboard and action cards.",
        "priority": "MEDIUM",
        "status": "IN_PROGRESS",
        "due_date": "2026-10-20"
    }
]

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    priority: str = "MEDIUM"
    status: str = "PENDING"
    due_date: Optional[str] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[str] = None

@app.get("/api/tasks")
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
    return {"status": "DELETED", "id": task_id}

# ==============================================================================
# 3. INTERACTIVE WEB FRONTEND TEMPLATES
# ==============================================================================

EVENTHUB_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>EventHub — Live Application</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-dark: #0a0f1d;
      --bg-card: #131b2e;
      --bg-card-hover: #1a253f;
      --border: rgba(255, 255, 255, 0.1);
      --accent: #6366f1;
      --accent-hover: #4f46e5;
      --accent-cyan: #06b6d4;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --success: #10b981;
      --danger: #ef4444;
      --warning: #f59e0b;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Plus Jakarta Sans', sans-serif;
      background: var(--bg-dark);
      color: var(--text-main);
      min-height: 100vh;
      padding: 1.5rem 2rem;
    }
    .top-nav {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 1.25rem;
      border-bottom: 1px solid var(--border);
      margin-bottom: 1.5rem;
    }
    .logo-badge {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }
    .logo-badge h1 {
      font-size: 1.4rem;
      font-weight: 700;
      background: linear-gradient(135deg, #a5b4fc, #38bdf8);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    .pill {
      font-size: 0.7rem;
      font-weight: 600;
      padding: 0.2rem 0.6rem;
      border-radius: 9999px;
      background: rgba(99, 102, 241, 0.15);
      color: #a5b4fc;
      border: 1px solid rgba(99, 102, 241, 0.3);
    }
    .nav-tabs {
      display: flex;
      gap: 0.5rem;
    }
    .nav-btn {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--border);
      color: var(--text-muted);
      padding: 0.45rem 1rem;
      border-radius: 8px;
      font-size: 0.82rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
    }
    .nav-btn.active, .nav-btn:hover {
      background: var(--accent);
      color: #fff;
      border-color: var(--accent);
    }
    /* Toolbar */
    .toolbar {
      display: flex;
      gap: 1rem;
      margin-bottom: 1.5rem;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
    }
    .search-box {
      flex: 1;
      min-width: 260px;
      max-width: 450px;
      position: relative;
    }
    .search-input {
      width: 100%;
      background: var(--bg-card);
      border: 1px solid var(--border);
      color: #fff;
      padding: 0.6rem 1rem;
      border-radius: 8px;
      font-size: 0.85rem;
      outline: none;
    }
    .search-input:focus {
      border-color: var(--accent);
    }
    .category-filters {
      display: flex;
      gap: 0.4rem;
    }
    .cat-chip {
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid var(--border);
      color: var(--text-muted);
      padding: 0.35rem 0.8rem;
      border-radius: 6px;
      font-size: 0.78rem;
      cursor: pointer;
      font-weight: 500;
    }
    .cat-chip.active {
      background: rgba(99, 102, 241, 0.2);
      color: #c7d2fe;
      border-color: var(--accent);
    }
    /* Grid */
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
      gap: 1.25rem;
    }
    .event-card {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.25rem;
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
      transition: all 0.2s;
    }
    .event-card:hover {
      background: var(--bg-card-hover);
      transform: translateY(-2px);
      border-color: rgba(99, 102, 241, 0.4);
    }
    .card-top {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 0.5rem;
    }
    .card-title {
      font-size: 1.05rem;
      font-weight: 700;
      color: #fff;
      line-height: 1.3;
    }
    .card-desc {
      font-size: 0.82rem;
      color: var(--text-muted);
      line-height: 1.5;
    }
    .meta-row {
      display: flex;
      align-items: center;
      gap: 1rem;
      font-size: 0.75rem;
      color: #94a3b8;
      padding: 0.5rem 0;
      border-top: 1px solid rgba(255, 255, 255, 0.05);
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }
    .seats-badge {
      font-weight: 700;
      font-size: 0.75rem;
      padding: 0.2rem 0.5rem;
      border-radius: 4px;
    }
    .seats-available { background: rgba(16, 185, 129, 0.15); color: #34d399; }
    .seats-soldout { background: rgba(239, 68, 68, 0.15); color: #f87171; }
    .card-foot {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: auto;
      padding-top: 0.5rem;
    }
    .btn-register {
      background: var(--accent);
      color: #fff;
      border: none;
      padding: 0.5rem 1.1rem;
      border-radius: 8px;
      font-size: 0.82rem;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.2s;
    }
    .btn-register:hover:not(:disabled) { background: var(--accent-hover); }
    .btn-register:disabled {
      background: rgba(255, 255, 255, 0.1);
      color: #64748b;
      cursor: not-allowed;
    }
    .btn-cancel {
      background: rgba(239, 68, 68, 0.15);
      color: #f87171;
      border: 1px solid rgba(239, 68, 68, 0.3);
      padding: 0.4rem 0.9rem;
      border-radius: 6px;
      font-size: 0.78rem;
      font-weight: 600;
      cursor: pointer;
    }
    .btn-cancel:hover { background: rgba(239, 68, 68, 0.25); }
    /* Toast notice */
    #toast {
      position: fixed;
      bottom: 2rem;
      right: 2rem;
      background: #1e1b4b;
      border: 1px solid #6366f1;
      color: #e0e7ff;
      padding: 0.75rem 1.25rem;
      border-radius: 8px;
      font-size: 0.85rem;
      display: none;
      z-index: 999;
      box-shadow: 0 10px 25px rgba(0,0,0,0.5);
    }
  </style>
</head>
<body>
  <div class="top-nav">
    <div class="logo-badge">
      <h1>EventHub</h1>
      <span class="pill">FastAPI + SPA v1.0.0</span>
      <span style="font-size: 0.78rem; color: var(--text-muted);">Runtime: Active (Port 8001)</span>
    </div>
    <div class="nav-tabs">
      <button class="nav-btn active" id="tab-browse" onclick="switchView('browse')">Discover Events</button>
      <button class="nav-btn" id="tab-registered" onclick="switchView('registered')">My Registrations (<span id="reg-count">0</span>)</button>
      <a href="/taskflow" class="nav-btn" style="text-decoration: none;">View TaskFlow App</a>
    </div>
  </div>

  <!-- Browse View -->
  <div id="view-browse">
    <div class="toolbar">
      <div class="search-box">
        <input type="text" id="search-input" class="search-input" placeholder="Search events by title, topic, or city..." oninput="handleSearch()" />
      </div>
      <div class="category-filters">
        <button class="cat-chip active" onclick="setCategory('All', this)">All</button>
        <button class="cat-chip" onclick="setCategory('Technology', this)">Technology</button>
        <button class="cat-chip" onclick="setCategory('Design', this)">Design</button>
        <button class="cat-chip" onclick="setCategory('Business', this)">Business</button>
      </div>
    </div>
    <div id="events-grid" class="grid"></div>
  </div>

  <!-- Registered View -->
  <div id="view-registered" style="display: none;">
    <h2 style="font-size: 1.15rem; margin-bottom: 1rem; color: #fff;">My Registered Events</h2>
    <div id="registered-grid" class="grid"></div>
  </div>

  <div id="toast"></div>

  <script>
    let currentCategory = 'All';
    let currentSearch = '';
    let currentView = 'browse';
    let userRegistrations = [];

    async function fetchEvents() {
      let url = `/api/events?category=${encodeURIComponent(currentCategory)}`;
      if (currentSearch) url += `&search=${encodeURIComponent(currentSearch)}`;
      const res = await fetch(url);
      const events = await res.json();
      renderEvents(events);
    }

    async function fetchRegistrations() {
      const res = await fetch('/api/registrations');
      userRegistrations = await res.json();
      document.getElementById('reg-count').textContent = userRegistrations.length;
      renderRegistrations();
    }

    function renderEvents(events) {
      const grid = document.getElementById('events-grid');
      if (!events || events.length === 0) {
        grid.innerHTML = '<div style="grid-column: 1/-1; padding: 3rem; text-align: center; color: #64748b;">No events match your current filter.</div>';
        return;
      }

      grid.innerHTML = events.map(e => {
        const isReg = userRegistrations.some(r => r.event_id === e.id);
        const isSoldOut = e.available_seats <= 0;
        return `
          <div class="event-card" id="event-card-${e.id}">
            <div class="card-top">
              <div class="card-title">${e.title}</div>
              <span class="pill" style="font-size: 0.68rem;">${e.category}</span>
            </div>
            <div class="card-desc">${e.description}</div>
            <div class="meta-row">
              <span>📍 ${e.location}</span>
              <span>📅 ${e.date}</span>
              <span>⏰ ${e.time}</span>
            </div>
            <div class="card-foot">
              <span class="seats-badge ${isSoldOut ? 'seats-soldout' : 'seats-available'}">
                ${isSoldOut ? 'Sold Out' : `${e.available_seats} Seats Available`}
              </span>
              ${isReg ? `
                <button class="btn-cancel" onclick="cancelReg(${e.id})">Cancel Registration</button>
              ` : `
                <button class="btn-register" ${isSoldOut ? 'disabled' : ''} onclick="registerEvent(${e.id})" id="btn-register-${e.id}">
                  ${isSoldOut ? 'Capacity Full' : 'Register Now'}
                </button>
              `}
            </div>
          </div>
        `;
      }).join('');
    }

    function renderRegistrations() {
      const grid = document.getElementById('registered-grid');
      if (!userRegistrations || userRegistrations.length === 0) {
        grid.innerHTML = '<div style="grid-column: 1/-1; padding: 3rem; text-align: center; color: #64748b;">You have no active event registrations.</div>';
        return;
      }
      grid.innerHTML = userRegistrations.map(r => `
        <div class="event-card">
          <div class="card-top">
            <div class="card-title">${r.event_title}</div>
            <span class="pill" style="font-size: 0.68rem; background: rgba(16,185,129,0.15); color: #34d399; border-color: rgba(16,185,129,0.3);">Confirmed</span>
          </div>
          <div class="meta-row">
            <span>📍 ${r.location}</span>
            <span>📅 ${r.date}</span>
            <span>🏷️ ${r.category}</span>
          </div>
          <div style="font-size: 0.75rem; color: #94a3b8;">Registered for: ${r.user_name} (${r.user_email})</div>
          <div class="card-foot">
            <button class="btn-cancel" onclick="cancelReg(${r.event_id})">Cancel Registration</button>
          </div>
        </div>
      `).join('');
    }

    async function registerEvent(eventId) {
      try {
        const res = await fetch(`/api/events/${eventId}/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_name: 'Developer User', user_email: 'developer@se-intelliplatform.local' })
        });
        const data = await res.json();
        if (!res.ok) {
          showToast(data.detail || 'Registration failed', true);
          return;
        }
        showToast('Successfully registered for ' + data.registration.event_title);
        await fetchRegistrations();
        await fetchEvents();
      } catch (err) {
        showToast('Registration error: ' + err.message, true);
      }
    }

    async function cancelReg(eventId) {
      try {
        const res = await fetch(`/api/events/${eventId}/registration`, {
          method: 'DELETE'
        });
        const data = await res.json();
        showToast(data.message || 'Registration cancelled.');
        await fetchRegistrations();
        await fetchEvents();
      } catch (err) {
        showToast('Cancellation error: ' + err.message, true);
      }
    }

    function setCategory(cat, btn) {
      currentCategory = cat;
      document.querySelectorAll('.cat-chip').forEach(c => c.classList.remove('active'));
      btn.classList.add('active');
      fetchEvents();
    }

    function handleSearch() {
      currentSearch = document.getElementById('search-input').value.trim();
      fetchEvents();
    }

    function switchView(view) {
      currentView = view;
      document.getElementById('view-browse').style.display = view === 'browse' ? 'block' : 'none';
      document.getElementById('view-registered').style.display = view === 'registered' ? 'block' : 'none';
      document.getElementById('tab-browse').classList.toggle('active', view === 'browse');
      document.getElementById('tab-registered').classList.toggle('active', view === 'registered');
    }

    function showToast(msg, isErr = false) {
      const toast = document.getElementById('toast');
      toast.textContent = msg;
      toast.style.borderColor = isErr ? 'var(--danger)' : 'var(--accent)';
      toast.style.display = 'block';
      setTimeout(() => { toast.style.display = 'none'; }, 3500);
    }

    fetchRegistrations().then(() => fetchEvents());
  </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def index_page():
    return HTMLResponse(content=EVENTHUB_HTML)

@app.get("/eventhub", response_class=HTMLResponse)
def eventhub_page():
    return HTMLResponse(content=EVENTHUB_HTML)

TASKFLOW_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>TaskFlow — Live Application</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #0b1120;
      --card-bg: #151d30;
      --border: rgba(255, 255, 255, 0.08);
      --accent: #3b82f6;
      --accent-hover: #2563eb;
      --text: #f8fafc;
      --text-muted: #94a3b8;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Plus Jakarta Sans', sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      padding: 2rem;
    }
    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 1.5rem;
      border-bottom: 1px solid var(--border);
      margin-bottom: 2rem;
    }
    .logo {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }
    .logo h1 { font-size: 1.5rem; font-weight: 700; color: #fff; }
    .badge {
      font-size: 0.7rem;
      font-weight: 600;
      padding: 0.2rem 0.5rem;
      border-radius: 4px;
      background: rgba(59, 130, 246, 0.15);
      color: #60a5fa;
      border: 1px solid rgba(59, 130, 246, 0.3);
    }
    .btn {
      background: var(--accent);
      color: #fff;
      border: none;
      padding: 0.5rem 1rem;
      border-radius: 6px;
      font-weight: 600;
      cursor: pointer;
      font-size: 0.875rem;
      transition: background 0.2s;
    }
    .btn:hover { background: var(--accent-hover); }
    .btn-secondary { background: rgba(255, 255, 255, 0.08); color: var(--text); }
    .btn-secondary:hover { background: rgba(255, 255, 255, 0.12); }
    .btn-danger { background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }
    .btn-danger:hover { background: rgba(239, 68, 68, 0.25); }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      gap: 1.25rem;
    }
    .card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1.25rem;
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
    }
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 0.5rem;
    }
    .card-title { font-weight: 600; font-size: 1rem; }
    .card-desc { font-size: 0.85rem; color: var(--text-muted); line-height: 1.4; }
    .card-meta {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-size: 0.75rem;
    }
    .tag { padding: 0.15rem 0.5rem; border-radius: 4px; font-weight: 600; text-transform: uppercase; }
    .tag-high { background: rgba(239, 68, 68, 0.2); color: #f87171; }
    .tag-med { background: rgba(245, 158, 11, 0.2); color: #fbbf24; }
    .tag-status { background: rgba(16, 185, 129, 0.2); color: #34d399; }
    .tag-pending { background: rgba(148, 163, 184, 0.2); color: #94a3b8; }
    .card-actions {
      margin-top: auto;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding-top: 0.75rem;
      border-top: 1px solid var(--border);
    }
    .modal-overlay {
      display: none;
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(0, 0, 0, 0.7);
      backdrop-filter: blur(4px);
      align-items: center;
      justify-content: center;
      z-index: 1000;
    }
    .modal {
      background: #151d30;
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 1.5rem;
      width: 100%;
      max-width: 450px;
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }
    .form-group { display: flex; flex-direction: column; gap: 0.35rem; }
    .form-label { font-size: 0.8rem; font-weight: 600; color: var(--text-muted); }
    .form-input, .form-select, .form-textarea {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 0.5rem 0.75rem;
      color: #fff;
      font-family: inherit;
      font-size: 0.875rem;
    }
    .modal-actions { display: flex; justify-content: flex-end; gap: 0.5rem; margin-top: 0.5rem; }
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
    <button id="btn-add-task" class="btn" onclick="openModal()">+ Add New Task</button>
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
  <script>
    async function fetchTasks() {
      const res = await fetch('/api/tasks');
      const tasks = await res.json();
      const container = document.getElementById('tasks-container');
      container.innerHTML = tasks.map(t => `
        <div class="card" id="task-card-${t.id}">
          <div class="card-header">
            <div class="card-title">${t.title}</div>
            <span class="tag ${t.priority === 'HIGH' ? 'tag-high' : 'tag-med'}">${t.priority}</span>
          </div>
          <div class="card-desc">${t.description || 'No description provided.'}</div>
          <div class="card-meta">
            <span class="tag ${t.status === 'COMPLETED' ? 'tag-status' : 'tag-pending'}">${t.status}</span>
            <span style="color: var(--text-muted);">Due: ${t.due_date || 'N/A'}</span>
          </div>
          <div class="card-actions">
            <select style="background: rgba(255,255,255,0.06); border: 1px solid var(--border); color: #fff; padding: 0.3rem; border-radius: 4px; font-size: 0.75rem;"
              onchange="updateStatus(${t.id}, this.value)" id="select-status-${t.id}">
              <option value="PENDING" ${t.status === 'PENDING' ? 'selected' : ''}>Pending</option>
              <option value="IN_PROGRESS" ${t.status === 'IN_PROGRESS' ? 'selected' : ''}>In Progress</option>
              <option value="COMPLETED" ${t.status === 'COMPLETED' ? 'selected' : ''}>Completed</option>
            </select>
            <button class="btn btn-danger" style="padding: 0.3rem 0.6rem; font-size: 0.75rem;" onclick="deleteTask(${t.id})" id="btn-delete-${t.id}">Delete</button>
          </div>
        </div>
      `).join('');
    }
    function openModal() { document.getElementById('task-modal').style.display = 'flex'; }
    function closeModal() { document.getElementById('task-modal').style.display = 'none'; }
    async function saveTask() {
      const title = document.getElementById('modal-title').value.trim();
      if (!title) return alert('Title is required');
      const desc = document.getElementById('modal-desc').value.trim();
      const priority = document.getElementById('modal-priority').value;
      const status = document.getElementById('modal-status').value;
      const due_date = document.getElementById('modal-due').value;
      await fetch('/api/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, description: desc, priority, status, due_date })
      });
      closeModal();
      document.getElementById('modal-title').value = '';
      document.getElementById('modal-desc').value = '';
      fetchTasks();
    }
    async function updateStatus(id, newStatus) {
      await fetch(`/api/tasks/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus })
      });
      fetchTasks();
    }
    async function deleteTask(id) {
      await fetch(`/api/tasks/${id}`, { method: 'DELETE' });
      fetchTasks();
    }
    fetchTasks();
  </script>
</body>
</html>
"""

@app.get("/taskflow", response_class=HTMLResponse)
def taskflow_page():
    return HTMLResponse(content=TASKFLOW_HTML)

if __name__ == "__main__":
    uvicorn.run("taskflow_app_server:app", host="127.0.0.1", port=8001, log_level="info", reload=False)
