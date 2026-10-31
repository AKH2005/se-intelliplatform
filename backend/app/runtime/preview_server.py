import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from app.services.preview_api_service import PreviewApiService
"""SE IntelliPlatform Generated Application Preview Server.

Serves live interactive preview applications on Port 8001:
- EventHub: Modern event management, search, category filters, seat capacity constraints, registration & cancellation.
- TaskFlow: Modern task management, status transitions, priorities, due dates.
"""

import sys
from pathlib import Path
DB_PATH = Path(__file__).resolve().parent.parent.parent / 'se_intelliplatform.db'
import sqlite3

def get_db_conn():
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=5.0)
        conn.execute("PRAGMA busy_timeout = 5000")
        return conn
    except Exception:
        return sqlite3.connect(":memory:")

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

active_project_context = {
    "project_id": None,
    "project_name": "ShopSphere",
    "mode": "ecommerce",
}

project_contexts: dict[str, dict] = {}

def detect_mode(name: str = "", desc: str = "") -> str:
    combined = f"{name} {desc}".lower()
    if any(k in combined for k in ["analytics", "kpi", "dashboard", "metric", "executive", "revenue", "bi "]):
        return "analytics"
    if any(k in combined for k in ["event", "meet", "summit", "conference", "ticket"]):
        return "eventhub"
    if any(k in combined for k in ["snake", "arcade", "game", "retro"]):
        return "snake_game"
    if any(k in combined for k in ["shop", "store", "commerce", "cart", "product", "checkout", "market"]):
        return "ecommerce"
    if any(k in combined for k in ["task", "todo", "action", "item", "flow", "kanban"]):
        return "taskflow"
    if any(k in combined for k in ["student", "manage", "employee", "admin", "record", "faculty", "school"]):
        return "management"
    return "custom"

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "app": "SE IntelliPlatform - Live Application Preview",
        "port": 8001,
        "active_project_id": active_project_context.get("project_id"),
        "active_project_name": active_project_context.get("project_name"),
        "active_mode": active_project_context.get("mode", "taskflow"),
    }

@app.post("/api/runtime/context")
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

    mode = detect_mode(p_name, p_desc)
    
    ctx = {
        "project_id": p_id if p_id else None,
        "project_name": p_name,
        "project_description": p_desc,
        "mode": mode,
    }
    active_project_context.update(ctx)
    if p_id:
        project_contexts[p_id] = ctx
    return {"status": "SUCCESS", "context": active_project_context}

def is_dark_mode_active(project_id: Optional[str] = None) -> bool:
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
                if v_num > 1:
                    conn.close()
                    return True
        conn.close()
    except Exception:
        pass
    return bool(runtime_features.get("dark_mode", False))

def sync_tasks_from_db():
    global tasks_db
    try:
        import sqlite3
        conn = get_db_conn()
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

# ==============================================================================
# FAST-PATH RUNTIME FEATURE STATE & AUTHENTICATION ENDPOINTS
# ==============================================================================

runtime_features = {
    "auth": False,
    "modern_ui": False,
    "search": False,
    "dark_mode": False,
    "category_filter": False,
    "login_fixed": True,
}

auth_users_db = [
    {"id": 1, "email": "developer@se-intelliplatform.local", "name": "Developer User", "role": "admin"}
]
active_sessions = set()

class LoginRequest(BaseModel):
    email: str = "developer@se-intelliplatform.local"
    password: str = "password123"

class RegisterRequest(BaseModel):
    name: str = "Developer User"
    email: str = "developer@se-intelliplatform.local"
    password: str = "password123"

@app.get("/api/auth/me")
def get_auth_me():
    if active_sessions:
        return {"authenticated": True, "user": auth_users_db[0]}
    return {"authenticated": False, "user": None}

@app.post("/api/auth/login")
def auth_login(req: LoginRequest):
    active_sessions.add(req.email)
    return {"status": "SUCCESS", "message": "Successfully logged in.", "user": auth_users_db[0]}

@app.post("/api/auth/register")
def auth_register(req: RegisterRequest):
    new_user = {"id": len(auth_users_db) + 1, "email": req.email, "name": req.name, "role": "member"}
    auth_users_db.append(new_user)
    active_sessions.add(req.email)
    return {"status": "SUCCESS", "message": "Successfully registered and logged in.", "user": new_user}

@app.post("/api/auth/logout")
def auth_logout():
    active_sessions.clear()
    return {"status": "SUCCESS", "message": "Logged out."}

@app.get("/api/runtime/features")
def get_runtime_features():
    return {
        "status": "ok",
        "features": runtime_features,
        "active_mode": active_project_context.get("mode", "taskflow"),
    }

@app.post("/api/runtime/features")
def update_runtime_features(payload: dict):
    for k, v in payload.items():
        if k in runtime_features:
            runtime_features[k] = bool(v)
    return {
        "status": "SUCCESS",
        "features": runtime_features,
        "message": "Runtime features updated successfully.",
    }

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
        conn = get_db_conn()
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
                conn = get_db_conn()
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
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM preview_tasks WHERE id = ?", (task_id,))
        conn.commit()
        conn.close()
    except Exception:
        pass
    return {"status": "DELETED", "id": task_id}

@app.get("/tasks")
def get_tasks_root():
    return get_tasks()

@app.post("/tasks", status_code=status.HTTP_201_CREATED)
def create_task_root(task: TaskCreate):
    return create_task(task)

@app.get("/tasks/{task_id}")
def get_task_root(task_id: int):
    return get_task(task_id)

@app.put("/tasks/{task_id}")
def update_task_root(task_id: int, task: TaskUpdate):
    return update_task(task_id, task)

@app.delete("/tasks/{task_id}")
def delete_task_root(task_id: int):
    return delete_task(task_id)

class ScoreCreate(BaseModel):
    score: int
    player_name: Optional[str] = "Player 1"

@app.get("/scores")
@app.get("/api/scores")
async def get_scores_endpoint(project_id: Optional[str] = None):
    p_id = project_id or active_project_context.get("project_id")
    return await PreviewApiService.get_scores(p_id)

@app.post("/scores", status_code=status.HTTP_201_CREATED)
@app.post("/api/scores", status_code=status.HTTP_201_CREATED)
async def add_score_endpoint(payload: ScoreCreate, project_id: Optional[str] = None):
    p_id = project_id or active_project_context.get("project_id")
    return await PreviewApiService.add_score(payload.score, payload.player_name or "Player 1", p_id)

@app.get("/metrics")
@app.get("/api/metrics")
def get_metrics_endpoint(project_id: Optional[str] = None):
    p_id = project_id or active_project_context.get("project_id")
    return PreviewApiService.get_analytics_metrics(p_id)


# ==============================================================================

# ==============================================================================
# 2C. SHOPSPHERE E-COMMERCE APPLICATION DATA & APIS
# ==============================================================================

ecommerce_products_db = [
    {
        "id": 1,
        "name": "Neural Dev Pro Station",
        "category": "Hardware",
        "price": 1499.00,
        "stock": 12,
        "icon": "💻",
        "description": "High-performance developer workstation with 64GB unified memory, optimized for local AI agent inference, container compilation, and parallel microservices.",
        "image_url": "https://images.unsplash.com/photo-1593640408182-31c70c8268f5?w=500&auto=format&fit=crop&q=60"
    },
    {
        "id": 2,
        "name": "Mechanical Ergo Keyboard",
        "category": "Accessories",
        "price": 189.00,
        "stock": 25,
        "icon": "⌨️",
        "description": "Split ergonomic mechanical keyboard with low-profile tactile switches, PBT keycaps, per-key RGB backlighting, and programmable QMK firmware.",
        "image_url": "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=500&auto=format&fit=crop&q=60"
    },
    {
        "id": 3,
        "name": "AI Architecture Suite",
        "category": "Software",
        "price": 299.00,
        "stock": 50,
        "icon": "⚡",
        "description": "Autonomous system design synthesizer, OpenAPI contract generator, and database schema optimizer with full local inference support.",
        "image_url": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=500&auto=format&fit=crop&q=60"
    },
    {
        "id": 4,
        "name": "Ultra-Wide 5K Display",
        "category": "Hardware",
        "price": 899.00,
        "stock": 8,
        "icon": "🖥️",
        "description": "40-inch curved 5K resolution display with 99% DCI-P3 color precision, Thunderbolt 4 96W power delivery, and anti-glare nano-texture coating.",
        "image_url": "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=500&auto=format&fit=crop&q=60"
    },
    {
        "id": 5,
        "name": "Noise-Cancelling Studio Headset",
        "category": "Audio",
        "price": 249.00,
        "stock": 18,
        "icon": "🎧",
        "description": "Precision active noise cancellation with 40mm beryllium drivers, spatial audio tracking, ultra-soft memory foam pads, and 38-hour battery longevity.",
        "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500&auto=format&fit=crop&q=60"
    },
    {
        "id": 6,
        "name": "Cloud Sandbox License",
        "category": "Software",
        "price": 99.00,
        "stock": 100,
        "icon": "☁️",
        "description": "Enterprise isolated Docker runtime cluster with instant container previews, ephemeral testing branches, and automated health probing.",
        "image_url": "https://images.unsplash.com/photo-1544197150-b99a580bb7a8?w=500&auto=format&fit=crop&q=60"
    },
    {
        "id": 7,
        "name": "Precision Laser Trackball Mouse",
        "category": "Accessories",
        "price": 89.00,
        "stock": 15,
        "icon": "🖱️",
        "description": "Ergonomic 20-degree tilt angle trackball mouse with dual wireless connectivity, high-precision optical tracking, and customizable gestures.",
        "image_url": "https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?w=500&auto=format&fit=crop&q=60"
    },
    {
        "id": 8,
        "name": "Thunderbolt 4 Multi-Port Dock",
        "category": "Hardware",
        "price": 229.00,
        "stock": 14,
        "icon": "🔌",
        "description": "14-in-1 high-speed docking station with dual 4K/60Hz display support, 2.5GbE Ethernet, UHS-II SD card reader, and 98W host charging.",
        "image_url": "https://images.unsplash.com/photo-1544652478-6653e09f18a2?w=500&auto=format&fit=crop&q=60"
    }
]

ecommerce_categories_db = [
    {"id": 1, "name": "Hardware", "icon": "💻", "description": "High-performance workstations, displays, and docking stations."},
    {"id": 2, "name": "Software", "icon": "⚡", "description": "Developer licenses, AI platforms, and cloud sandboxes."},
    {"id": 3, "name": "Accessories", "icon": "⌨️", "description": "Ergonomic keyboards, mice, and productivity gear."},
    {"id": 4, "name": "Audio", "icon": "🎧", "description": "Studio-grade headsets and noise-cancelling equipment."}
]

ecommerce_orders_db = [
    {
        "id": 1001,
        "order_number": "ORD-2026-1001",
        "customer_name": "Capstone Engineer",
        "email": "customer@example.com",
        "shipping_address": "456 Tech Parkway",
        "city": "San Francisco",
        "postal_code": "94107",
        "phone": "+1 (555) 234-5678",
        "status": "PROCESSING",
        "items": [
            {"product_id": 2, "name": "Mechanical Ergo Keyboard", "price": 189.00, "qty": 1, "subtotal": 189.00},
            {"product_id": 7, "name": "Precision Laser Trackball Mouse", "price": 89.00, "qty": 1, "subtotal": 89.00}
        ],
        "subtotal": 278.00,
        "tax": 22.24,
        "shipping": 0.00,
        "total": 300.24,
        "created_at": "2026-10-24 16:30"
    }
]

class EcommerceProductCreate(BaseModel):
    name: str
    category: str
    price: float
    stock: int = 10
    description: Optional[str] = ""
    icon: Optional[str] = "📦"

class EcommerceProductUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    description: Optional[str] = None
    icon: Optional[str] = None

class CheckoutRequest(BaseModel):
    customer_name: str
    email: str
    shipping_address: str
    city: str
    postal_code: str
    phone: Optional[str] = ""
    items: List[dict]

class OrderStatusUpdate(BaseModel):
    status: str

@app.get("/api/ecommerce/products")
def get_ecommerce_products(
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    sort: Optional[str] = Query(None)
):
    results = list(ecommerce_products_db)
    if category and category.lower() != "all":
        results = [p for p in results if p["category"].lower() == category.lower()]
    if search:
        q = search.lower().strip()
        results = [p for p in results if q in p["name"].lower() or q in p["description"].lower() or q in p["category"].lower()]
    if sort == "price_asc":
        results.sort(key=lambda x: x["price"])
    elif sort == "price_desc":
        results.sort(key=lambda x: x["price"], reverse=True)
    elif sort == "name_asc":
        results.sort(key=lambda x: x["name"].lower())
    elif sort == "newest":
        results.sort(key=lambda x: x["id"], reverse=True)
    return results

@app.get("/api/ecommerce/products/{product_id}")
def get_ecommerce_product(product_id: int):
    for p in ecommerce_products_db:
        if p["id"] == product_id:
            return p
    raise HTTPException(status_code=404, detail="Product not found")

@app.post("/api/ecommerce/products", status_code=status.HTTP_201_CREATED)
def create_ecommerce_product(payload: EcommerceProductCreate):
    new_id = max([p["id"] for p in ecommerce_products_db], default=0) + 1
    new_product = {
        "id": new_id,
        "name": payload.name,
        "category": payload.category,
        "price": float(payload.price),
        "stock": int(payload.stock),
        "icon": payload.icon or "📦",
        "description": payload.description or "",
        "image_url": "https://images.unsplash.com/photo-1526738549149-8e07eca6c147?w=500&auto=format&fit=crop&q=60"
    }
    ecommerce_products_db.append(new_product)
    return new_product

@app.put("/api/ecommerce/products/{product_id}")
def update_ecommerce_product(product_id: int, payload: EcommerceProductUpdate):
    for p in ecommerce_products_db:
        if p["id"] == product_id:
            if payload.name is not None:
                p["name"] = payload.name
            if payload.category is not None:
                p["category"] = payload.category
            if payload.price is not None:
                p["price"] = float(payload.price)
            if payload.stock is not None:
                p["stock"] = int(payload.stock)
            if payload.description is not None:
                p["description"] = payload.description
            if payload.icon is not None:
                p["icon"] = payload.icon
            return p
    raise HTTPException(status_code=404, detail="Product not found")

@app.delete("/api/ecommerce/products/{product_id}")
def delete_ecommerce_product(product_id: int):
    global ecommerce_products_db
    for p in ecommerce_products_db:
        if p["id"] == product_id:
            ecommerce_products_db = [x for x in ecommerce_products_db if x["id"] != product_id]
            return {"status": "DELETED", "id": product_id}
    raise HTTPException(status_code=404, detail="Product not found")

@app.get("/api/ecommerce/categories")
def get_ecommerce_categories():
    results = []
    for cat in ecommerce_categories_db:
        count = sum(1 for p in ecommerce_products_db if p["category"].lower() == cat["name"].lower())
        results.append({**cat, "product_count": count})
    return results

@app.post("/api/ecommerce/checkout", status_code=status.HTTP_201_CREATED)
def ecommerce_checkout(req: CheckoutRequest):
    if not req.items or len(req.items) == 0:
        raise HTTPException(status_code=400, detail="Cart is empty. Cannot checkout.")
    
    # Inventory validation
    order_items = []
    subtotal = 0.0
    for item in req.items:
        p_id = int(item.get("id") or item.get("product_id") or 0)
        qty = int(item.get("qty") or item.get("quantity") or 1)
        
        product = next((p for p in ecommerce_products_db if p["id"] == p_id), None)
        if not product:
            raise HTTPException(status_code=400, detail=f"Product with ID {p_id} no longer exists.")
        if product["stock"] < qty:
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient stock for '{product['name']}'. Requested: {qty}, Available: {product['stock']}."
            )
        
        # Deduct stock
        product["stock"] -= qty
        line_subtotal = round(product["price"] * qty, 2)
        subtotal += line_subtotal
        order_items.append({
            "product_id": product["id"],
            "name": product["name"],
            "price": product["price"],
            "qty": qty,
            "subtotal": line_subtotal
        })
    
    tax = round(subtotal * 0.08, 2)
    shipping = 0.0 if subtotal >= 100 else 15.00
    total = round(subtotal + tax + shipping, 2)
    
    new_id = max([o["id"] for o in ecommerce_orders_db], default=1000) + 1
    new_order = {
        "id": new_id,
        "order_number": f"ORD-2026-{new_id}",
        "customer_name": req.customer_name,
        "email": req.email,
        "shipping_address": req.shipping_address,
        "city": req.city,
        "postal_code": req.postal_code,
        "phone": req.phone or "",
        "status": "PENDING",
        "items": order_items,
        "subtotal": subtotal,
        "tax": tax,
        "shipping": shipping,
        "total": total,
        "created_at": "2026-10-25 00:45"
    }
    ecommerce_orders_db.insert(0, new_order)
    return {"status": "SUCCESS", "order": new_order}

@app.get("/api/ecommerce/orders")
def get_ecommerce_orders():
    return ecommerce_orders_db

@app.get("/api/ecommerce/orders/{order_id}")
def get_ecommerce_order(order_id: int):
    for o in ecommerce_orders_db:
        if o["id"] == order_id:
            return o
    raise HTTPException(status_code=404, detail="Order not found")

@app.put("/api/ecommerce/orders/{order_id}/status")
def update_ecommerce_order_status(order_id: int, payload: OrderStatusUpdate):
    for o in ecommerce_orders_db:
        if o["id"] == order_id:
            o["status"] = payload.status
            return o
    raise HTTPException(status_code=404, detail="Order not found")

@app.get("/api/ecommerce/admin/stats")
def get_ecommerce_admin_stats():
    valid_orders = [o for o in ecommerce_orders_db if o["status"] != "CANCELLED"]
    rev = sum(o["total"] for o in valid_orders)
    return {
        "total_revenue": round(rev, 2),
        "total_orders": len(ecommerce_orders_db),
        "total_products": len(ecommerce_products_db),
        "low_stock_count": sum(1 for p in ecommerce_products_db if p["stock"] < 10),
        "recent_orders": ecommerce_orders_db[:5]
    }


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

def get_taskflow_html(project_id: Optional[str] = None):
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
    @media (max-width: 640px) {{
      body {{ padding: 0.85rem; }}
      .header {{ flex-direction: column; align-items: stretch; gap: 0.75rem; }}
      .controls {{ flex-direction: column; align-items: stretch; gap: 0.75rem; }}
      .filter-bar {{ overflow-x: auto; padding-bottom: 0.35rem; }}
      .grid {{ grid-template-columns: 1fr; }}
      .card-actions {{ flex-direction: column; align-items: stretch; gap: 0.5rem; }}
    }}
    @media (max-width: 360px) {{
      body {{ padding: 0.5rem; }}
      .logo h1 {{ font-size: 1.25rem; }}
      .btn {{ padding: 0.4rem 0.75rem; font-size: 0.8rem; }}
    }}
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

# 4. ADDITIONAL GENERATED APPLICATION TEMPLATES (SNAKE, E-COMMERCE, MANAGEMENT)
# ==============================================================================

def get_snake_game_html(title: str = "Arcade Snake Game") -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title} — Live Preview</title>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Plus Jakarta Sans', sans-serif;
      background: radial-gradient(circle at 50% 0%, #1e1b4b 0%, #090d16 65%);
      color: #f8fafc;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 1.5rem;
    }}
    .header {{
      text-align: center;
      margin-bottom: 1.25rem;
    }}
    .header h1 {{
      font-size: 1.75rem;
      font-weight: 800;
      background: linear-gradient(135deg, #38bdf8, #818cf8, #c084fc);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      letter-spacing: -0.5px;
    }}
    .header p {{
      color: #94a3b8;
      font-size: 0.85rem;
      margin-top: 0.25rem;
    }}
    .scoreboard {{
      display: flex;
      gap: 1.5rem;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid rgba(255, 255, 255, 0.1);
      backdrop-filter: blur(10px);
      padding: 0.6rem 1.75rem;
      border-radius: 9999px;
      margin-bottom: 1.25rem;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.9rem;
    }}
    .score-item span {{ color: #38bdf8; font-weight: 700; }}
    .canvas-wrapper {{
      position: relative;
      border-radius: 16px;
      padding: 4px;
      background: linear-gradient(135deg, rgba(56, 189, 248, 0.3), rgba(129, 140, 248, 0.2), rgba(192, 132, 252, 0.3));
      box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6), 0 0 30px rgba(56, 189, 248, 0.15);
    }}
    canvas {{
      background: #0b101e;
      border-radius: 12px;
      display: block;
      max-width: 100%;
      height: auto;
    }}
    .canvas-wrapper {{
      max-width: 100%;
    }}
    .scoreboard {{
      flex-wrap: wrap;
      justify-content: center;
      gap: 0.75rem;
    }}
    .controls {{
      margin-top: 1.25rem;
      display: flex;
      flex-wrap: wrap;
      justify-content: center;
      gap: 0.75rem;
      align-items: center;
    }}
    .btn {{
      background: linear-gradient(135deg, #3b82f6, #6366f1);
      color: #fff;
      border: none;
      padding: 0.55rem 1.25rem;
      border-radius: 8px;
      font-weight: 600;
      font-size: 0.85rem;
      cursor: pointer;
      transition: all 0.2s;
    }}
    .btn:hover {{ transform: translateY(-1px); box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4); }}
    .btn-secondary {{ background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.15); }}
    .btn-secondary:hover {{ background: rgba(255, 255, 255, 0.15); box-shadow: none; }}
    .d-pad {{
      margin-top: 1.25rem;
      display: grid;
      grid-template-columns: repeat(3, 44px);
      grid-template-rows: repeat(2, 44px);
      gap: 6px;
    }}
    .d-btn {{
      background: rgba(255, 255, 255, 0.06);
      border: 1px solid rgba(255, 255, 255, 0.12);
      color: #fff;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.1rem;
      cursor: pointer;
    }}
    .d-btn:active {{ background: #6366f1; }}
  </style>
</head>
<body>
  <div class="header">
    <h1>{title}</h1>
    <p>Use Arrow Keys or WASD to navigate. Eat glowing energy orbs.</p>
  </div>

  <div class="scoreboard">
    <div class="score-item">SCORE: <span id="val-score">0</span></div>
    <div class="score-item">HIGH: <span id="val-high">0</span></div>
    <div class="score-item">SPEED: <span id="val-speed">1x</span></div>
  </div>

  <div class="canvas-wrapper">
    <canvas id="gameCanvas" width="400" height="400"></canvas>
  </div>

  <div class="controls">
    <button class="btn" id="btn-start" onclick="togglePlay()">Start Game</button>
    <button class="btn btn-secondary" onclick="resetGame()">Reset</button>
    <select id="speed-select" onchange="setSpeed(this.value)" style="background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.15); color: #fff; padding: 0.5rem; border-radius: 8px; font-size: 0.85rem;">
      <option value="120">Normal</option>
      <option value="80">Fast</option>
      <option value="50">Insane</option>
      <option value="160">Casual</option>
    </select>
  </div>

  <div class="d-pad">
    <div></div>
    <button class="d-btn" onclick="changeDir('UP')">▲</button>
    <div></div>
    <button class="d-btn" onclick="changeDir('LEFT')">◀</button>
    <button class="d-btn" onclick="changeDir('DOWN')">▼</button>
    <button class="d-btn" onclick="changeDir('RIGHT')">▶</button>
  </div>

  <script>
    const canvas = document.getElementById('gameCanvas');
    const ctx = canvas.getContext('2d');
    const GRID_SIZE = 20;
    const TILE_COUNT = canvas.width / GRID_SIZE;

    let snake = [{{ x: 10, y: 10 }}, {{ x: 9, y: 10 }}, {{ x: 8, y: 10 }}];
    let food = {{ x: 15, y: 10 }};
    let dx = 1, dy = 0;
    let nextDx = 1, nextDy = 0;
    let score = 0;
    let highScore = parseInt(localStorage.getItem('snake_high_score') || '0', 10);
    let gameLoop = null;
    let isRunning = false;
    let speed = 120;

    document.getElementById('val-high').textContent = highScore;

    function drawGrid() {{
      ctx.fillStyle = '#0b101e';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.03)';
      for (let x = 0; x < canvas.width; x += GRID_SIZE) {{
        ctx.beginPath();
        ctx.moveTo(x, 0); ctx.lineTo(x, canvas.height);
        ctx.stroke();
      }}
      for (let y = 0; y < canvas.height; y += GRID_SIZE) {{
        ctx.beginPath();
        ctx.moveTo(0, y); ctx.lineTo(canvas.width, y);
        ctx.stroke();
      }}
    }}

    function drawFood() {{
      const cx = food.x * GRID_SIZE + GRID_SIZE / 2;
      const cy = food.y * GRID_SIZE + GRID_SIZE / 2;
      ctx.shadowBlur = 15;
      ctx.shadowColor = '#38bdf8';
      ctx.fillStyle = '#38bdf8';
      ctx.beginPath();
      ctx.arc(cx, cy, GRID_SIZE / 2.5, 0, Math.PI * 2);
      ctx.fill();
      ctx.shadowBlur = 0;
    }}

    function drawSnake() {{
      snake.forEach((seg, i) => {{
        const isHead = i === 0;
        ctx.fillStyle = isHead ? '#818cf8' : '#6366f1';
        ctx.shadowBlur = isHead ? 10 : 0;
        ctx.shadowColor = '#818cf8';
        const r = 4;
        ctx.beginPath();
        ctx.roundRect(seg.x * GRID_SIZE + 1, seg.y * GRID_SIZE + 1, GRID_SIZE - 2, GRID_SIZE - 2, r);
        ctx.fill();
        ctx.shadowBlur = 0;
      }});
    }}

    function move() {{
      dx = nextDx;
      dy = nextDy;
      const head = {{ x: snake[0].x + dx, y: snake[0].y + dy }};

      // Wrap-around edges
      if (head.x < 0) head.x = TILE_COUNT - 1;
      if (head.x >= TILE_COUNT) head.x = 0;
      if (head.y < 0) head.y = TILE_COUNT - 1;
      if (head.y >= TILE_COUNT) head.y = 0;

      // Self collision
      if (snake.some(s => s.x === head.x && s.y === head.y)) {{
        gameOver();
        return;
      }}

      snake.unshift(head);

      if (head.x === food.x && head.y === food.y) {{
        score += 10;
        document.getElementById('val-score').textContent = score;
        if (score > highScore) {{
          highScore = score;
          localStorage.setItem('snake_high_score', highScore);
          document.getElementById('val-high').textContent = highScore;
        }}
        spawnFood();
      }} else {{
        snake.pop();
      }}
    }}

    function spawnFood() {{
      food = {{
        x: Math.floor(Math.random() * TILE_COUNT),
        y: Math.floor(Math.random() * TILE_COUNT)
      }};
      if (snake.some(s => s.x === food.x && s.y === food.y)) spawnFood();
    }}

    function update() {{
      move();
      drawGrid();
      drawFood();
      drawSnake();
    }}

    function togglePlay() {{
      const btn = document.getElementById('btn-start');
      if (isRunning) {{
        clearInterval(gameLoop);
        isRunning = false;
        btn.textContent = 'Resume';
      }} else {{
        gameLoop = setInterval(update, speed);
        isRunning = true;
        btn.textContent = 'Pause';
      }}
    }}

    function gameOver() {{
      clearInterval(gameLoop);
      isRunning = false;
      document.getElementById('btn-start').textContent = 'Restart';
      ctx.fillStyle = 'rgba(0, 0, 0, 0.75)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = '#ef4444';
      ctx.font = '700 24px Plus Jakarta Sans';
      ctx.textAlign = 'center';
      ctx.fillText('GAME OVER', canvas.width / 2, canvas.height / 2 - 10);
      ctx.fillStyle = '#fff';
      ctx.font = '500 14px Plus Jakarta Sans';
      ctx.fillText('Score: ' + score, canvas.width / 2, canvas.height / 2 + 20);

      if (score > 0) {{
        try {{
          var sPayload = JSON.stringify({{ score: score, player_name: 'Player 1' }});
          var apiBase = window.__PREVIEW_API_BASE__ || '';
          fetch(apiBase ? apiBase + '/scores' : '/scores', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: sPayload
          }}).catch(function() {{
            return fetch('/api/scores', {{
              method: 'POST',
              headers: {{ 'Content-Type': 'application/json' }},
              body: sPayload
            }});
          }}).catch(function() {{}});
        }} catch(e) {{}}
      }}
    }}

    function resetGame() {{
      clearInterval(gameLoop);
      isRunning = false;
      snake = [{{ x: 10, y: 10 }}, {{ x: 9, y: 10 }}, {{ x: 8, y: 10 }}];
      dx = 1; dy = 0; nextDx = 1; nextDy = 0;
      score = 0;
      document.getElementById('val-score').textContent = '0';
      document.getElementById('btn-start').textContent = 'Start Game';
      spawnFood();
      drawGrid();
      drawFood();
      drawSnake();
    }}

    function setSpeed(val) {{
      speed = parseInt(val, 10);
      const label = speed <= 50 ? '3x' : speed <= 80 ? '2x' : speed <= 120 ? '1x' : '0.7x';
      document.getElementById('val-speed').textContent = label;
      if (isRunning) {{
        clearInterval(gameLoop);
        gameLoop = setInterval(update, speed);
      }}
    }}

    function changeDir(dir) {{
      if (dir === 'UP' && dy === 0) {{ nextDx = 0; nextDy = -1; }}
      if (dir === 'DOWN' && dy === 0) {{ nextDx = 0; nextDy = 1; }}
      if (dir === 'LEFT' && dx === 0) {{ nextDx = -1; nextDy = 0; }}
      if (dir === 'RIGHT' && dx === 0) {{ nextDx = 1; nextDy = 0; }}
    }}

    window.addEventListener('keydown', e => {{
      if (e.key === 'ArrowUp' || e.key === 'w' || e.key === 'W') changeDir('UP');
      if (e.key === 'ArrowDown' || e.key === 's' || e.key === 'S') changeDir('DOWN');
      if (e.key === 'ArrowLeft' || e.key === 'a' || e.key === 'A') changeDir('LEFT');
      if (e.key === 'ArrowRight' || e.key === 'd' || e.key === 'D') changeDir('RIGHT');
      if (e.key === ' ') {{ e.preventDefault(); togglePlay(); }}
    }});

    resetGame();
  </script>
</body>
</html>"""


def get_ecommerce_html(title: str = "ShopSphere", desc: str = "") -> str:
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title} — Modern E-Commerce Platform</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg-dark: #0a0f1d;
      --bg-card: #131b2e;
      --bg-card-hover: #1a253f;
      --border: rgba(255, 255, 255, 0.08);
      --accent: #3b82f6;
      --accent-hover: #2563eb;
      --accent-glow: rgba(59, 130, 246, 0.25);
      --accent-cyan: #06b6d4;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --success: #10b981;
      --warning: #f59e0b;
      --danger: #ef4444;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
      background: var(--bg-dark);
      color: var(--text);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }}
    /* Top Header */
    header {{
      background: rgba(19, 27, 46, 0.85);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--border);
      position: sticky;
      top: 0;
      z-index: 50;
      padding: 0.85rem 2rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .logo-container {{
      display: flex;
      align-items: center;
      gap: 0.75rem;
      text-decoration: none;
      cursor: pointer;
    }}
    .logo-icon {{
      width: 36px;
      height: 36px;
      border-radius: 10px;
      background: linear-gradient(135deg, #3b82f6, #06b6d4);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.2rem;
    }}
    .logo-text {{
      font-size: 1.35rem;
      font-weight: 800;
      background: linear-gradient(135deg, #60a5fa, #38bdf8);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}
    .nav-links {{
      display: flex;
      align-items: center;
      gap: 1.5rem;
    }}
    .nav-link {{
      color: var(--text-muted);
      text-decoration: none;
      font-size: 0.9rem;
      font-weight: 600;
      transition: color 0.2s;
      cursor: pointer;
    }}
    .nav-link:hover, .nav-link.active {{
      color: #60a5fa;
    }}
    .header-actions {{
      display: flex;
      align-items: center;
      gap: 1rem;
    }}
    .cart-btn {{
      background: rgba(59, 130, 246, 0.15);
      border: 1px solid rgba(59, 130, 246, 0.35);
      color: #60a5fa;
      padding: 0.5rem 1rem;
      border-radius: 9999px;
      font-size: 0.85rem;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 0.5rem;
      transition: all 0.2s;
    }}
    .cart-btn:hover {{
      background: var(--accent);
      color: #fff;
    }}
    .user-pill {{
      display: flex;
      align-items: center;
      gap: 0.5rem;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid var(--border);
      padding: 0.4rem 0.85rem;
      border-radius: 9999px;
      font-size: 0.8rem;
      cursor: pointer;
    }}
    .user-pill:hover {{
      border-color: rgba(255, 255, 255, 0.2);
    }}
    /* Main Layout */
    main {{
      flex: 1;
      max-width: 1240px;
      width: 100%;
      margin: 0 auto;
      padding: 2rem 1.5rem;
    }}
    /* Buttons & Controls */
    .btn {{
      padding: 0.6rem 1.25rem;
      border-radius: 8px;
      font-weight: 600;
      font-size: 0.88rem;
      cursor: pointer;
      border: none;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
      transition: all 0.2s;
    }}
    .btn-primary {{
      background: var(--accent);
      color: #fff;
    }}
    .btn-primary:hover {{
      background: var(--accent-hover);
      box-shadow: 0 4px 14px var(--accent-glow);
    }}
    .btn-secondary {{
      background: rgba(255, 255, 255, 0.06);
      color: var(--text);
      border: 1px solid var(--border);
    }}
    .btn-secondary:hover {{
      background: rgba(255, 255, 255, 0.1);
    }}
    .btn-danger {{
      background: rgba(239, 68, 68, 0.15);
      color: #f87171;
      border: 1px solid rgba(239, 68, 68, 0.3);
    }}
    .btn-danger:hover {{
      background: #ef4444;
      color: #fff;
    }}
    .btn-sm {{
      padding: 0.35rem 0.75rem;
      font-size: 0.8rem;
      border-radius: 6px;
    }}
    .badge {{
      display: inline-flex;
      align-items: center;
      padding: 0.2rem 0.6rem;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 600;
    }}
    .badge-success {{ background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }}
    .badge-warning {{ background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }}
    .badge-danger {{ background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }}
    .badge-info {{ background: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); }}
    /* Cards & Grids */
    .card {{
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 1.5rem;
    }}
    .product-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(270px, 1fr));
      gap: 1.5rem;
    }}
    .product-card {{
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 1.25rem;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      transition: all 0.2s;
    }}
    .product-card:hover {{
      transform: translateY(-4px);
      border-color: rgba(96, 165, 250, 0.4);
      box-shadow: 0 12px 24px rgba(0, 0, 0, 0.4);
    }}
    .product-thumb {{
      width: 100%;
      height: 150px;
      border-radius: 10px;
      background: rgba(255, 255, 255, 0.02);
      border: 1px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 3.5rem;
      margin-bottom: 1rem;
      cursor: pointer;
    }}
    .product-name {{
      font-size: 1.05rem;
      font-weight: 700;
      color: var(--text);
      margin-bottom: 0.35rem;
      cursor: pointer;
    }}
    .product-name:hover {{
      color: #60a5fa;
    }}
    .product-desc {{
      color: var(--text-muted);
      font-size: 0.82rem;
      line-height: 1.4;
      margin-bottom: 1rem;
      flex: 1;
    }}
    .input-field {{
      width: 100%;
      background: rgba(10, 15, 29, 0.7);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 0.65rem 1rem;
      color: var(--text);
      font-family: inherit;
      font-size: 0.88rem;
    }}
    .input-field:focus {{
      outline: none;
      border-color: var(--accent);
      box-shadow: 0 0 0 2px var(--accent-glow);
    }}
    /* Toast notifications */
    #toast {{
      position: fixed;
      bottom: 2rem;
      right: 2rem;
      background: #1e293b;
      border: 1px solid #3b82f6;
      color: #fff;
      padding: 0.75rem 1.25rem;
      border-radius: 8px;
      font-size: 0.88rem;
      display: none;
      z-index: 1000;
      box-shadow: 0 10px 25px rgba(0,0,0,0.5);
      animation: fadeIn 0.3s;
    }}
    /* Modal */
    .modal-overlay {{
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.75);
      backdrop-filter: blur(6px);
      z-index: 100;
      align-items: center;
      justify-content: center;
      padding: 1rem;
    }}
    .modal-box {{
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 16px;
      width: 100%;
      max-width: 520px;
      padding: 2rem;
    }}
  </style>
</head>
<body>
  <header>
    <div class="logo-container" onclick="navigate('/')">
      <div class="logo-icon">🛍️</div>
      <div class="logo-text">{title}</div>
    </div>
    <nav class="nav-links">
      <span class="nav-link" id="nav-home" onclick="navigate('/')">Home</span>
      <span class="nav-link" id="nav-products" onclick="navigate('/products')">Products</span>
      <span class="nav-link" id="nav-categories" onclick="navigate('/categories')">Categories</span>
      <span class="nav-link" id="nav-orders" onclick="navigate('/orders')">Orders</span>
      <span class="nav-link" id="nav-admin" onclick="navigate('/admin/dashboard')">Admin</span>
    </nav>
    <div class="header-actions">
      <button class="cart-btn" onclick="navigate('/cart')">
        🛒 Cart (<span id="header-cart-count">0</span>)
      </button>
      <div class="user-pill" onclick="navigate('/profile')">
        <span id="user-display-name">Alex M.</span>
        <span class="badge badge-info" id="user-role-badge">Customer</span>
      </div>
    </div>
  </header>

  <main id="app-view">
    <!-- Dynamic views render here -->
  </main>

  <!-- Global Toast -->
  <div id="toast"></div>

  <!-- Global Modal for Add/Edit -->
  <div class="modal-overlay" id="global-modal">
    <div class="modal-box" id="modal-content"></div>
  </div>

  <script>
    // State
    let currentUser = JSON.parse(localStorage.getItem('shopsphere_user') || 'null') || {{
      name: 'Capstone Engineer',
      email: 'customer@example.com',
      role: 'CUSTOMER'
    }};
    let cart = JSON.parse(localStorage.getItem('shopsphere_cart') || '[]');
    let currentFilterCategory = 'All';
    let searchQuery = '';
    let sortOption = 'featured';

    function saveCart() {{
      localStorage.setItem('shopsphere_cart', JSON.stringify(cart));
      updateCartBadge();
    }}

    function updateCartBadge() {{
      const count = cart.reduce((acc, c) => acc + c.qty, 0);
      const el = document.getElementById('header-cart-count');
      if (el) el.textContent = count;
    }}

    function showToast(msg) {{
      const t = document.getElementById('toast');
      t.textContent = msg;
      t.style.display = 'block';
      setTimeout(() => {{ t.style.display = 'none'; }}, 2800);
    }}

    function updateHeaderUser() {{
      const nameEl = document.getElementById('user-display-name');
      const roleEl = document.getElementById('user-role-badge');
      if (nameEl) nameEl.textContent = currentUser.name.split(' ')[0];
      if (roleEl) {{
        roleEl.textContent = currentUser.role;
        roleEl.className = currentUser.role === 'ADMIN' ? 'badge badge-warning' : 'badge badge-info';
      }}
    }}

    // Router
    function getRoute() {{
      const hash = window.location.hash.replace(/^#/, '');
      return hash || '/';
    }}

    function navigate(path, pushState = true) {{
      if (pushState) {{
        window.location.hash = path;
      }}
      renderRoute(path);
    }}

    window.addEventListener('hashchange', () => {{
      renderRoute(getRoute());
    }});

    // Views
    async function renderRoute(route) {{
      updateCartBadge();
      updateHeaderUser();
      
      // Update nav active states
      document.querySelectorAll('.nav-link').forEach(el => el.classList.remove('active'));
      if (route === '/' || route === '') document.getElementById('nav-home')?.classList.add('active');
      else if (route.startsWith('/products')) document.getElementById('nav-products')?.classList.add('active');
      else if (route.startsWith('/categories')) document.getElementById('nav-categories')?.classList.add('active');
      else if (route.startsWith('/orders')) document.getElementById('nav-orders')?.classList.add('active');
      else if (route.startsWith('/admin')) document.getElementById('nav-admin')?.classList.add('active');

      const app = document.getElementById('app-view');
      
      if (route === '/' || route === '') {{
        await renderHome(app);
      }} else if (route === '/products') {{
        await renderCatalogue(app);
      }} else if (route.startsWith('/products/')) {{
        const id = parseInt(route.replace('/products/', ''));
        await renderProductDetail(app, id);
      }} else if (route === '/categories') {{
        await renderCategories(app);
      }} else if (route === '/cart') {{
        renderCart(app);
      }} else if (route === '/checkout') {{
        renderCheckout(app);
      }} else if (route === '/orders') {{
        await renderOrders(app);
      }} else if (route.startsWith('/orders/')) {{
        const id = parseInt(route.replace('/orders/', ''));
        await renderOrderDetail(app, id);
      }} else if (route === '/profile') {{
        renderProfile(app);
      }} else if (route === '/login') {{
        renderLogin(app);
      }} else if (route === '/admin/dashboard') {{
        await renderAdminDashboard(app);
      }} else if (route === '/admin/products') {{
        await renderAdminProducts(app);
      }} else if (route === '/admin/orders') {{
        await renderAdminOrders(app);
      }} else {{
        renderNotFound(app);
      }}
    }}

    // Home View
    async function renderHome(container) {{
      let products = [];
      try {{
        const res = await fetch('/api/ecommerce/products');
        products = await res.json();
      }} catch (e) {{}}

      container.innerHTML = `
        <div style="text-align: center; padding: 3rem 1rem 4rem; background: radial-gradient(circle at 50% 30%, rgba(59, 130, 246, 0.15) 0%, transparent 70%);">
          <span class="badge badge-info" style="margin-bottom: 1rem;">Next-Gen Hardware & Software Platform</span>
          <h1 style="font-size: 2.75rem; font-weight: 800; line-height: 1.2; margin-bottom: 1rem;">
            Empower Your Engineering Workflow with <span style="background: linear-gradient(135deg, #60a5fa, #38bdf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{title}</span>
          </h1>
          <p style="color: var(--text-muted); font-size: 1.05rem; max-width: 680px; margin: 0 auto 2rem; line-height: 1.6;">
            {desc or 'Explore our curated inventory of cutting-edge developer workstations, mechanical keyboards, ultra-wide 5K displays, and cloud licenses with verified live stock.'}
          </p>
          <div style="display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap;">
            <button class="btn btn-primary" onclick="navigate('/products')">Browse Product Catalogue →</button>
            <button class="btn btn-secondary" onclick="navigate('/categories')">View Categories</button>
          </div>
        </div>

        <div style="margin-top: 2rem;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
            <h2 style="font-size: 1.4rem; font-weight: 700;">Featured Products</h2>
            <button class="btn btn-secondary btn-sm" onclick="navigate('/products')">View All Products →</button>
          </div>
          <div class="product-grid">
            ${{products.slice(0, 4).map(p => `
              <div class="product-card">
                <div>
                  <div class="product-thumb" onclick="navigate('/products/${{p.id}}')">${{p.icon}}</div>
                  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <span class="badge badge-info">${{p.category}}</span>
                    <span style="font-size: 0.75rem; color: ${{p.stock > 0 ? '#34d399' : '#f87171'}}">
                      ${{p.stock > 0 ? p.stock + ' in stock' : 'Out of Stock'}}
                    </span>
                  </div>
                  <div class="product-name" onclick="navigate('/products/${{p.id}}')">${{p.name}}</div>
                  <div class="product-desc">${{p.description}}</div>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--border);">
                  <span style="font-size: 1.25rem; font-weight: 800; color: #60a5fa;">$${{p.price.toFixed(2)}}</span>
                  <button class="btn btn-primary btn-sm" onclick="addToCart(${{p.id}}, '${{p.name.replace(/'/g, "\\'")}}', ${{p.price}}, '${{p.icon}}', ${{p.stock}})">
                    Add to Cart
                  </button>
                </div>
              </div>
            `).join('')}}
          </div>
        </div>
      `;
    }}

    // Catalogue View
    async function renderCatalogue(container) {{
      container.innerHTML = `<div style="text-align: center; padding: 3rem;"><p>Loading products catalogue...</p></div>`;
      
      let products = [];
      let categories = [];
      try {{
        let url = '/api/ecommerce/products?';
        if (currentFilterCategory !== 'All') url += '&category=' + encodeURIComponent(currentFilterCategory);
        if (searchQuery) url += '&search=' + encodeURIComponent(searchQuery);
        if (sortOption) url += '&sort=' + encodeURIComponent(sortOption);
        
        const [pRes, cRes] = await Promise.all([
          fetch(url),
          fetch('/api/ecommerce/categories')
        ]);
        products = await pRes.json();
        categories = await cRes.json();
      }} catch (e) {{}}

      container.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 2rem; flex-wrap: wrap; gap: 1rem;">
          <div>
            <h1 style="font-size: 1.85rem; font-weight: 800; margin-bottom: 0.35rem;">Product Catalogue</h1>
            <p style="color: var(--text-muted); font-size: 0.9rem;">Search, filter, and discover engineering hardware & software</p>
          </div>
          <div style="display: flex; gap: 0.75rem; align-items: center;">
            <input 
              type="text" 
              id="catalogue-search" 
              placeholder="Search products..." 
              value="${{searchQuery}}"
              oninput="handleSearch(this.value)"
              class="input-field" 
              style="width: 240px;"
            />
            <select id="catalogue-sort" class="input-field" style="width: 170px;" onchange="handleSort(this.value)">
              <option value="featured" ${{sortOption === 'featured' ? 'selected' : ''}}>Featured</option>
              <option value="price_asc" ${{sortOption === 'price_asc' ? 'selected' : ''}}>Price: Low to High</option>
              <option value="price_desc" ${{sortOption === 'price_desc' ? 'selected' : ''}}>Price: High to Low</option>
              <option value="name_asc" ${{sortOption === 'name_asc' ? 'selected' : ''}}>Name: A to Z</option>
            </select>
          </div>
        </div>

        <div style="display: flex; gap: 0.5rem; margin-bottom: 2rem; overflow-x: auto; padding-bottom: 0.5rem;">
          <button 
            class="btn ${{currentFilterCategory === 'All' ? 'btn-primary' : 'btn-secondary'}} btn-sm" 
            onclick="filterCategory('All')"
          >
            All Products
          </button>
          ${{categories.map(c => `
            <button 
              class="btn ${{currentFilterCategory === c.name ? 'btn-primary' : 'btn-secondary'}} btn-sm" 
              onclick="filterCategory('${{c.name}}')"
            >
              ${{c.icon}} ${{c.name}} (${{c.product_count}})
            </button>
          `).join('')}}
        </div>

        ${{products.length === 0 ? `
          <div class="card" style="text-align: center; padding: 4rem;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">🔍</div>
            <h3 style="font-size: 1.2rem; font-weight: 700; margin-bottom: 0.5rem;">No products found</h3>
            <p style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 1.5rem;">Try adjusting your search keywords or category filters.</p>
            <button class="btn btn-secondary" onclick="resetFilters()">Reset Filters</button>
          </div>
        ` : `
          <div class="product-grid">
            ${{products.map(p => `
              <div class="product-card">
                <div>
                  <div class="product-thumb" onclick="navigate('/products/${{p.id}}')">${{p.icon}}</div>
                  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <span class="badge badge-info">${{p.category}}</span>
                    <span style="font-size: 0.75rem; color: ${{p.stock > 0 ? '#34d399' : '#f87171'}}">
                      ${{p.stock > 0 ? p.stock + ' in stock' : 'Out of Stock'}}
                    </span>
                  </div>
                  <div class="product-name" onclick="navigate('/products/${{p.id}}')">${{p.name}}</div>
                  <div class="product-desc">${{p.description}}</div>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--border);">
                  <span style="font-size: 1.25rem; font-weight: 800; color: #60a5fa;">$${{p.price.toFixed(2)}}</span>
                  <button class="btn btn-primary btn-sm" onclick="addToCart(${{p.id}}, '${{p.name.replace(/'/g, "\\'")}}', ${{p.price}}, '${{p.icon}}', ${{p.stock}})">
                    Add to Cart
                  </button>
                </div>
              </div>
            `).join('')}}
          </div>
        `}}
      `;
    }}

    function handleSearch(val) {{
      searchQuery = val;
      renderCatalogue(document.getElementById('app-view'));
    }}

    function handleSort(val) {{
      sortOption = val;
      renderCatalogue(document.getElementById('app-view'));
    }}

    function filterCategory(cat) {{
      currentFilterCategory = cat;
      renderCatalogue(document.getElementById('app-view'));
    }}

    function resetFilters() {{
      searchQuery = '';
      currentFilterCategory = 'All';
      sortOption = 'featured';
      renderCatalogue(document.getElementById('app-view'));
    }}

    // Product Detail View
    async function renderProductDetail(container, productId) {{
      let product = null;
      try {{
        const res = await fetch('/api/ecommerce/products/' + productId);
        if (res.ok) product = await res.json();
      }} catch (e) {{}}

      if (!product) {{
        container.innerHTML = `
          <div class="card" style="text-align: center; padding: 4rem; max-width: 500px; margin: 3rem auto;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">⚠️</div>
            <h2 style="font-size: 1.35rem; font-weight: 700; margin-bottom: 0.5rem;">Product Not Found</h2>
            <p style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 1.5rem;">The product you requested with ID #${{productId}} does not exist or has been removed.</p>
            <button class="btn btn-primary" onclick="navigate('/products')">Back to Catalogue</button>
          </div>
        `;
        return;
      }}

      container.innerHTML = `
        <div style="margin-bottom: 1.5rem;">
          <span style="color: var(--text-muted); font-size: 0.85rem; cursor: pointer;" onclick="navigate('/products')">← Back to Products</span>
        </div>
        <div class="card" style="display: grid; grid-template-columns: 1fr 1.2fr; gap: 3rem; padding: 2.5rem;">
          <div style="display: flex; align-items: center; justify-content: center; background: rgba(255, 255, 255, 0.02); border-radius: 12px; border: 1px solid var(--border); font-size: 8rem; min-height: 320px;">
            ${{product.icon}}
          </div>
          <div style="display: flex; flex-direction: column; justify-content: space-between;">
            <div>
              <div style="display: flex; gap: 0.75rem; align-items: center; margin-bottom: 0.75rem;">
                <span class="badge badge-info">${{product.category}}</span>
                <span class="badge ${{product.stock > 0 ? 'badge-success' : 'badge-danger'}}">
                  ${{product.stock > 0 ? 'In Stock (' + product.stock + ' available)' : 'Out of Stock'}}
                </span>
              </div>
              <h1 style="font-size: 2rem; font-weight: 800; margin-bottom: 0.75rem;">${{product.name}}</h1>
              <div style="font-size: 1.85rem; font-weight: 800; color: #60a5fa; margin-bottom: 1.5rem;">
                $${{product.price.toFixed(2)}}
              </div>
              <div style="line-height: 1.6; color: var(--text-muted); margin-bottom: 2rem;">
                ${{product.description}}
              </div>
            </div>

            <div style="border-top: 1px solid var(--border); padding-top: 1.5rem;">
              <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1.5rem;">
                <span style="font-size: 0.9rem; font-weight: 600;">Quantity:</span>
                <div style="display: flex; align-items: center; gap: 0.5rem; background: rgba(255,255,255,0.05); padding: 0.25rem 0.5rem; border-radius: 8px; border: 1px solid var(--border);">
                  <button class="btn btn-secondary btn-sm" onclick="adjustDetailQty(-1)" style="padding: 0.2rem 0.6rem;">-</button>
                  <span id="detail-qty" style="min-width: 28px; text-align: center; font-weight: 700;">1</span>
                  <button class="btn btn-secondary btn-sm" onclick="adjustDetailQty(1, ${{product.stock}})" style="padding: 0.2rem 0.6rem;">+</button>
                </div>
              </div>
              <button 
                class="btn btn-primary" 
                style="width: 100%; padding: 0.85rem;"
                onclick="addDetailToCart(${{product.id}}, '${{product.name.replace(/'/g, "\\'")}}', ${{product.price}}, '${{product.icon}}', ${{product.stock}})"
              >
                Add to Shopping Cart
              </button>
            </div>
          </div>
        </div>
      `;
    }}

    let detailSelectedQty = 1;
    function adjustDetailQty(delta, maxStock = 99) {{
      detailSelectedQty = Math.max(1, Math.min(maxStock, detailSelectedQty + delta));
      const el = document.getElementById('detail-qty');
      if (el) el.textContent = detailSelectedQty;
    }}

    function addDetailToCart(id, name, price, icon, stock) {{
      addToCart(id, name, price, icon, stock, detailSelectedQty);
      detailSelectedQty = 1;
    }}

    function addToCart(id, name, price, icon, stock, qty = 1) {{
      const existing = cart.find(i => i.id === id);
      if (existing) {{
        if (existing.qty + qty > stock) {{
          alert('Cannot add more than available stock (' + stock + ').');
          return;
        }}
        existing.qty += qty;
      }} else {{
        if (qty > stock) {{
          alert('Cannot add more than available stock (' + stock + ').');
          return;
        }}
        cart.push({{ id, name, price, icon, stock, qty }});
      }}
      saveCart();
      showToast('Added ' + qty + ' × ' + name + ' to cart!');
    }}

    // Categories View
    async function renderCategories(container) {{
      let categories = [];
      try {{
        const res = await fetch('/api/ecommerce/categories');
        categories = await res.json();
      }} catch (e) {{}}

      container.innerHTML = `
        <div style="margin-bottom: 2rem;">
          <h1 style="font-size: 1.85rem; font-weight: 800; margin-bottom: 0.35rem;">Product Categories</h1>
          <p style="color: var(--text-muted); font-size: 0.9rem;">Explore our curated hardware and software collections</p>
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1.5rem;">
          ${{categories.map(c => `
            <div class="card" style="cursor: pointer; transition: all 0.2s;" onclick="filterCategory('${{c.name}}'); navigate('/products');">
              <div style="font-size: 3rem; margin-bottom: 1rem;">${{c.icon}}</div>
              <h3 style="font-size: 1.25rem; font-weight: 700; margin-bottom: 0.35rem;">${{c.name}}</h3>
              <p style="color: var(--text-muted); font-size: 0.85rem; line-height: 1.5; margin-bottom: 1.5rem;">${{c.description}}</p>
              <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--border); padding-top: 1rem;">
                <span class="badge badge-info">${{c.product_count}} Products</span>
                <span style="color: #60a5fa; font-weight: 600; font-size: 0.85rem;">Browse Catalogue →</span>
              </div>
            </div>
          `).join('')}}
        </div>
      `;
    }}

    // Cart View
    function renderCart(container) {{
      const subtotal = cart.reduce((acc, c) => acc + c.price * c.qty, 0);
      const tax = roundTo2(subtotal * 0.08);
      const shipping = subtotal === 0 ? 0 : (subtotal >= 100 ? 0 : 15.00);
      const total = roundTo2(subtotal + tax + shipping);

      if (cart.length === 0) {{
        container.innerHTML = `
          <div class="card" style="text-align: center; padding: 4rem; max-width: 520px; margin: 3rem auto;">
            <div style="font-size: 3.5rem; margin-bottom: 1rem;">🛒</div>
            <h2 style="font-size: 1.4rem; font-weight: 700; margin-bottom: 0.5rem;">Your Cart is Empty</h2>
            <p style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 1.5rem;">You have not added any products to your shopping cart yet.</p>
            <button class="btn btn-primary" onclick="navigate('/products')">Browse Product Catalogue</button>
          </div>
        `;
        return;
      }}

      container.innerHTML = `
        <h1 style="font-size: 1.85rem; font-weight: 800; margin-bottom: 2rem;">Shopping Cart (${{cart.reduce((a,b) => a + b.qty, 0)}} items)</h1>
        <div style="display: grid; grid-template-columns: 1fr 340px; gap: 2rem; align-items: start;">
          <div class="card" style="padding: 1.5rem;">
            <div style="display: flex; flex-direction: column; gap: 1.25rem;">
              ${{cart.map(item => `
                <div style="display: flex; justify-content: space-between; align-items: center; padding-bottom: 1.25rem; border-bottom: 1px solid var(--border);">
                  <div style="display: flex; align-items: center; gap: 1rem;">
                    <div style="width: 54px; height: 54px; border-radius: 8px; background: rgba(255,255,255,0.03); border: 1px solid var(--border); display: flex; align-items: center; justify-content: center; font-size: 1.75rem;">
                      ${{item.icon}}
                    </div>
                    <div>
                      <h4 style="font-size: 0.95rem; font-weight: 700; margin-bottom: 0.25rem;">${{item.name}}</h4>
                      <span style="color: #60a5fa; font-weight: 700; font-size: 0.9rem;">$${{item.price.toFixed(2)}}</span>
                    </div>
                  </div>
                  <div style="display: flex; align-items: center; gap: 1.5rem;">
                    <div style="display: flex; align-items: center; gap: 0.35rem; background: rgba(255,255,255,0.05); padding: 0.2rem 0.4rem; border-radius: 6px; border: 1px solid var(--border);">
                      <button class="btn btn-secondary btn-sm" style="padding: 0.15rem 0.5rem;" onclick="updateCartQty(${{item.id}}, -1)">-</button>
                      <span style="min-width: 24px; text-align: center; font-weight: 700; font-size: 0.85rem;">${{item.qty}}</span>
                      <button class="btn btn-secondary btn-sm" style="padding: 0.15rem 0.5rem;" onclick="updateCartQty(${{item.id}}, 1)">+</button>
                    </div>
                    <span style="font-weight: 800; font-size: 1rem; min-width: 75px; text-align: right;">$${{(item.price * item.qty).toFixed(2)}}</span>
                    <button class="btn btn-danger btn-sm" onclick="removeFromCart(${{item.id}})" title="Remove item">✕</button>
                  </div>
                </div>
              `).join('')}}
            </div>
            <div style="margin-top: 1.5rem; display: flex; justify-content: space-between; align-items: center;">
              <button class="btn btn-secondary btn-sm" onclick="navigate('/products')">← Continue Shopping</button>
              <button class="btn btn-danger btn-sm" onclick="clearCart()">Clear Cart</button>
            </div>
          </div>

          <!-- Order Summary Card -->
          <div class="card" style="padding: 1.75rem;">
            <h3 style="font-size: 1.15rem; font-weight: 700; margin-bottom: 1.25rem;">Order Summary</h3>
            <div style="display: flex; flex-direction: column; gap: 0.75rem; font-size: 0.9rem; padding-bottom: 1.25rem; border-bottom: 1px solid var(--border);">
              <div style="display: flex; justify-content: space-between; color: var(--text-muted);">
                <span>Subtotal</span>
                <span style="color: var(--text); font-weight: 600;">$${{subtotal.toFixed(2)}}</span>
              </div>
              <div style="display: flex; justify-content: space-between; color: var(--text-muted);">
                <span>Estimated Tax (8%)</span>
                <span style="color: var(--text); font-weight: 600;">$${{tax.toFixed(2)}}</span>
              </div>
              <div style="display: flex; justify-content: space-between; color: var(--text-muted);">
                <span>Shipping</span>
                <span style="color: var(--text); font-weight: 600;">${{shipping === 0 ? 'FREE' : '$' + shipping.toFixed(2)}}</span>
              </div>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 1.15rem; font-weight: 800; margin: 1.25rem 0 1.5rem;">
              <span>Total</span>
              <span style="color: #60a5fa;">$${{total.toFixed(2)}}</span>
            </div>
            <button class="btn btn-primary" style="width: 100%; padding: 0.85rem;" onclick="navigate('/checkout')">
              Proceed to Checkout →
            </button>
          </div>
        </div>
      `;
    }}

    function roundTo2(num) {{
      return Math.round(num * 100) / 100;
    }}

    function updateCartQty(id, delta) {{
      const item = cart.find(i => i.id === id);
      if (!item) return;
      if (item.qty + delta <= 0) {{
        removeFromCart(id);
      }} else {{
        if (item.qty + delta > item.stock) {{
          alert('Cannot exceed available stock of ' + item.stock);
          return;
        }}
        item.qty += delta;
        saveCart();
        renderCart(document.getElementById('app-view'));
      }}
    }}

    function removeFromCart(id) {{
      cart = cart.filter(i => i.id !== id);
      saveCart();
      renderCart(document.getElementById('app-view'));
    }}

    function clearCart() {{
      cart = [];
      saveCart();
      renderCart(document.getElementById('app-view'));
    }}

    // Checkout View
    function renderCheckout(container) {{
      if (cart.length === 0) {{
        navigate('/cart');
        return;
      }}

      const subtotal = cart.reduce((acc, c) => acc + c.price * c.qty, 0);
      const tax = roundTo2(subtotal * 0.08);
      const shipping = subtotal >= 100 ? 0 : 15.00;
      const total = roundTo2(subtotal + tax + shipping);

      container.innerHTML = `
        <div style="margin-bottom: 1.5rem;">
          <span style="color: var(--text-muted); font-size: 0.85rem; cursor: pointer;" onclick="navigate('/cart')">← Back to Cart</span>
        </div>
        <h1 style="font-size: 1.85rem; font-weight: 800; margin-bottom: 2rem;">Checkout</h1>
        <div style="display: grid; grid-template-columns: 1fr 360px; gap: 2rem; align-items: start;">
          <div class="card">
            <h3 style="font-size: 1.15rem; font-weight: 700; margin-bottom: 1.25rem;">Delivery & Customer Information</h3>
            <div id="checkout-error" style="display: none; padding: 0.75rem 1rem; border-radius: 8px; background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3); color: #f87171; font-size: 0.85rem; margin-bottom: 1.25rem;"></div>
            <form onsubmit="submitCheckout(event)" style="display: flex; flex-direction: column; gap: 1rem;">
              <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                <div>
                  <label style="display: block; font-size: 0.8rem; font-weight: 600; margin-bottom: 0.35rem;">Full Name *</label>
                  <input type="text" id="chk-name" required value="${{currentUser.name}}" class="input-field" placeholder="John Doe" />
                </div>
                <div>
                  <label style="display: block; font-size: 0.8rem; font-weight: 600; margin-bottom: 0.35rem;">Email Address *</label>
                  <input type="email" id="chk-email" required value="${{currentUser.email}}" class="input-field" placeholder="john@example.com" />
                </div>
              </div>
              <div>
                <label style="display: block; font-size: 0.8rem; font-weight: 600; margin-bottom: 0.35rem;">Street Address *</label>
                <input type="text" id="chk-address" required value="100 Silicon Valley Way" class="input-field" placeholder="123 Innovation Drive" />
              </div>
              <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                <div>
                  <label style="display: block; font-size: 0.8rem; font-weight: 600; margin-bottom: 0.35rem;">City *</label>
                  <input type="text" id="chk-city" required value="San Francisco" class="input-field" placeholder="San Francisco" />
                </div>
                <div>
                  <label style="display: block; font-size: 0.8rem; font-weight: 600; margin-bottom: 0.35rem;">Postal Code *</label>
                  <input type="text" id="chk-postal" required value="94105" class="input-field" placeholder="94105" />
                </div>
              </div>
              <div>
                <label style="display: block; font-size: 0.8rem; font-weight: 600; margin-bottom: 0.35rem;">Contact Phone</label>
                <input type="text" id="chk-phone" value="+1 (555) 987-6543" class="input-field" placeholder="+1 (555) 000-0000" />
              </div>
              <div style="margin-top: 1rem; padding: 1rem; border-radius: 8px; background: rgba(59, 130, 246, 0.08); border: 1px solid rgba(59, 130, 246, 0.2); font-size: 0.85rem; color: #93c5fd;">
                💳 <strong>Verified Test Mode:</strong> No real payment or credit card is processed. Live order records and inventory updates will persist directly to database.
              </div>
              <button type="submit" id="chk-submit-btn" class="btn btn-primary" style="margin-top: 1rem; padding: 0.85rem;">
                Complete & Place Test Order ($${{total.toFixed(2)}})
              </button>
            </form>
          </div>

          <!-- Checkout Summary -->
          <div class="card">
            <h3 style="font-size: 1.15rem; font-weight: 700; margin-bottom: 1.25rem;">Items Summary (${{cart.length}})</h3>
            <div style="display: flex; flex-direction: column; gap: 0.85rem; max-height: 240px; overflow-y: auto; margin-bottom: 1.25rem; padding-right: 0.5rem;">
              ${{cart.map(i => `
                <div style="display: flex; justify-content: space-between; font-size: 0.85rem;">
                  <span>${{i.qty}} × ${{i.name}}</span>
                  <span style="font-weight: 600;">$${{(i.price * i.qty).toFixed(2)}}</span>
                </div>
              `).join('')}}
            </div>
            <div style="border-top: 1px solid var(--border); padding-top: 1rem; font-size: 0.88rem; display: flex; flex-direction: column; gap: 0.5rem;">
              <div style="display: flex; justify-content: space-between; color: var(--text-muted);">
                <span>Subtotal</span>
                <span>$${{subtotal.toFixed(2)}}</span>
              </div>
              <div style="display: flex; justify-content: space-between; color: var(--text-muted);">
                <span>Estimated Tax (8%)</span>
                <span>$${{tax.toFixed(2)}}</span>
              </div>
              <div style="display: flex; justify-content: space-between; color: var(--text-muted);">
                <span>Shipping</span>
                <span>${{shipping === 0 ? 'FREE' : '$' + shipping.toFixed(2)}}</span>
              </div>
              <div style="display: flex; justify-content: space-between; font-size: 1.1rem; font-weight: 800; margin-top: 0.5rem; color: #60a5fa;">
                <span>Total</span>
                <span>$${{total.toFixed(2)}}</span>
              </div>
            </div>
          </div>
        </div>
      `;
    }}

    async function submitCheckout(e) {{
      e.preventDefault();
      const errEl = document.getElementById('checkout-error');
      const submitBtn = document.getElementById('chk-submit-btn');
      errEl.style.display = 'none';

      const customer_name = document.getElementById('chk-name').value.trim();
      const email = document.getElementById('chk-email').value.trim();
      const shipping_address = document.getElementById('chk-address').value.trim();
      const city = document.getElementById('chk-city').value.trim();
      const postal_code = document.getElementById('chk-postal').value.trim();
      const phone = document.getElementById('chk-phone').value.trim();

      if (!customer_name || !email || !shipping_address || !city || !postal_code) {{
        errEl.textContent = 'Please fill out all required fields to complete checkout.';
        errEl.style.display = 'block';
        return;
      }}

      submitBtn.disabled = true;
      submitBtn.textContent = 'Processing Order...';

      try {{
        const res = await fetch('/api/ecommerce/checkout', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{
            customer_name,
            email,
            shipping_address,
            city,
            postal_code,
            phone,
            items: cart
          }})
        }});

        const data = await res.json();
        if (!res.ok) {{
          throw new Error(data.detail || 'Failed to place order');
        }}

        // Order placed successfully! Clear cart & navigate to Order Detail
        cart = [];
        saveCart();
        showToast('Order placed successfully!');
        navigate('/orders/' + data.order.id);
      }} catch (err) {{
        errEl.textContent = err.message || 'An error occurred while placing order.';
        errEl.style.display = 'block';
        submitBtn.disabled = false;
        submitBtn.textContent = 'Complete & Place Test Order';
      }}
    }}

    // Orders History View
    async function renderOrders(container) {{
      let orders = [];
      try {{
        const res = await fetch('/api/ecommerce/orders');
        orders = await res.json();
      }} catch (e) {{}}

      container.innerHTML = `
        <div style="margin-bottom: 2rem;">
          <h1 style="font-size: 1.85rem; font-weight: 800; margin-bottom: 0.35rem;">Your Order History</h1>
          <p style="color: var(--text-muted); font-size: 0.9rem;">Track past purchases, shipping status, and receipts</p>
        </div>
        ${{orders.length === 0 ? `
          <div class="card" style="text-align: center; padding: 4rem;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">📦</div>
            <h3 style="font-size: 1.2rem; font-weight: 700; margin-bottom: 0.5rem;">No orders yet</h3>
            <p style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 1.5rem;">You have not completed any purchases yet.</p>
            <button class="btn btn-primary" onclick="navigate('/products')">Browse Catalogue</button>
          </div>
        ` : `
          <div style="display: flex; flex-direction: column; gap: 1.25rem;">
            ${{orders.map(o => `
              <div class="card" style="display: flex; justify-content: space-between; align-items: center; padding: 1.5rem;">
                <div>
                  <div style="display: flex; gap: 0.75rem; align-items: center; margin-bottom: 0.5rem;">
                    <span style="font-weight: 800; font-size: 1.05rem;">${{o.order_number}}</span>
                    <span class="badge ${{o.status === 'DELIVERED' ? 'badge-success' : o.status === 'SHIPPED' ? 'badge-info' : o.status === 'PROCESSING' ? 'badge-warning' : 'badge-danger'}}">
                      ${{o.status}}
                    </span>
                  </div>
                  <div style="font-size: 0.85rem; color: var(--text-muted);">
                    Ordered on ${{o.created_at}} · ${{o.items.length}} item${{o.items.length > 1 ? 's' : ''}}
                  </div>
                  <div style="font-size: 0.82rem; color: #94a3b8; margin-top: 0.35rem;">
                    Recipient: ${{o.customer_name}} (${{o.city}})
                  </div>
                </div>
                <div style="display: flex; align-items: center; gap: 1.5rem;">
                  <span style="font-size: 1.35rem; font-weight: 800; color: #60a5fa;">$${{o.total.toFixed(2)}}</span>
                  <button class="btn btn-secondary btn-sm" onclick="navigate('/orders/${{o.id}}')">
                    View Details →
                  </button>
                </div>
              </div>
            `).join('')}}
          </div>
        `}}
      `;
    }}

    // Order Detail View
    async function renderOrderDetail(container, orderId) {{
      let order = null;
      try {{
        const res = await fetch('/api/ecommerce/orders/' + orderId);
        if (res.ok) order = await res.json();
      }} catch (e) {{}}

      if (!order) {{
        container.innerHTML = `
          <div class="card" style="text-align: center; padding: 4rem; max-width: 500px; margin: 3rem auto;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">⚠️</div>
            <h2 style="font-size: 1.35rem; font-weight: 700; margin-bottom: 0.5rem;">Order Not Found</h2>
            <p style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 1.5rem;">The order with ID #${{orderId}} does not exist or has been removed.</p>
            <button class="btn btn-primary" onclick="navigate('/orders')">Back to Orders</button>
          </div>
        `;
        return;
      }}

      container.innerHTML = `
        <div style="margin-bottom: 1.5rem;">
          <span style="color: var(--text-muted); font-size: 0.85rem; cursor: pointer;" onclick="navigate('/orders')">← Back to Orders</span>
        </div>
        <div class="card" style="padding: 2rem;">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; padding-bottom: 1.5rem; border-bottom: 1px solid var(--border); margin-bottom: 1.5rem;">
            <div>
              <div style="display: flex; gap: 0.75rem; align-items: center; margin-bottom: 0.5rem;">
                <h1 style="font-size: 1.6rem; font-weight: 800;">${{order.order_number}}</h1>
                <span class="badge ${{order.status === 'DELIVERED' ? 'badge-success' : order.status === 'SHIPPED' ? 'badge-info' : order.status === 'PROCESSING' ? 'badge-warning' : 'badge-danger'}}">
                  ${{order.status}}
                </span>
              </div>
              <p style="font-size: 0.85rem; color: var(--text-muted);">Placed on ${{order.created_at}} · Order ID #${{order.id}}</p>
            </div>
            <button class="btn btn-secondary btn-sm" onclick="window.print()">Print Receipt</button>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin-bottom: 2rem;">
            <div style="background: rgba(255, 255, 255, 0.02); padding: 1.25rem; border-radius: 8px; border: 1px solid var(--border);">
              <h4 style="font-size: 0.85rem; font-weight: 700; text-transform: uppercase; color: var(--text-muted); margin-bottom: 0.75rem;">Shipping Address</h4>
              <p style="font-weight: 600; font-size: 0.95rem;">${{order.customer_name}}</p>
              <p style="color: var(--text-muted); font-size: 0.85rem; margin-top: 0.25rem;">${{order.shipping_address}}</p>
              <p style="color: var(--text-muted); font-size: 0.85rem;">${{order.city}}, ${{order.postal_code}}</p>
              ${{order.phone ? `<p style="color: var(--text-muted); font-size: 0.85rem; margin-top: 0.25rem;">Phone: ${{order.phone}}</p>` : ''}}
            </div>
            <div style="background: rgba(255, 255, 255, 0.02); padding: 1.25rem; border-radius: 8px; border: 1px solid var(--border);">
              <h4 style="font-size: 0.85rem; font-weight: 700; text-transform: uppercase; color: var(--text-muted); margin-bottom: 0.75rem;">Payment & Billing</h4>
              <p style="font-weight: 600; font-size: 0.95rem;">Test Order Workflow</p>
              <p style="color: #34d399; font-size: 0.85rem; margin-top: 0.25rem;">Status: Authorized & Paid</p>
              <p style="color: var(--text-muted); font-size: 0.85rem; margin-top: 0.25rem;">Email Receipt: ${{order.email}}</p>
            </div>
          </div>

          <h3 style="font-size: 1.1rem; font-weight: 700; margin-bottom: 1rem;">Purchased Items</h3>
          <div style="display: flex; flex-direction: column; gap: 0.75rem; margin-bottom: 1.5rem;">
            ${{order.items.map(item => `
              <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.85rem 1rem; background: rgba(255,255,255,0.02); border-radius: 8px; border: 1px solid var(--border);">
                <div>
                  <span style="font-weight: 600; font-size: 0.9rem;">${{item.name}}</span>
                  <div style="color: var(--text-muted); font-size: 0.8rem;">Qty: ${{item.qty}} × $${{item.price.toFixed(2)}}</div>
                </div>
                <span style="font-weight: 700; color: #60a5fa;">$${{item.subtotal.toFixed(2)}}</span>
              </div>
            `).join('')}}
          </div>

          <div style="display: flex; justify-content: flex-end;">
            <div style="width: 280px; display: flex; flex-direction: column; gap: 0.5rem; font-size: 0.9rem;">
              <div style="display: flex; justify-content: space-between; color: var(--text-muted);">
                <span>Subtotal</span>
                <span>$${{order.subtotal.toFixed(2)}}</span>
              </div>
              <div style="display: flex; justify-content: space-between; color: var(--text-muted);">
                <span>Tax (8%)</span>
                <span>$${{order.tax.toFixed(2)}}</span>
              </div>
              <div style="display: flex; justify-content: space-between; color: var(--text-muted);">
                <span>Shipping</span>
                <span>${{order.shipping === 0 ? 'FREE' : '$' + order.shipping.toFixed(2)}}</span>
              </div>
              <div style="display: flex; justify-content: space-between; font-size: 1.25rem; font-weight: 800; border-top: 1px solid var(--border); padding-top: 0.75rem; color: #60a5fa;">
                <span>Total</span>
                <span>$${{order.total.toFixed(2)}}</span>
              </div>
            </div>
          </div>
        </div>
      `;
    }}

    // Profile & Auth
    function renderProfile(container) {{
      container.innerHTML = `
        <div class="card" style="max-width: 540px; margin: 2rem auto; padding: 2rem;">
          <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1.5rem;">
            <div style="width: 64px; height: 64px; border-radius: 50%; background: linear-gradient(135deg, #3b82f6, #06b6d4); display: flex; align-items: center; justify-content: center; font-size: 2rem;">
              👤
            </div>
            <div>
              <h2 style="font-size: 1.35rem; font-weight: 800;">${{currentUser.name}}</h2>
              <span class="badge ${{currentUser.role === 'ADMIN' ? 'badge-warning' : 'badge-info'}}">${{currentUser.role}}</span>
            </div>
          </div>
          <div style="display: flex; flex-direction: column; gap: 1rem; font-size: 0.9rem; padding: 1.25rem 0; border-top: 1px solid var(--border); border-bottom: 1px solid var(--border); margin-bottom: 1.5rem;">
            <div style="display: flex; justify-content: space-between;">
              <span style="color: var(--text-muted);">Email</span>
              <span style="font-weight: 600;">${{currentUser.email}}</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
              <span style="color: var(--text-muted);">Account Status</span>
              <span style="color: #34d399; font-weight: 600;">Verified Active</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
              <span style="color: var(--text-muted);">Fast Switch Role</span>
              <button class="btn btn-secondary btn-sm" onclick="toggleUserRole()">
                Switch to ${{currentUser.role === 'ADMIN' ? 'CUSTOMER' : 'ADMIN'}}
              </button>
            </div>
          </div>
          <div style="display: flex; gap: 1rem;">
            <button class="btn btn-primary" style="flex: 1;" onclick="navigate('/orders')">View Orders</button>
            <button class="btn btn-secondary" style="flex: 1;" onclick="navigate('/admin/dashboard')">Admin Portal</button>
          </div>
        </div>
      `;
    }}

    function toggleUserRole() {{
      currentUser.role = currentUser.role === 'ADMIN' ? 'CUSTOMER' : 'ADMIN';
      if (currentUser.role === 'ADMIN') {{
        currentUser.name = 'Administrator';
        currentUser.email = 'admin@shopsphere.io';
      }} else {{
        currentUser.name = 'Capstone Engineer';
        currentUser.email = 'customer@example.com';
      }}
      localStorage.setItem('shopsphere_user', JSON.stringify(currentUser));
      updateHeaderUser();
      showToast('Switched session to ' + currentUser.role + ' (' + currentUser.name + ')');
      renderRoute(getRoute());
    }}

    // Admin Dashboard
    async function renderAdminDashboard(container) {{
      if (currentUser.role !== 'ADMIN') {{
        container.innerHTML = `
          <div class="card" style="text-align: center; padding: 4rem; max-width: 500px; margin: 3rem auto;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">🔒</div>
            <h2 style="font-size: 1.35rem; font-weight: 700; margin-bottom: 0.5rem;">Administrator Access Restricted</h2>
            <p style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 1.5rem;">You are currently logged in as CUSTOMER. Switch to an authorized Administrator account to access store governance.</p>
            <button class="btn btn-primary" onclick="toggleUserRole()">Sign In as Administrator</button>
          </div>
        `;
        return;
      }}

      let stats = {{ total_revenue: 0, total_orders: 0, total_products: 0, low_stock_count: 0, recent_orders: [] }};
      try {{
        const res = await fetch('/api/ecommerce/admin/stats');
        if (res.ok) stats = await res.json();
      }} catch (e) {{}}

      container.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
          <div>
            <h1 style="font-size: 1.85rem; font-weight: 800; margin-bottom: 0.35rem;">Admin Dashboard</h1>
            <p style="color: var(--text-muted); font-size: 0.9rem;">Store overview, inventory alerts, and real-time sales telemetry</p>
          </div>
          <div style="display: flex; gap: 0.75rem;">
            <button class="btn btn-secondary" onclick="navigate('/admin/products')">Product Management</button>
            <button class="btn btn-primary" onclick="navigate('/admin/orders')">Order Management</button>
          </div>
        </div>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1.5rem; margin-bottom: 2rem;">
          <div class="card">
            <span style="font-size: 0.8rem; font-weight: 600; text-transform: uppercase; color: var(--text-muted);">Total Revenue</span>
            <div style="font-size: 2rem; font-weight: 800; color: #60a5fa; margin-top: 0.5rem;">$${{stats.total_revenue.toFixed(2)}}</div>
            <span style="font-size: 0.75rem; color: #34d399;">+18.4% from last month</span>
          </div>
          <div class="card">
            <span style="font-size: 0.8rem; font-weight: 600; text-transform: uppercase; color: var(--text-muted);">Total Orders</span>
            <div style="font-size: 2rem; font-weight: 800; color: #f8fafc; margin-top: 0.5rem;">${{stats.total_orders}}</div>
            <span style="font-size: 0.75rem; color: var(--text-muted);">Processed test transactions</span>
          </div>
          <div class="card">
            <span style="font-size: 0.8rem; font-weight: 600; text-transform: uppercase; color: var(--text-muted);">Active Products</span>
            <div style="font-size: 2rem; font-weight: 800; color: #34d399; margin-top: 0.5rem;">${{stats.total_products}}</div>
            <span style="font-size: 0.75rem; color: var(--text-muted);">Live in catalogue</span>
          </div>
          <div class="card">
            <span style="font-size: 0.8rem; font-weight: 600; text-transform: uppercase; color: var(--text-muted);">Low Stock Alerts</span>
            <div style="font-size: 2rem; font-weight: 800; color: #fbbf24; margin-top: 0.5rem;">${{stats.low_stock_count}}</div>
            <span style="font-size: 0.75rem; color: #fbbf24;">Items under 10 units</span>
          </div>
        </div>

        <div class="card">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.25rem;">
            <h3 style="font-size: 1.15rem; font-weight: 700;">Recent Store Orders</h3>
            <button class="btn btn-secondary btn-sm" onclick="navigate('/admin/orders')">View All Orders →</button>
          </div>
          <div style="overflow-x: auto;">
            <table style="width: 100%; border-collapse: collapse; font-size: 0.88rem; text-align: left;">
              <thead>
                <tr style="border-bottom: 1px solid var(--border); color: var(--text-muted);">
                  <th style="padding: 0.75rem;">Order Number</th>
                  <th style="padding: 0.75rem;">Customer</th>
                  <th style="padding: 0.75rem;">Total</th>
                  <th style="padding: 0.75rem;">Status</th>
                  <th style="padding: 0.75rem;">Action</th>
                </tr>
              </thead>
              <tbody>
                ${{stats.recent_orders.map(o => `
                  <tr style="border-bottom: 1px solid var(--border);">
                    <td style="padding: 0.75rem; font-weight: 700;">${{o.order_number}}</td>
                    <td style="padding: 0.75rem;">${{o.customer_name}}</td>
                    <td style="padding: 0.75rem; font-weight: 700; color: #60a5fa;">$${{o.total.toFixed(2)}}</td>
                    <td style="padding: 0.75rem;">
                      <span class="badge ${{o.status === 'DELIVERED' ? 'badge-success' : o.status === 'SHIPPED' ? 'badge-info' : o.status === 'PROCESSING' ? 'badge-warning' : 'badge-danger'}}">
                        ${{o.status}}
                      </span>
                    </td>
                    <td style="padding: 0.75rem;">
                      <button class="btn btn-secondary btn-sm" onclick="navigate('/orders/${{o.id}}')">Details</button>
                    </td>
                  </tr>
                `).join('')}}
              </tbody>
            </table>
          </div>
        </div>
      `;
    }}

    // Admin Products View
    async function renderAdminProducts(container) {{
      if (currentUser.role !== 'ADMIN') return renderAdminDashboard(container);

      let products = [];
      try {{
        const res = await fetch('/api/ecommerce/products');
        products = await res.json();
      }} catch (e) {{}}

      container.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
          <div>
            <div style="margin-bottom: 0.5rem;">
              <span style="color: var(--text-muted); font-size: 0.85rem; cursor: pointer;" onclick="navigate('/admin/dashboard')">← Back to Dashboard</span>
            </div>
            <h1 style="font-size: 1.85rem; font-weight: 800;">Product Management</h1>
          </div>
          <button class="btn btn-primary" onclick="openAddProductModal()">+ Add New Product</button>
        </div>

        <div class="card" style="padding: 1.5rem; overflow-x: auto;">
          <table style="width: 100%; border-collapse: collapse; font-size: 0.88rem; text-align: left;">
            <thead>
              <tr style="border-bottom: 1px solid var(--border); color: var(--text-muted);">
                <th style="padding: 0.75rem;">ID</th>
                <th style="padding: 0.75rem;">Item</th>
                <th style="padding: 0.75rem;">Category</th>
                <th style="padding: 0.75rem;">Price</th>
                <th style="padding: 0.75rem;">Stock</th>
                <th style="padding: 0.75rem; text-align: right;">Actions</th>
              </tr>
            </thead>
            <tbody>
              ${{products.map(p => `
                <tr style="border-bottom: 1px solid var(--border);">
                  <td style="padding: 0.75rem; font-mono; color: var(--text-muted);">#${{p.id}}</td>
                  <td style="padding: 0.75rem; font-weight: 600;">
                    <span style="margin-right: 0.5rem;">${{p.icon}}</span>${{p.name}}
                  </td>
                  <td style="padding: 0.75rem;"><span class="badge badge-info">${{p.category}}</span></td>
                  <td style="padding: 0.75rem; font-weight: 700; color: #60a5fa;">$${{p.price.toFixed(2)}}</td>
                  <td style="padding: 0.75rem;">
                    <span class="badge ${{p.stock > 0 ? (p.stock < 10 ? 'badge-warning' : 'badge-success') : 'badge-danger'}}">
                      ${{p.stock}} units
                    </span>
                  </td>
                  <td style="padding: 0.75rem; text-align: right;">
                    <button class="btn btn-secondary btn-sm" style="margin-right: 0.5rem;" onclick="openEditProductModal(${{p.id}}, '${{p.name.replace(/'/g, "\\'")}}', ${{p.price}}, ${{p.stock}})">
                      Edit
                    </button>
                    <button class="btn btn-danger btn-sm" onclick="deleteProduct(${{p.id}}, '${{p.name.replace(/'/g, "\\'")}}')">
                      Delete
                    </button>
                  </td>
                </tr>
              `).join('')}}
            </tbody>
          </table>
        </div>
      `;
    }}

    function openAddProductModal() {{
      const modal = document.getElementById('global-modal');
      const content = document.getElementById('modal-content');
      content.innerHTML = `
        <h2 style="font-size: 1.35rem; font-weight: 800; margin-bottom: 1.25rem;">Add New Product</h2>
        <form onsubmit="submitNewProduct(event)" style="display: flex; flex-direction: column; gap: 1rem;">
          <div>
            <label style="display: block; font-size: 0.8rem; font-weight: 600; margin-bottom: 0.35rem;">Product Name *</label>
            <input type="text" id="np-name" required class="input-field" placeholder="e.g. Ergonomic Standing Desk" />
          </div>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
            <div>
              <label style="display: block; font-size: 0.8rem; font-weight: 600; margin-bottom: 0.35rem;">Category *</label>
              <select id="np-cat" class="input-field">
                <option value="Hardware">Hardware</option>
                <option value="Software">Software</option>
                <option value="Accessories">Accessories</option>
                <option value="Audio">Audio</option>
              </select>
            </div>
            <div>
              <label style="display: block; font-size: 0.8rem; font-weight: 600; margin-bottom: 0.35rem;">Icon Emoji</label>
              <input type="text" id="np-icon" value="📦" class="input-field" />
            </div>
          </div>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
            <div>
              <label style="display: block; font-size: 0.8rem; font-weight: 600; margin-bottom: 0.35rem;">Price ($) *</label>
              <input type="number" step="0.01" id="np-price" required value="199.00" class="input-field" />
            </div>
            <div>
              <label style="display: block; font-size: 0.8rem; font-weight: 600; margin-bottom: 0.35rem;">Stock Units *</label>
              <input type="number" id="np-stock" required value="20" class="input-field" />
            </div>
          </div>
          <div>
            <label style="display: block; font-size: 0.8rem; font-weight: 600; margin-bottom: 0.35rem;">Description</label>
            <textarea id="np-desc" class="input-field" rows="3" placeholder="Product details..."></textarea>
          </div>
          <div style="display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 1rem;">
            <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
            <button type="submit" class="btn btn-primary">Create Product</button>
          </div>
        </form>
      `;
      modal.style.display = 'flex';
    }}

    async function submitNewProduct(e) {{
      e.preventDefault();
      const name = document.getElementById('np-name').value.trim();
      const category = document.getElementById('np-cat').value;
      const icon = document.getElementById('np-icon').value || '📦';
      const price = parseFloat(document.getElementById('np-price').value);
      const stock = parseInt(document.getElementById('np-stock').value);
      const description = document.getElementById('np-desc').value.trim();

      try {{
        const res = await fetch('/api/ecommerce/products', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ name, category, icon, price, stock, description }})
        }});
        if (res.ok) {{
          showToast('Created new product "' + name + '"!');
          closeModal();
          renderAdminProducts(document.getElementById('app-view'));
        }}
      }} catch (e) {{
        alert('Failed to create product');
      }}
    }}

    function openEditProductModal(id, name, price, stock) {{
      const modal = document.getElementById('global-modal');
      const content = document.getElementById('modal-content');
      content.innerHTML = `
        <h2 style="font-size: 1.35rem; font-weight: 800; margin-bottom: 1.25rem;">Edit Product #${{id}}</h2>
        <form onsubmit="submitEditProduct(event, ${{id}})" style="display: flex; flex-direction: column; gap: 1rem;">
          <div>
            <label style="display: block; font-size: 0.8rem; font-weight: 600; margin-bottom: 0.35rem;">Product Name</label>
            <input type="text" id="ep-name" value="${{name}}" required class="input-field" />
          </div>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
            <div>
              <label style="display: block; font-size: 0.8rem; font-weight: 600; margin-bottom: 0.35rem;">Price ($)</label>
              <input type="number" step="0.01" id="ep-price" value="${{price}}" required class="input-field" />
            </div>
            <div>
              <label style="display: block; font-size: 0.8rem; font-weight: 600; margin-bottom: 0.35rem;">Stock Units</label>
              <input type="number" id="ep-stock" value="${{stock}}" required class="input-field" />
            </div>
          </div>
          <div style="display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 1rem;">
            <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
            <button type="submit" class="btn btn-primary">Save Changes</button>
          </div>
        </form>
      `;
      modal.style.display = 'flex';
    }}

    async function submitEditProduct(e, id) {{
      e.preventDefault();
      const name = document.getElementById('ep-name').value.trim();
      const price = parseFloat(document.getElementById('ep-price').value);
      const stock = parseInt(document.getElementById('ep-stock').value);

      try {{
        const res = await fetch('/api/ecommerce/products/' + id, {{
          method: 'PUT',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ name, price, stock }})
        }});
        if (res.ok) {{
          showToast('Updated product details successfully!');
          closeModal();
          renderAdminProducts(document.getElementById('app-view'));
        }}
      }} catch (e) {{
        alert('Failed to update product');
      }}
    }}

    async function deleteProduct(id, name) {{
      if (!confirm('Are you sure you want to delete product "' + name + '"?')) return;
      try {{
        const res = await fetch('/api/ecommerce/products/' + id, {{ method: 'DELETE' }});
        if (res.ok) {{
          showToast('Product deleted');
          renderAdminProducts(document.getElementById('app-view'));
        }}
      }} catch (e) {{
        alert('Failed to delete product');
      }}
    }}

    function closeModal() {{
      document.getElementById('global-modal').style.display = 'none';
    }}

    // Admin Orders View
    async function renderAdminOrders(container) {{
      if (currentUser.role !== 'ADMIN') return renderAdminDashboard(container);

      let orders = [];
      try {{
        const res = await fetch('/api/ecommerce/orders');
        orders = await res.json();
      }} catch (e) {{}}

      container.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
          <div>
            <div style="margin-bottom: 0.5rem;">
              <span style="color: var(--text-muted); font-size: 0.85rem; cursor: pointer;" onclick="navigate('/admin/dashboard')">← Back to Dashboard</span>
            </div>
            <h1 style="font-size: 1.85rem; font-weight: 800;">Order Management</h1>
          </div>
        </div>

        <div class="card" style="padding: 1.5rem; overflow-x: auto;">
          <table style="width: 100%; border-collapse: collapse; font-size: 0.88rem; text-align: left;">
            <thead>
              <tr style="border-bottom: 1px solid var(--border); color: var(--text-muted);">
                <th style="padding: 0.75rem;">Order Number</th>
                <th style="padding: 0.75rem;">Customer</th>
                <th style="padding: 0.75rem;">Items</th>
                <th style="padding: 0.75rem;">Total</th>
                <th style="padding: 0.75rem;">Status</th>
                <th style="padding: 0.75rem; text-align: right;">Action</th>
              </tr>
            </thead>
            <tbody>
              ${{orders.map(o => `
                <tr style="border-bottom: 1px solid var(--border);">
                  <td style="padding: 0.75rem; font-weight: 700;">${{o.order_number}}</td>
                  <td style="padding: 0.75rem;">${{o.customer_name}} (${{o.email}})</td>
                  <td style="padding: 0.75rem;">${{o.items.length}} item${{o.items.length > 1 ? 's' : ''}}</td>
                  <td style="padding: 0.75rem; font-weight: 700; color: #60a5fa;">$${{o.total.toFixed(2)}}</td>
                  <td style="padding: 0.75rem;">
                    <select class="input-field" style="padding: 0.3rem 0.6rem; font-size: 0.8rem; width: 140px;" onchange="updateOrderStatus(${{o.id}}, this.value)">
                      <option value="PENDING" ${{o.status === 'PENDING' ? 'selected' : ''}}>PENDING</option>
                      <option value="PROCESSING" ${{o.status === 'PROCESSING' ? 'selected' : ''}}>PROCESSING</option>
                      <option value="SHIPPED" ${{o.status === 'SHIPPED' ? 'selected' : ''}}>SHIPPED</option>
                      <option value="DELIVERED" ${{o.status === 'DELIVERED' ? 'selected' : ''}}>DELIVERED</option>
                      <option value="CANCELLED" ${{o.status === 'CANCELLED' ? 'selected' : ''}}>CANCELLED</option>
                    </select>
                  </td>
                  <td style="padding: 0.75rem; text-align: right;">
                    <button class="btn btn-secondary btn-sm" onclick="navigate('/orders/${{o.id}}')">Details</button>
                  </td>
                </tr>
              `).join('')}}
            </tbody>
          </table>
        </div>
      `;
    }}

    async function updateOrderStatus(orderId, newStatus) {{
      try {{
        const res = await fetch('/api/ecommerce/orders/' + orderId + '/status', {{
          method: 'PUT',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ status: newStatus }})
        }});
        if (res.ok) {{
          showToast('Updated order status to ' + newStatus);
        }}
      }} catch (e) {{
        alert('Failed to update status');
      }}
    }}

    // Not Found View
    function renderNotFound(container) {{
      container.innerHTML = `
        <div class="card" style="text-align: center; padding: 4rem; max-width: 500px; margin: 3rem auto;">
          <div style="font-size: 3.5rem; margin-bottom: 1rem;">🔍</div>
          <h2 style="font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;">404 — Page Not Found</h2>
          <p style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 1.5rem;">The requested URL could not be found on this store.</p>
          <button class="btn btn-primary" onclick="navigate('/')">Return to Homepage</button>
        </div>
      `;
    }}

    // Initial load
    renderRoute(getRoute());
  </script>
</body>
</html>'''


# Test and verify Executive Analytics Dashboard HTML generator

def get_analytics_dashboard_html(title: str = "Executive Analytics Dashboard", desc: str = "", project_id: str = None) -> str:
    # Safe title and desc
    clean_title = title or "Executive Analytics Dashboard"
    clean_desc = desc or "Executive analytics dashboard with revenue charts, user retention metrics, conversion funnel, and team performance KPIs"
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{clean_title} - Executive Analytics Portal</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #0a0d14;
      --surface: #111726;
      --surface-card: rgba(17, 24, 39, 0.75);
      --surface-hover: #1e293b;
      --border: rgba(255, 255, 255, 0.08);
      --border-accent: rgba(99, 102, 241, 0.3);
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --accent-primary: #6366f1;
      --accent-violet: #8b5cf6;
      --accent-cyan: #06b6d4;
      --success: #10b981;
      --success-bg: rgba(16, 185, 129, 0.15);
      --warning: #f59e0b;
      --warning-bg: rgba(245, 158, 11, 0.15);
      --danger: #ef4444;
      --danger-bg: rgba(239, 68, 68, 0.15);
      --font-sans: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;
      --font-mono: 'JetBrains Mono', monospace;
    }}

    body.light-theme {{
      --bg: #f8fafc;
      --surface: #ffffff;
      --surface-card: #ffffff;
      --surface-hover: #f1f5f9;
      --border: #e2e8f0;
      --border-accent: rgba(99, 102, 241, 0.4);
      --text: #0f172a;
      --text-muted: #64748b;
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: var(--font-sans);
      background-color: var(--bg);
      color: var(--text);
      min-height: 100vh;
      padding: 1.5rem;
      transition: background 0.2s ease, color 0.2s ease;
      line-height: 1.5;
    }}

    .container {{
      max-width: 1380px;
      margin: 0 auto;
      display: flex;
      flex-direction: column;
      gap: 1.75rem;
    }}

    /* Top Navigation Header */
    .header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 1rem;
      padding-bottom: 1.25rem;
      border-bottom: 1px solid var(--border);
    }}

    .header-left {{
      display: flex;
      align-items: center;
      gap: 1rem;
    }}

    .app-icon {{
      width: 44px;
      height: 44px;
      border-radius: 12px;
      background: linear-gradient(135deg, #6366f1, #8b5cf6);
      display: flex;
      align-items: center;
      justify-content: center;
      color: #fff;
      font-weight: 800;
      font-size: 1.2rem;
      box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35);
    }}

    .app-title-group h1 {{
      font-size: 1.45rem;
      font-weight: 700;
      letter-spacing: -0.02em;
      display: flex;
      align-items: center;
      gap: 0.6rem;
    }}

    .live-badge {{
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      font-size: 0.7rem;
      font-weight: 700;
      color: var(--success);
      background: var(--success-bg);
      border: 1px solid rgba(16, 185, 129, 0.3);
      padding: 0.2rem 0.55rem;
      border-radius: 9999px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}

    .live-dot {{
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: var(--success);
      box-shadow: 0 0 8px var(--success);
      animation: pulse-dot 2s infinite;
    }}

    @keyframes pulse-dot {{
      0% {{ transform: scale(0.95); opacity: 0.8; }}
      50% {{ transform: scale(1.2); opacity: 1; }}
      100% {{ transform: scale(0.95); opacity: 0.8; }}
    }}

    .app-subtitle {{
      font-size: 0.85rem;
      color: var(--text-muted);
      margin-top: 0.15rem;
    }}

    .header-actions {{
      display: flex;
      align-items: center;
      gap: 0.75rem;
      flex-wrap: wrap;
    }}

    /* Time range filter buttons */
    .filter-group {{
      display: inline-flex;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 3px;
      gap: 2px;
    }}

    .filter-btn {{
      background: transparent;
      border: none;
      color: var(--text-muted);
      padding: 0.35rem 0.7rem;
      font-size: 0.78rem;
      font-weight: 600;
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.15s ease;
    }}

    .filter-btn:hover {{
      color: var(--text);
    }}

    .filter-btn.active {{
      background: var(--accent-primary);
      color: #ffffff;
      box-shadow: 0 2px 6px rgba(99, 102, 241, 0.35);
    }}

    .btn {{
      display: inline-flex;
      align-items: center;
      gap: 0.45rem;
      padding: 0.45rem 0.85rem;
      font-size: 0.82rem;
      font-weight: 600;
      border-radius: 8px;
      cursor: pointer;
      border: 1px solid var(--border);
      background: var(--surface);
      color: var(--text);
      transition: all 0.15s ease;
      text-decoration: none;
    }}

    .btn:hover {{
      background: var(--surface-hover);
      border-color: rgba(255, 255, 255, 0.2);
    }}

    .btn-primary {{
      background: linear-gradient(135deg, var(--accent-primary), var(--accent-violet));
      color: #ffffff;
      border: 1px solid rgba(255, 255, 255, 0.15);
      box-shadow: 0 2px 10px rgba(99, 102, 241, 0.3);
    }}

    .btn-primary:hover {{
      box-shadow: 0 4px 14px rgba(99, 102, 241, 0.45);
      transform: translateY(-1px);
    }}

    /* KPI Summary Cards Grid */
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 1.25rem;
    }}

    .kpi-card {{
      background: var(--surface-card);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 1.35rem;
      backdrop-filter: blur(12px);
      transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
      position: relative;
      overflow: hidden;
    }}

    .kpi-card:hover {{
      transform: translateY(-2px);
      border-color: var(--border-accent);
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
    }}

    .kpi-card::before {{
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 3px;
      background: linear-gradient(90deg, var(--accent-primary), var(--accent-cyan));
      opacity: 0.7;
    }}

    .kpi-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 0.75rem;
    }}

    .kpi-label {{
      font-size: 0.82rem;
      font-weight: 600;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}

    .kpi-trend {{
      display: inline-flex;
      align-items: center;
      gap: 0.25rem;
      font-size: 0.75rem;
      font-weight: 700;
      padding: 0.15rem 0.45rem;
      border-radius: 6px;
    }}

    .trend-up {{
      color: var(--success);
      background: var(--success-bg);
      border: 1px solid rgba(16, 185, 129, 0.3);
    }}

    .trend-down {{
      color: var(--danger);
      background: var(--danger-bg);
      border: 1px solid rgba(239, 68, 68, 0.3);
    }}

    .kpi-value {{
      font-size: 2.1rem;
      font-weight: 800;
      letter-spacing: -0.03em;
      color: var(--text);
      font-family: var(--font-sans);
    }}

    .kpi-subtext {{
      font-size: 0.75rem;
      color: var(--text-muted);
      margin-top: 0.45rem;
    }}

    /* Charts Section */
    .charts-grid {{
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: 1.25rem;
    }}

    .chart-card {{
      background: var(--surface-card);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 1.35rem;
      backdrop-filter: blur(12px);
      display: flex;
      flex-direction: column;
    }}

    .chart-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1.25rem;
    }}

    .chart-title {{
      font-size: 1.05rem;
      font-weight: 700;
      letter-spacing: -0.01em;
    }}

    .chart-subtitle {{
      font-size: 0.78rem;
      color: var(--text-muted);
      margin-top: 0.1rem;
    }}

    /* SVG Chart */
    .svg-chart-container {{
      width: 100%;
      height: 240px;
      position: relative;
    }}

    svg.trend-chart {{
      width: 100%;
      height: 100%;
      overflow: visible;
    }}

    .chart-point {{
      cursor: pointer;
      transition: r 0.15s ease, fill 0.15s ease;
    }}

    .chart-point:hover {{
      r: 6;
      fill: #ffffff;
      stroke: var(--accent-primary);
      stroke-width: 3;
    }}

    /* Funnel Bars */
    .funnel-list {{
      display: flex;
      flex-direction: column;
      gap: 1rem;
      margin-top: 0.5rem;
    }}

    .funnel-item {{
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
    }}

    .funnel-info {{
      display: flex;
      justify-content: space-between;
      font-size: 0.82rem;
    }}

    .funnel-label {{
      font-weight: 600;
      color: var(--text);
    }}

    .funnel-stats {{
      color: var(--text-muted);
      font-family: var(--font-mono);
      font-size: 0.78rem;
    }}

    .funnel-bar-track {{
      height: 10px;
      background: rgba(255, 255, 255, 0.06);
      border-radius: 9999px;
      overflow: hidden;
      position: relative;
    }}

    .funnel-bar-fill {{
      height: 100%;
      border-radius: 9999px;
      background: linear-gradient(90deg, var(--accent-primary), var(--accent-cyan));
      transition: width 0.6s cubic-bezier(0.16, 1, 0.3, 1);
    }}

    /* Table Section */
    .table-card {{
      background: var(--surface-card);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 1.35rem;
      backdrop-filter: blur(12px);
    }}

    .table-toolbar {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1.25rem;
      flex-wrap: wrap;
      gap: 1rem;
    }}

    .search-box {{
      position: relative;
      min-width: 280px;
    }}

    .search-input {{
      width: 100%;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 0.5rem 0.85rem 0.5rem 2.2rem;
      font-size: 0.82rem;
      color: var(--text);
      outline: none;
      transition: border-color 0.15s ease;
    }}

    .search-input:focus {{
      border-color: var(--accent-primary);
    }}

    .search-icon {{
      position: absolute;
      left: 0.75rem;
      top: 50%;
      transform: translateY(-50%);
      color: var(--text-muted);
      pointer-events: none;
    }}

    .category-tabs {{
      display: flex;
      gap: 0.5rem;
    }}

    .tab-btn {{
      background: transparent;
      border: 1px solid transparent;
      color: var(--text-muted);
      padding: 0.35rem 0.75rem;
      font-size: 0.78rem;
      font-weight: 600;
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.15s ease;
    }}

    .tab-btn.active {{
      background: rgba(99, 102, 241, 0.15);
      color: #818cf8;
      border-color: rgba(99, 102, 241, 0.3);
    }}

    .data-table {{
      width: 100%;
      border-collapse: collapse;
      text-align: left;
      font-size: 0.82rem;
    }}

    .data-table th {{
      background: rgba(255, 255, 255, 0.02);
      color: var(--text-muted);
      padding: 0.75rem 1rem;
      font-weight: 600;
      border-bottom: 1px solid var(--border);
      cursor: pointer;
      user-select: none;
    }}

    .data-table th:hover {{
      color: var(--text);
    }}

    .data-table td {{
      padding: 0.85rem 1rem;
      border-bottom: 1px solid var(--border);
      color: var(--text);
    }}

    .data-table tr:hover td {{
      background: rgba(255, 255, 255, 0.02);
    }}

    .status-pill {{
      display: inline-block;
      padding: 0.2rem 0.5rem;
      border-radius: 9999px;
      font-size: 0.72rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }}

    .status-exceeded {{
      background: var(--success-bg);
      color: var(--success);
      border: 1px solid rgba(16, 185, 129, 0.3);
    }}

    .status-ontrack {{
      background: rgba(6, 182, 212, 0.15);
      color: #22d3ee;
      border: 1px solid rgba(6, 182, 212, 0.3);
    }}

    .status-atrisk {{
      background: var(--warning-bg);
      color: var(--warning);
      border: 1px solid rgba(245, 158, 11, 0.3);
    }}

    /* Modal */
    .modal-backdrop {{
      display: none;
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.75);
      backdrop-filter: blur(6px);
      z-index: 1000;
      align-items: center;
      justify-content: center;
    }}

    .modal-backdrop.open {{
      display: flex;
    }}

    .modal-content {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 16px;
      width: 100%;
      max-width: 480px;
      padding: 1.75rem;
      box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6);
      display: flex;
      flex-direction: column;
      gap: 1.25rem;
    }}

    .modal-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}

    .modal-title {{
      font-size: 1.15rem;
      font-weight: 700;
    }}

    .form-group {{
      display: flex;
      flex-direction: column;
      gap: 0.4rem;
    }}

    .form-label {{
      font-size: 0.78rem;
      font-weight: 600;
      color: var(--text-muted);
    }}

    .form-input {{
      background: rgba(0, 0, 0, 0.2);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 0.55rem 0.85rem;
      font-size: 0.85rem;
      color: var(--text);
      outline: none;
    }}

    .form-input:focus {{
      border-color: var(--accent-primary);
    }}

    .modal-actions {{
      display: flex;
      justify-content: flex-end;
      gap: 0.75rem;
      margin-top: 0.5rem;
    }}

    /* Responsive Queries */
    @media (max-width: 1024px) {{
      .kpi-grid {{
        grid-template-columns: repeat(2, 1fr);
      }}
      .charts-grid {{
        grid-template-columns: 1fr;
      }}
    }}

    @media (max-width: 640px) {{
      body {{
        padding: 1rem;
      }}
      .kpi-grid {{
        grid-template-columns: 1fr;
      }}
      .header {{
        flex-direction: column;
        align-items: flex-start;
      }}
      .table-toolbar {{
        flex-direction: column;
        align-items: stretch;
      }}
      .search-box {{
        min-width: 100%;
      }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <!-- Top Header -->
    <header class="header">
      <div class="header-left">
        <div class="app-icon">EA</div>
        <div class="app-title-group">
          <h1>
            <span>{clean_title}</span>
            <span class="live-badge"><span class="live-dot"></span> LIVE STREAM</span>
          </h1>
          <p class="app-subtitle">{clean_desc}</p>
        </div>
      </div>

      <div class="header-actions">
        <!-- Time Range Selector -->
        <div class="filter-group" role="group" aria-label="Time range filters">
          <button type="button" class="filter-btn" onclick="setTimeRange('7D')">7D</button>
          <button type="button" class="filter-btn active" onclick="setTimeRange('30D')">30D</button>
          <button type="button" class="filter-btn" onclick="setTimeRange('90D')">90D</button>
          <button type="button" class="filter-btn" onclick="setTimeRange('1Y')">1Y</button>
        </div>

        <button type="button" class="btn" onclick="toggleTheme()" title="Toggle Dark/Light Mode">
          <span id="themeIcon">☀️</span>
        </button>

        <button type="button" class="btn btn-primary" onclick="openAddMetricModal()">
          <span>+ Add Metric</span>
        </button>

        <button type="button" class="btn" onclick="exportCSV()">
          <span>Export CSV</span>
        </button>
      </div>
    </header>

    <!-- 4 KPI Cards Grid -->
    <section class="kpi-grid" aria-label="Key Performance Indicators">
      <div class="kpi-card">
        <div class="kpi-header">
          <span class="kpi-label">Total ARR / Revenue</span>
          <span class="kpi-trend trend-up">+14.8%</span>
        </div>
        <div class="kpi-value" id="kpiRevenue">$1,428,500</div>
        <div class="kpi-subtext">+12.4% vs previous 30-day cohort</div>
      </div>

      <div class="kpi-card">
        <div class="kpi-header">
          <span class="kpi-label">Active Workspaces</span>
          <span class="kpi-trend trend-up">+21.4%</span>
        </div>
        <div class="kpi-value" id="kpiWorkspaces">3,842</div>
        <div class="kpi-subtext">98.2% customer retention index</div>
      </div>

      <div class="kpi-card">
        <div class="kpi-header">
          <span class="kpi-label">Conversion Rate</span>
          <span class="kpi-trend trend-up">+3.2%</span>
        </div>
        <div class="kpi-value" id="kpiConversion">24.6%</div>
        <div class="kpi-subtext">Trial-to-paid funnel completion</div>
      </div>

      <div class="kpi-card">
        <div class="kpi-header">
          <span class="kpi-label">Customer Churn</span>
          <span class="kpi-trend trend-up">-0.4%</span>
        </div>
        <div class="kpi-value" id="kpiChurn">1.8%</div>
        <div class="kpi-subtext">Benchmark avg: 3.5% annually</div>
      </div>
    </section>

    <!-- Charts Grid -->
    <section class="charts-grid">
      <!-- Revenue Trajectory Chart -->
      <div class="chart-card">
        <div class="chart-header">
          <div>
            <h2 class="chart-title">Revenue & Growth Trajectory</h2>
            <p class="chart-subtitle">Monthly recurring revenue with continuous ARR forecast</p>
          </div>
          <span style="font-size: 0.75rem; color: #818cf8; font-weight: 700;">+28.5% YoY</span>
        </div>

        <div class="svg-chart-container">
          <svg class="trend-chart" viewBox="0 0 600 220" preserveAspectRatio="none">
            <defs>
              <linearGradient id="revenueGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#6366f1" stop-opacity="0.45"/>
                <stop offset="100%" stop-color="#6366f1" stop-opacity="0.0"/>
              </linearGradient>
            </defs>
            <!-- Grid Lines -->
            <line x1="40" y1="30" x2="580" y2="30" stroke="rgba(255,255,255,0.06)" stroke-dasharray="4"/>
            <line x1="40" y1="80" x2="580" y2="80" stroke="rgba(255,255,255,0.06)" stroke-dasharray="4"/>
            <line x1="40" y1="130" x2="580" y2="130" stroke="rgba(255,255,255,0.06)" stroke-dasharray="4"/>
            <line x1="40" y1="180" x2="580" y2="180" stroke="rgba(255,255,255,0.08)"/>

            <!-- Area fill -->
            <polygon points="50,180 50,150 110,135 170,142 230,118 290,105 350,92 410,74 470,62 530,42 570,30 570,180" fill="url(#revenueGradient)"/>

            <!-- Trend Line -->
            <polyline points="50,150 110,135 170,142 230,118 290,105 350,92 410,74 470,62 530,42 570,30" fill="none" stroke="#6366f1" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>

            <!-- Hoverable points -->
            <circle class="chart-point" cx="50" cy="150" r="4" fill="#6366f1" data-date="Jan" data-val="$820k"/>
            <circle class="chart-point" cx="110" cy="135" r="4" fill="#6366f1" data-date="Feb" data-val="$890k"/>
            <circle class="chart-point" cx="170" cy="142" r="4" fill="#6366f1" data-date="Mar" data-val="$875k"/>
            <circle class="chart-point" cx="230" cy="118" r="4" fill="#6366f1" data-date="Apr" data-val="$990k"/>
            <circle class="chart-point" cx="290" cy="105" r="4" fill="#6366f1" data-date="May" data-val="$1.08M"/>
            <circle class="chart-point" cx="350" cy="92" r="4" fill="#6366f1" data-date="Jun" data-val="$1.16M"/>
            <circle class="chart-point" cx="410" cy="74" r="4" fill="#6366f1" data-date="Jul" data-val="$1.24M"/>
            <circle class="chart-point" cx="470" cy="62" r="4" fill="#6366f1" data-date="Aug" data-val="$1.31M"/>
            <circle class="chart-point" cx="530" cy="42" r="4" fill="#6366f1" data-date="Sep" data-val="$1.39M"/>
            <circle class="chart-point" cx="570" cy="30" r="4" fill="#6366f1" data-date="Oct" data-val="$1.42M"/>

            <!-- Axis Labels -->
            <text x="50" y="202" fill="var(--text-muted)" font-size="11" text-anchor="middle">Jan</text>
            <text x="170" y="202" fill="var(--text-muted)" font-size="11" text-anchor="middle">Mar</text>
            <text x="290" y="202" fill="var(--text-muted)" font-size="11" text-anchor="middle">May</text>
            <text x="410" y="202" fill="var(--text-muted)" font-size="11" text-anchor="middle">Jul</text>
            <text x="530" y="202" fill="var(--text-muted)" font-size="11" text-anchor="middle">Sep</text>
            <text x="570" y="202" fill="var(--text-muted)" font-size="11" text-anchor="middle">Oct</text>
          </svg>
        </div>
      </div>

      <!-- Conversion Funnel Card -->
      <div class="chart-card">
        <div class="chart-header">
          <div>
            <h2 class="chart-title">Conversion Funnel</h2>
            <p class="chart-subtitle">End-to-end customer onboarding flow</p>
          </div>
          <span style="font-size: 0.75rem; color: #10b981; font-weight: 700;">Healthy</span>
        </div>

        <div class="funnel-list">
          <div class="funnel-item">
            <div class="funnel-info">
              <span class="funnel-label">Total Visitors</span>
              <span class="funnel-stats">145,200 (100%)</span>
            </div>
            <div class="funnel-bar-track">
              <div class="funnel-bar-fill" style="width: 100%;"></div>
            </div>
          </div>

          <div class="funnel-item">
            <div class="funnel-info">
              <span class="funnel-label">Product Signups</span>
              <span class="funnel-stats">48,300 (33.3%)</span>
            </div>
            <div class="funnel-bar-track">
              <div class="funnel-bar-fill" style="width: 33.3%;"></div>
            </div>
          </div>

          <div class="funnel-item">
            <div class="funnel-info">
              <span class="funnel-label">Active Trials</span>
              <span class="funnel-stats">18,450 (12.7%)</span>
            </div>
            <div class="funnel-bar-track">
              <div class="funnel-bar-fill" style="width: 12.7%;"></div>
            </div>
          </div>

          <div class="funnel-item">
            <div class="funnel-info">
              <span class="funnel-label">Enterprise Paid</span>
              <span class="funnel-stats">3,842 (2.6%)</span>
            </div>
            <div class="funnel-bar-track">
              <div class="funnel-bar-fill" style="width: 2.6%; background: #10b981;"></div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Metrics Data Table -->
    <section class="table-card" aria-label="Performance Metrics">
      <div class="table-toolbar">
        <div>
          <h2 class="chart-title">Key Performance Indicators</h2>
          <p class="chart-subtitle">Detailed financial, operational, and retention benchmarks</p>
        </div>

        <div style="display: flex; gap: 0.75rem; flex-wrap: wrap;">
          <div class="search-box">
            <span class="search-icon">🔍</span>
            <input type="text" id="metricSearch" class="search-input" placeholder="Search metrics or dimensions..." onkeyup="filterTable()" />
          </div>

          <div class="category-tabs">
            <button type="button" class="tab-btn active" onclick="setCategoryFilter('all')">All</button>
            <button type="button" class="tab-btn" onclick="setCategoryFilter('Financial')">Financial</button>
            <button type="button" class="tab-btn" onclick="setCategoryFilter('Product')">Product</button>
            <button type="button" class="tab-btn" onclick="setCategoryFilter('Retention')">Retention</button>
          </div>
        </div>
      </div>

      <div style="overflow-x: auto;">
        <table class="data-table" id="metricsTable">
          <thead>
            <tr>
              <th onclick="sortTable(0)">Metric Name ↕</th>
              <th onclick="sortTable(1)">Category ↕</th>
              <th onclick="sortTable(2)">Current Value ↕</th>
              <th onclick="sortTable(3)">Target ↕</th>
              <th onclick="sortTable(4)">Trend ↕</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody id="metricsBody">
            <tr data-category="Financial">
              <td style="font-weight: 600;">Annual Recurring Revenue (ARR)</td>
              <td>Financial</td>
              <td style="font-family: var(--font-mono); font-weight: 700;">$1,428,500</td>
              <td style="color: var(--text-muted);">$1,350,000</td>
              <td style="color: var(--success); font-weight: 700;">+14.8%</td>
              <td><span class="status-pill status-exceeded">Exceeded</span></td>
            </tr>
            <tr data-category="Financial">
              <td style="font-weight: 600;">Average Revenue Per User (ARPU)</td>
              <td>Financial</td>
              <td style="font-family: var(--font-mono); font-weight: 700;">$371.80</td>
              <td style="color: var(--text-muted);">$350.00</td>
              <td style="color: var(--success); font-weight: 700;">+6.2%</td>
              <td><span class="status-pill status-exceeded">Exceeded</span></td>
            </tr>
            <tr data-category="Product">
              <td style="font-weight: 600;">Monthly Active Workspaces</td>
              <td>Product</td>
              <td style="font-family: var(--font-mono); font-weight: 700;">3,842</td>
              <td style="color: var(--text-muted);">3,500</td>
              <td style="color: var(--success); font-weight: 700;">+21.4%</td>
              <td><span class="status-pill status-exceeded">Exceeded</span></td>
            </tr>
            <tr data-category="Product">
              <td style="font-weight: 600;">Trial-to-Paid Conversion</td>
              <td>Product</td>
              <td style="font-family: var(--font-mono); font-weight: 700;">24.6%</td>
              <td style="color: var(--text-muted);">25.0%</td>
              <td style="color: var(--warning); font-weight: 700;">-0.4%</td>
              <td><span class="status-pill status-ontrack">On Track</span></td>
            </tr>
            <tr data-category="Retention">
              <td style="font-weight: 600;">Net Revenue Retention (NRR)</td>
              <td>Retention</td>
              <td style="font-family: var(--font-mono); font-weight: 700;">122.4%</td>
              <td style="color: var(--text-muted);">118.0%</td>
              <td style="color: var(--success); font-weight: 700;">+4.4%</td>
              <td><span class="status-pill status-exceeded">Exceeded</span></td>
            </tr>
            <tr data-category="Retention">
              <td style="font-weight: 600;">Customer Gross Churn Rate</td>
              <td>Retention</td>
              <td style="font-family: var(--font-mono); font-weight: 700;">1.8%</td>
              <td style="color: var(--text-muted);">&lt; 2.5%</td>
              <td style="color: var(--success); font-weight: 700;">-0.4%</td>
              <td><span class="status-pill status-ontrack">On Track</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>

  <!-- Add Metric Modal -->
  <div class="modal-backdrop" id="addMetricModal">
    <div class="modal-content">
      <div class="modal-header">
        <h3 class="modal-title">Add Custom KPI Metric</h3>
        <button type="button" class="btn" style="padding: 0.2rem 0.5rem;" onclick="closeAddMetricModal()">✕</button>
      </div>

      <div class="form-group">
        <label class="form-label" for="metricName">Metric Name</label>
        <input type="text" id="metricName" class="form-input" placeholder="e.g. Daily Active Users" />
      </div>

      <div class="form-group">
        <label class="form-label" for="metricCategory">Category</label>
        <select id="metricCategory" class="form-input">
          <option value="Financial">Financial</option>
          <option value="Product">Product</option>
          <option value="Retention">Retention</option>
        </select>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem;">
        <div class="form-group">
          <label class="form-label" for="metricVal">Current Value</label>
          <input type="text" id="metricVal" class="form-input" placeholder="e.g. 15,200" />
        </div>
        <div class="form-group">
          <label class="form-label" for="metricTarget">Target</label>
          <input type="text" id="metricTarget" class="form-input" placeholder="e.g. 12,000" />
        </div>
      </div>

      <div class="modal-actions">
        <button type="button" class="btn" onclick="closeAddMetricModal()">Cancel</button>
        <button type="button" class="btn btn-primary" onclick="submitNewMetric()">Save Metric</button>
      </div>
    </div>
  </div>

  <!-- Interactive JavaScript logic -->
  <script>
    // Theme toggle
    function toggleTheme() {{
      const isLight = document.body.classList.toggle('light-theme');
      document.getElementById('themeIcon').textContent = isLight ? '🌙' : '☀️';
    }}

    // Time range filter switching
    function setTimeRange(range) {{
      document.querySelectorAll('.filter-btn').forEach(btn => {{
        btn.classList.toggle('active', btn.textContent.trim() === range);
      }});

      const revElem = document.getElementById('kpiRevenue');
      const wsElem = document.getElementById('kpiWorkspaces');
      if (range === '7D') {{
        revElem.textContent = '$348,200';
        wsElem.textContent = '1,120';
      }} else if (range === '30D') {{
        revElem.textContent = '$1,428,500';
        wsElem.textContent = '3,842';
      }} else if (range === '90D') {{
        revElem.textContent = '$4,190,000';
        wsElem.textContent = '6,450';
      }} else if (range === '1Y') {{
        revElem.textContent = '$14,800,000';
        wsElem.textContent = '12,900';
      }}
    }}

    // Filter table by search query
    function filterTable() {{
      const query = (document.getElementById('metricSearch').value || '').toLowerCase();
      const rows = document.querySelectorAll('#metricsBody tr');
      rows.forEach(r => {{
        const text = r.textContent.toLowerCase();
        r.style.display = text.includes(query) ? '' : 'none';
      }});
    }}

    // Filter table by category tab
    function setCategoryFilter(cat) {{
      document.querySelectorAll('.tab-btn').forEach(b => {{
        b.classList.toggle('active', b.textContent.trim().toLowerCase() === cat.toLowerCase());
      }});

      const rows = document.querySelectorAll('#metricsBody tr');
      rows.forEach(r => {{
        if (cat === 'all' || r.getAttribute('data-category').toLowerCase() === cat.toLowerCase()) {{
          r.style.display = '';
        }} else {{
          r.style.display = 'none';
        }}
      }});
    }}

    // Sort table by column index
    let sortAsc = true;
    function sortTable(colIndex) {{
      const tbody = document.getElementById('metricsBody');
      const rows = Array.from(tbody.querySelectorAll('tr'));
      rows.sort((a, b) => {{
        const textA = a.children[colIndex].textContent.trim();
        const textB = b.children[colIndex].textContent.trim();
        return sortAsc ? textA.localeCompare(textB) : textB.localeCompare(textA);
      }});
      sortAsc = !sortAsc;
      rows.forEach(r => tbody.appendChild(r));
    }}

    // Modal controls
    function openAddMetricModal() {{
      document.getElementById('addMetricModal').classList.add('open');
    }}

    function closeAddMetricModal() {{
      document.getElementById('addMetricModal').classList.remove('open');
    }}

    function submitNewMetric() {{
      const name = document.getElementById('metricName').value.trim();
      const cat = document.getElementById('metricCategory').value;
      const val = document.getElementById('metricVal').value.trim() || '0';
      const target = document.getElementById('metricTarget').value.trim() || '0';

      if (!name) {{
        alert('Please enter a metric name');
        return;
      }}

      const tbody = document.getElementById('metricsBody');
      const tr = document.createElement('tr');
      tr.setAttribute('data-category', cat);
      tr.innerHTML = `
        <td style="font-weight: 600;">${{name}}</td>
        <td>${{cat}}</td>
        <td style="font-family: var(--font-mono); font-weight: 700;">${{val}}</td>
        <td style="color: var(--text-muted);">${{target}}</td>
        <td style="color: var(--success); font-weight: 700;">+5.0%</td>
        <td><span class="status-pill status-ontrack">On Track</span></td>
      `;
      tbody.prepend(tr);
      closeAddMetricModal();
      document.getElementById('metricName').value = '';
    }}

    // Export CSV
    function exportCSV() {{
      const rows = Array.from(document.querySelectorAll('#metricsTable tr'));
      const csv = rows.map(r => {{
        const cells = Array.from(r.querySelectorAll('th, td')).map(c => '"' + c.textContent.trim().replace(/"/g, '""') + '"');
        return cells.join(',');
      }}).join('\\n');

      const blob = new Blob([csv], {{ type: 'text/csv' }});
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'executive-analytics-metrics.csv';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    }}
  </script>
</body>
</html>"""


def get_management_html(title: str = "Enterprise Management System", desc: str = "") -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title} — Live Management Portal</title>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #090d16;
      --card: #111827;
      --border: rgba(255, 255, 255, 0.08);
      --accent: #6366f1;
      --text: #f8fafc;
      --muted: #94a3b8;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Plus Jakarta Sans', sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      padding: 1.5rem 2rem;
    }}
    .header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 2rem;
      border-bottom: 1px solid var(--border);
      padding-bottom: 1.25rem;
    }}
    .stats-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 1.25rem;
      margin-bottom: 2rem;
    }}
    .stat-card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.25rem;
    }}
    .stat-val {{ font-size: 1.8rem; font-weight: 700; color: #818cf8; margin-top: 0.35rem; }}
    .table-card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      overflow: hidden;
    }}
    table {{ width: 100%; border-collapse: collapse; text-align: left; font-size: 0.875rem; }}
    th {{ background: rgba(255, 255, 255, 0.03); color: var(--muted); padding: 0.9rem 1.25rem; font-weight: 600; border-bottom: 1px solid var(--border); }}
    td {{ padding: 0.9rem 1.25rem; border-bottom: 1px solid var(--border); }}
    .badge {{ display: inline-block; padding: 0.25rem 0.6rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; }}
    .badge-active {{ background: rgba(16, 185, 129, 0.15); color: #34d399; }}
    .badge-pending {{ background: rgba(245, 158, 11, 0.15); color: #fbbf24; }}
    .btn {{
      background: var(--accent);
      color: #fff;
      border: none;
      padding: 0.55rem 1.25rem;
      border-radius: 8px;
      font-weight: 600;
      cursor: pointer;
    }}
  </style>
</head>
<body>
  <div class="header">
    <div>
      <h1 style="font-size: 1.5rem; font-weight: 700;">📊 {title}</h1>
      <p style="color: var(--muted); font-size: 0.85rem; margin-top: 0.25rem;">{desc or 'Centralized management dashboard for resources, records, and departmental workflows.'}</p>
    </div>
    <button class="btn" onclick="openAddModal()">+ Add Record</button>
  </div>

  <div class="stats-grid">
    <div class="stat-card">
      <div style="color: var(--muted); font-size: 0.8rem;">TOTAL RECORDS</div>
      <div class="stat-val" id="stat-total">4</div>
    </div>
    <div class="stat-card">
      <div style="color: var(--muted); font-size: 0.8rem;">ACTIVE STATUS</div>
      <div class="stat-val" id="stat-active" style="color: #34d399;">3</div>
    </div>
    <div class="stat-card">
      <div style="color: var(--muted); font-size: 0.8rem;">PENDING REVIEW</div>
      <div class="stat-val" id="stat-pending" style="color: #fbbf24;">1</div>
    </div>
  </div>

  <div class="table-card">
    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>NAME / TITLE</th>
          <th>DEPARTMENT / CATEGORY</th>
          <th>STATUS</th>
          <th>LAST UPDATED</th>
          <th>ACTION</th>
        </tr>
      </thead>
      <tbody id="table-body"></tbody>
    </table>
  </div>

  <script>
    let records = [
      {{ id: 'REC-101', name: 'Software Intelligence Pipeline', dept: 'Engineering', status: 'ACTIVE', updated: '2026-10-24' }},
      {{ id: 'REC-102', name: 'Autonomous Testing Cluster', dept: 'DevOps', status: 'ACTIVE', updated: '2026-10-23' }},
      {{ id: 'REC-103', name: 'Database Model Migration', dept: 'Infrastructure', status: 'PENDING', updated: '2026-10-22' }},
      {{ id: 'REC-104', name: 'Frontend Design Token System', dept: 'Product UI', status: 'ACTIVE', updated: '2026-10-21' }}
    ];

    function renderTable() {{
      const tbody = document.getElementById('table-body');
      tbody.innerHTML = records.map(r => `
        <tr>
          <td style="font-family: monospace; color: #818cf8;">${{r.id}}</td>
          <td style="font-weight: 600;">${{r.name}}</td>
          <td>${{r.dept}}</td>
          <td><span class="badge ${{r.status === 'ACTIVE' ? 'badge-active' : 'badge-pending'}}">${{r.status}}</span></td>
          <td style="color: var(--muted);">${{r.updated}}</td>
          <td><button onclick="deleteRecord('${{r.id}}')" style="background: none; border: none; color: #ef4444; cursor: pointer; font-size: 0.8rem;">Delete</button></td>
        </tr>
      `).join('');

      document.getElementById('stat-total').textContent = records.length;
      document.getElementById('stat-active').textContent = records.filter(r => r.status === 'ACTIVE').length;
      document.getElementById('stat-pending').textContent = records.filter(r => r.status !== 'ACTIVE').length;
    }}

    function deleteRecord(id) {{
      records = records.filter(r => r.id !== id);
      renderTable();
    }}

    function openAddModal() {{
      const name = prompt('Enter record name:');
      if (!name) return;
      const dept = prompt('Enter department or category:') || 'General';
      const newRec = {{
        id: 'REC-' + (100 + records.length + 1),
        name,
        dept,
        status: 'ACTIVE',
        updated: new Date().toISOString().split('T')[0]
      }};
      records.unshift(newRec);
      renderTable();
    }}

    renderTable();
  </script>
</body>
</html>"""


def get_custom_app_html(title: str = "SE IntelliPlatform Application", desc: str = "") -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title} — Live Preview</title>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #090d16;
      --card: #111827;
      --border: rgba(255, 255, 255, 0.08);
      --accent: #3b82f6;
      --text: #f8fafc;
      --muted: #94a3b8;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Plus Jakarta Sans', sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      padding: 2rem;
      display: flex;
      flex-direction: column;
      align-items: center;
    }}
    .card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 2rem;
      max-width: 700px;
      width: 100%;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
    }}
    h1 {{
      font-size: 1.8rem;
      font-weight: 700;
      background: linear-gradient(135deg, #60a5fa, #c084fc);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 0.5rem;
    }}
    p {{ color: var(--muted); line-height: 1.6; font-size: 0.95rem; margin-bottom: 1.5rem; }}
    .action-box {{
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 1.25rem;
      margin-top: 1rem;
    }}
    .btn {{
      background: var(--accent);
      color: #fff;
      border: none;
      padding: 0.6rem 1.25rem;
      border-radius: 8px;
      font-weight: 600;
      cursor: pointer;
    }}
  </style>
</head>
<body>
  <div class="card">
    <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem;">
      <span style="font-size: 2rem;">🚀</span>
      <div>
        <h1>{title}</h1>
        <span style="background: rgba(16, 185, 129, 0.15); color: #34d399; font-size: 0.75rem; font-weight: 600; padding: 0.2rem 0.6rem; border-radius: 9999px;">GENERATED & LIVE</span>
      </div>
    </div>

    <p>{desc or 'This application was synthesized according to the confirmed project specifications on SE IntelliPlatform.'}</p>

    <div class="action-box">
      <h3 style="font-size: 1rem; margin-bottom: 0.5rem;">Interactive Application Playground</h3>
      <p style="margin-bottom: 1rem; font-size: 0.85rem;">Test your application runtime features or use the AI Development Assistant to add custom workflows and database models.</p>
      <button class="btn" onclick="alert('Action triggered on {title}!')">Trigger Primary Action</button>
    </div>
  </div>
</body>
</html>"""


def get_app_html_for_project(project_id: Optional[str] = None, app_type: Optional[str] = None) -> str:
    # 1. If project_id provided without explicit prototype override, check isolated workspace directory first
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
                        return cand.read_text(encoding="utf-8", errors="replace")
                for root, _, files in os.walk(str(ws_dir)):
                    for f in files:
                        if f.endswith(".html"):
                            return Path(root, f).read_text(encoding="utf-8", errors="replace")
        except Exception:
            pass

    mode = app_type
    p_name = ""
    p_desc = ""

    if not mode and project_id:
        if str(project_id) in project_contexts:
            ctx = project_contexts[str(project_id)]
            mode = ctx.get("mode")
            p_name = ctx.get("project_name", "")
            p_desc = ctx.get("project_description", "")
        else:
            # Fallback to local SQLite project lookup
            try:
                import sqlite3
                conn = get_db_conn()
                cur = conn.cursor()
                pid_s = str(project_id)
                pid_h = pid_s.replace("-", "")
                cur.execute("SELECT name, description FROM projects WHERE id = ? OR id = ?", (pid_s, pid_h))
                row = cur.fetchone()
                conn.close()
                if row:
                    p_name, p_desc = row[0] or "", row[1] or ""
                    mode = detect_mode(p_name, p_desc)
                    project_contexts[str(project_id)] = {
                        "project_id": str(project_id),
                        "project_name": p_name,
                        "project_description": p_desc,
                        "mode": mode,
                    }
            except Exception:
                pass

    if not mode:
        mode = active_project_context.get("mode", "taskflow")
        p_name = active_project_context.get("project_name", "")
        p_desc = active_project_context.get("project_description", "")

    if mode == "analytics":
        return get_analytics_dashboard_html(p_name or "Executive Analytics Dashboard", p_desc, project_id)
    elif mode == "eventhub":
        return EVENTHUB_HTML
    elif mode == "taskflow":
        return get_taskflow_html(project_id)
    elif mode == "snake_game":
        return get_snake_game_html(p_name or "Arcade Snake")
    elif mode == "ecommerce":
        return get_ecommerce_html(p_name or "ShopSphere", p_desc)
    elif mode == "management":
        return get_management_html(p_name or "Enterprise Management System", p_desc)
    elif mode == "custom":
        return get_custom_app_html(p_name or "SE IntelliPlatform Application", p_desc)
    return get_taskflow_html(project_id)


@app.get("/", response_class=HTMLResponse)
def index_page(
    app_type: Optional[str] = Query(None, alias="app"),
    project_id: Optional[str] = Query(None),
):
    html = get_app_html_for_project(project_id=project_id, app_type=app_type)
    return HTMLResponse(content=html)


@app.get("/preview/{project_id}", response_class=HTMLResponse)
def preview_project_page(project_id: str):
    html = get_app_html_for_project(project_id=project_id)
    return HTMLResponse(content=html)


@app.get("/analytics", response_class=HTMLResponse)
def analytics_page():
    return HTMLResponse(content=get_analytics_dashboard_html())


@app.get("/eventhub", response_class=HTMLResponse)
def eventhub_page():
    return HTMLResponse(content=EVENTHUB_HTML)


@app.get("/taskflow", response_class=HTMLResponse)
def taskflow_page():
    return HTMLResponse(content=get_taskflow_html())


@app.get("/snake", response_class=HTMLResponse)
def snake_page():
    return HTMLResponse(content=get_snake_game_html())


@app.get("/ecommerce", response_class=HTMLResponse)
def ecommerce_page():
    return HTMLResponse(content=get_ecommerce_html())


@app.get("/management", response_class=HTMLResponse)
def management_page():
    return HTMLResponse(content=get_management_html())


if __name__ == "__main__":
    uvicorn.run("taskflow_app_server:app", host="127.0.0.1", port=8001, log_level="info", reload=False)

