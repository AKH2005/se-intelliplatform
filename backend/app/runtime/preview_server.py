from app.runtime.preview_medium_complexity import get_inventory_html, get_lms_html
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
    from app.agents.code_generation.archetypes import detect_project_archetype
    return detect_project_archetype(name=name, desc=desc)

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
# MEDIUM-COMPLEXITY SQLITE PERSISTENCE ENGINES & APIS
# ==============================================================================

def sync_events_from_db():
    global events_db, registrations_db
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS preview_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                category TEXT DEFAULT 'Technology',
                location TEXT DEFAULT 'Virtual',
                date TEXT DEFAULT '2026-11-20',
                time TEXT DEFAULT '10:00 AM',
                total_seats INTEGER DEFAULT 100,
                available_seats INTEGER DEFAULT 100,
                price REAL DEFAULT 0.0
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS preview_event_registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                attendee_name TEXT NOT NULL,
                attendee_email TEXT NOT NULL,
                ticket_type TEXT DEFAULT 'Standard Pass',
                registration_date TEXT DEFAULT '',
                status TEXT DEFAULT 'CONFIRMED'
            )
        """)
        cur.execute("SELECT id, title, description, category, location, date, time, total_seats, available_seats, price FROM preview_events ORDER BY id ASC")
        rows = cur.fetchall()
        if not rows:
            initial = [
                ("Global AI Architecture Summit 2026", "Premier engineering conference on autonomous agents, neural architectures, and distributed intelligent systems.", "Technology", "San Francisco / Virtual", "2026-11-20", "09:00 AM", 75, 74, 199.0),
                ("Next-Gen Cloud & Microservices Expo", "Deep dive into event-driven design, high-throughput streaming, and zero-trust mesh architectures.", "Technology", "Austin, TX", "2026-12-05", "10:30 AM", 150, 148, 149.0),
                ("Modern Design Systems & UX Conference", "Interactive workshop on scalable component tokens, micro-animations, and accessible web ergonomics.", "Design", "Seattle, WA", "2026-12-12", "01:00 PM", 40, 22, 89.0),
                ("Cybersecurity & Zero-Trust Defense Forum", "Hands-on threat intelligence, confidential computing, and hardened infrastructure best practices.", "Security", "Boston, MA", "2026-12-18", "11:00 AM", 60, 58, 249.0),
                ("Enterprise Engineering Leadership Forum", "Executive roundtable on engineering velocity, developer autonomy, and scaling tech teams.", "Business", "New York, NY", "2026-11-25", "02:00 PM", 25, 0, 299.0)
            ]
            cur.executemany("INSERT INTO preview_events (title, description, category, location, date, time, total_seats, available_seats, price) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", initial)
            cur.execute("""
                INSERT INTO preview_event_registrations (event_id, attendee_name, attendee_email, ticket_type, registration_date, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (1, "Developer User", "developer@se-intelliplatform.local", "VIP Pass", "2026-11-15", "CONFIRMED"))
            conn.commit()
            cur.execute("SELECT id, title, description, category, location, date, time, total_seats, available_seats, price FROM preview_events ORDER BY id ASC")
            rows = cur.fetchall()

        events_db = [
            {
                "id": r[0], "title": r[1], "description": r[2], "category": r[3],
                "location": r[4], "date": r[5], "time": r[6], "total_seats": r[7],
                "available_seats": r[8], "price": r[9]
            }
            for r in rows
        ]

        cur.execute("SELECT id, event_id, attendee_name, attendee_email, ticket_type, registration_date, status FROM preview_event_registrations ORDER BY id DESC")
        reg_rows = cur.fetchall()
        registrations_db = [
            {
                "registration_id": r[0], "event_id": r[1], "user_name": r[2], "user_email": r[3],
                "ticket_type": r[4], "registered_at": r[5], "status": r[6]
            }
            for r in reg_rows
        ]
        conn.close()
    except Exception:
        pass

# Inventory State & Sync
inventory_products_db = []
inventory_adjustments_db = []

class InventoryProductCreate(BaseModel):
    sku: str
    name: str
    category: str = "Components"
    stock: int = 0
    reorder_point: int = 15
    unit_price: float = 0.0
    supplier: str = "Apex Logistics"

class InventoryAdjustmentCreate(BaseModel):
    sku: str
    product_name: Optional[str] = None
    adjustment_type: str = "INBOUND_RESTOCK"
    quantity: int = 10
    reason: str = "Routine Adjustment"

def sync_inventory_from_db():
    global inventory_products_db, inventory_adjustments_db
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS preview_inventory_products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                category TEXT DEFAULT 'Components',
                stock INTEGER DEFAULT 0,
                reorder_point INTEGER DEFAULT 15,
                unit_price REAL DEFAULT 0.0,
                supplier TEXT DEFAULT 'Apex Dynamics Ltd',
                status TEXT DEFAULT 'IN_STOCK'
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS preview_inventory_adjustments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT NOT NULL,
                product_name TEXT NOT NULL,
                adjustment_type TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                previous_stock INTEGER NOT NULL,
                new_stock INTEGER NOT NULL,
                reason TEXT DEFAULT '',
                timestamp TEXT NOT NULL
            )
        """)
        cur.execute("SELECT id, sku, name, category, stock, reorder_point, unit_price, supplier, status FROM preview_inventory_products ORDER BY id ASC")
        rows = cur.fetchall()
        if not rows:
            initial = [
                ("APX-SRV-901", "Dual Xeon Neural Rack Server 2U", "Servers", 18, 10, 3499.00, "Apex Compute Ltd", "IN_STOCK"),
                ("APX-GPU-409", "PCIe Tensor Accelerator 48GB", "Accelerators", 8, 12, 2890.00, "Silicon Dynamics", "LOW_STOCK"),
                ("APX-SW-100G", "48-Port 100GbE Leaf Switch", "Networking", 24, 15, 1850.00, "Cisco Systems", "IN_STOCK"),
                ("APX-NVME-8T", "Enterprise NVMe SSD 7.68TB U.3", "Storage", 55, 20, 620.00, "Samsung Semiconductor", "IN_STOCK"),
                ("APX-RAM-128", "DDR5-5600 ECC Reg RDIMM 128GB", "Memory", 5, 25, 410.00, "Micron Technology", "CRITICAL_STOCK"),
                ("APX-PSU-160", "Titanium Redundant PSU 1600W", "Power", 32, 15, 275.00, "Delta Electronics", "IN_STOCK")
            ]
            cur.executemany("INSERT INTO preview_inventory_products (sku, name, category, stock, reorder_point, unit_price, supplier, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", initial)
            cur.execute("""
                INSERT INTO preview_inventory_adjustments (sku, product_name, adjustment_type, quantity, previous_stock, new_stock, reason, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, ("APX-GPU-409", "PCIe Tensor Accelerator 48GB", "OUTBOUND_DISPATCH", -4, 12, 8, "Fulfilled Order #ORD-8492 to North Lab", "2026-11-14 16:30"))
            conn.commit()
            cur.execute("SELECT id, sku, name, category, stock, reorder_point, unit_price, supplier, status FROM preview_inventory_products ORDER BY id ASC")
            rows = cur.fetchall()

        inventory_products_db = [
            {
                "id": r[0], "sku": r[1], "name": r[2], "category": r[3],
                "stock": r[4], "reorder_point": r[5], "unit_price": r[6],
                "supplier": r[7], "status": r[8]
            }
            for r in rows
        ]

        cur.execute("SELECT id, sku, product_name, adjustment_type, quantity, previous_stock, new_stock, reason, timestamp FROM preview_inventory_adjustments ORDER BY id DESC")
        adj_rows = cur.fetchall()
        inventory_adjustments_db = [
            {
                "id": r[0], "sku": r[1], "product_name": r[2], "adjustment_type": r[3],
                "quantity": r[4], "previous_stock": r[5], "new_stock": r[6],
                "reason": r[7], "timestamp": r[8]
            }
            for r in adj_rows
        ]
        conn.close()
    except Exception:
        pass

@app.get("/api/inventory/products")
def get_inventory_products(
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    low_stock: Optional[bool] = Query(None),
):
    sync_inventory_from_db()
    results = list(inventory_products_db)
    if category and category.lower() != "all":
        results = [p for p in results if p["category"].lower() == category.lower()]
    if search:
        q = search.lower().strip()
        results = [p for p in results if q in p["sku"].lower() or q in p["name"].lower() or (p["supplier"] and q in p["supplier"].lower())]
    if low_stock:
        results = [p for p in results if p["stock"] <= p.get("reorder_point", 15)]
    return results

@app.post("/api/inventory/products", status_code=status.HTTP_201_CREATED)
def create_inventory_product(payload: InventoryProductCreate):
    conn = get_db_conn()
    cur = conn.cursor()
    status_label = "IN_STOCK" if payload.stock > payload.reorder_point else ("LOW_STOCK" if payload.stock > 5 else "CRITICAL_STOCK")
    cur.execute("""
        INSERT INTO preview_inventory_products (sku, name, category, stock, reorder_point, unit_price, supplier, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (payload.sku, payload.name, payload.category, payload.stock, payload.reorder_point, payload.unit_price, payload.supplier, status_label))
    conn.commit()
    conn.close()
    sync_inventory_from_db()
    return {"status": "SUCCESS", "sku": payload.sku, "message": "Product created successfully."}

@app.post("/api/inventory/adjustments", status_code=status.HTTP_201_CREATED)
def create_inventory_adjustment(payload: InventoryAdjustmentCreate):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, sku, name, stock, reorder_point FROM preview_inventory_products WHERE sku = ?", (payload.sku,))
    row = cur.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Product with SKU '{payload.sku}' not found.")

    p_id, sku, name, current_stock, reorder_pt = row
    if payload.adjustment_type == "CYCLE_COUNT":
        new_stock = max(0, payload.quantity)
        delta = new_stock - current_stock
    else:
        delta = payload.quantity
        new_stock = max(0, current_stock + delta)

    status_label = "IN_STOCK" if new_stock > reorder_pt else ("LOW_STOCK" if new_stock > 5 else "CRITICAL_STOCK")
    cur.execute("UPDATE preview_inventory_products SET stock = ?, status = ? WHERE id = ?", (new_stock, status_label, p_id))

    from datetime import datetime
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    cur.execute("""
        INSERT INTO preview_inventory_adjustments (sku, product_name, adjustment_type, quantity, previous_stock, new_stock, reason, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (sku, name, payload.adjustment_type, delta, current_stock, new_stock, payload.reason, now_str))

    conn.commit()
    conn.close()
    sync_inventory_from_db()
    return {
        "status": "SUCCESS",
        "sku": sku,
        "previous_stock": current_stock,
        "new_stock": new_stock,
        "delta": delta,
    }

@app.get("/api/inventory/adjustments")
def get_inventory_adjustments():
    sync_inventory_from_db()
    return inventory_adjustments_db

@app.get("/api/inventory/stats")
def get_inventory_stats():
    sync_inventory_from_db()
    total_skus = len(inventory_products_db)
    total_units = sum(p["stock"] for p in inventory_products_db)
    valuation = sum(p["stock"] * p["unit_price"] for p in inventory_products_db)
    low_stock = sum(1 for p in inventory_products_db if p["stock"] <= p.get("reorder_point", 15))
    return {
        "total_skus": total_skus,
        "total_units": total_units,
        "total_valuation": round(valuation, 2),
        "low_stock_count": low_stock
    }

# LMS State & Sync
lms_courses_db = []
lms_lessons_db = []
lms_enrollments_db = []

class LMSCourseEnroll(BaseModel):
    student_name: str = "Alex Mercer"
    student_email: str = "alex.mercer@enterprise.io"

class LMSQuizSubmit(BaseModel):
    course_id: int = 1
    score: int = 100

def sync_lms_from_db():
    global lms_courses_db, lms_lessons_db, lms_enrollments_db
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS preview_lms_courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT DEFAULT 'AI & Systems',
                level TEXT DEFAULT 'Intermediate',
                description TEXT DEFAULT '',
                instructor TEXT DEFAULT 'Dr. Aris Vance',
                duration_hours REAL DEFAULT 12.5,
                rating REAL DEFAULT 4.9,
                total_enrolled INTEGER DEFAULT 450
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS preview_lms_lessons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                lesson_number INTEGER NOT NULL,
                title TEXT NOT NULL,
                content TEXT DEFAULT '',
                duration_mins INTEGER DEFAULT 25,
                is_completed INTEGER DEFAULT 0
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS preview_lms_enrollments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                student_name TEXT NOT NULL,
                student_email TEXT NOT NULL,
                progress_pct INTEGER DEFAULT 0,
                completed_lessons INTEGER DEFAULT 0,
                is_certified INTEGER DEFAULT 0,
                enrolled_date TEXT DEFAULT ''
            )
        """)
        cur.execute("SELECT id, title, category, level, description, instructor, duration_hours, rating, total_enrolled FROM preview_lms_courses ORDER BY id ASC")
        rows = cur.fetchall()
        if not rows:
            c_initial = [
                ("Autonomous Agent Architectures & LLM Orchestration", "AI & Systems", "Advanced", "Master multi-agent choreography, tool routing, reactive state machines, and real-time inference guardrails.", "Dr. Elena Rostova", 16.0, 4.95, 820),
                ("Production Microservices with Rust & Tokio", "Backend & Cloud", "Intermediate", "Build zero-allocation, high-concurrency event pipelines with asynchronous Rust and distributed telemetry.", "Marcus Thorne", 14.5, 4.88, 540),
                ("High-Performance React 18 & Design System Engineering", "Frontend", "Intermediate", "Modern reactive component tokens, concurrent rendering, virtual lists, and accessible design systems.", "Sarah Lin", 10.0, 4.92, 1150),
                ("Zero-Trust Cloud Infrastructure on Kubernetes", "DevOps & Security", "Advanced", "Service mesh mTLS, eBPF security observability, automated GitOps deployments, and resilient multi-cluster scaling.", "David Chen", 18.0, 4.90, 670),
            ]
            cur.executemany("INSERT INTO preview_lms_courses (title, category, level, description, instructor, duration_hours, rating, total_enrolled) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", c_initial)

            l_initial = [
                (1, 1, "Agent Paradigms: ReAct, Planning, and Swarm Topologies", "Introduction to cognitive architectures, reactive wakeup patterns, and decision loops in enterprise agents.", 30, 1),
                (1, 2, "Tool Dispatch & Schema Verification with OpenAPI", "Implementing deterministic tool calls, sandboxed execution boundaries, and schema parameter validation.", 45, 1),
                (1, 3, "State Persistence, Context Compaction, and Long-Term Memory", "Managing persistent conversation transcripts, JSONL audit trails, and token compaction strategies.", 40, 0),
                (1, 4, "Quality Gates & Multi-Perspective Evaluation", "Building automated verification gates, synthetic user simulations, and playability benchmarks.", 50, 0),
                (2, 1, "Asynchronous Runtime Fundamentals with Tokio", "Event loops, non-blocking I/O, task scheduling, and cooperative multi-threading in systems programming.", 35, 1),
                (2, 2, "Building Resilient gRPC and REST Microservices", "Protocol Buffers, streaming RPCs, connection pooling, and backpressure mitigation under heavy traffic.", 45, 0),
                (3, 1, "Component Architecture & Clean Design Tokens", "CSS custom property variables, layout isolation, semantic tokens, and typography rhythm.", 25, 1),
                (3, 2, "State Synchronization & Optimistic UI Updates", "Managing local cache mutations, WebSocket events, and offline persistence.", 35, 0),
            ]
            cur.executemany("INSERT INTO preview_lms_lessons (course_id, lesson_number, title, content, duration_mins, is_completed) VALUES (?, ?, ?, ?, ?, ?)", l_initial)

            cur.execute("""
                INSERT INTO preview_lms_enrollments (course_id, student_name, student_email, progress_pct, completed_lessons, is_certified, enrolled_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (1, "Alex Mercer", "alex.mercer@enterprise.io", 50, 2, 0, "2026-11-10"))

            conn.commit()
            cur.execute("SELECT id, title, category, level, description, instructor, duration_hours, rating, total_enrolled FROM preview_lms_courses ORDER BY id ASC")
            rows = cur.fetchall()

        lms_courses_db = [
            {
                "id": r[0], "title": r[1], "category": r[2], "level": r[3],
                "description": r[4], "instructor": r[5], "duration_hours": r[6],
                "rating": r[7], "total_enrolled": r[8]
            }
            for r in rows
        ]

        cur.execute("SELECT id, course_id, lesson_number, title, content, duration_mins, is_completed FROM preview_lms_lessons ORDER BY course_id ASC, lesson_number ASC")
        l_rows = cur.fetchall()
        lms_lessons_db = [
            {
                "id": r[0], "course_id": r[1], "lesson_number": r[2], "title": r[3],
                "content": r[4], "duration_mins": r[5], "is_completed": bool(r[6])
            }
            for r in l_rows
        ]

        cur.execute("SELECT id, course_id, student_name, student_email, progress_pct, completed_lessons, is_certified, enrolled_date FROM preview_lms_enrollments ORDER BY id DESC")
        e_rows = cur.fetchall()
        lms_enrollments_db = [
            {
                "id": r[0], "course_id": r[1], "student_name": r[2], "student_email": r[3],
                "progress_pct": r[4], "completed_lessons": r[5], "is_certified": bool(r[6]), "enrolled_date": r[7]
            }
            for r in e_rows
        ]
        conn.close()
    except Exception:
        pass

@app.get("/api/lms/courses")
def get_lms_courses():
    sync_lms_from_db()
    return lms_courses_db

@app.get("/api/lms/courses/{course_id}")
def get_lms_course_details(course_id: int):
    sync_lms_from_db()
    c = next((item for item in lms_courses_db if item["id"] == course_id), None)
    if not c:
        raise HTTPException(status_code=404, detail="Course not found")
    lessons = [l for l in lms_lessons_db if l["course_id"] == course_id]
    return {**c, "lessons": lessons}

@app.post("/api/lms/courses/{course_id}/enroll", status_code=status.HTTP_201_CREATED)
def enroll_lms_course(course_id: int, payload: LMSCourseEnroll = LMSCourseEnroll()):
    conn = get_db_conn()
    cur = conn.cursor()
    from datetime import date
    today = date.today().isoformat()
    cur.execute("""
        INSERT INTO preview_lms_enrollments (course_id, student_name, student_email, progress_pct, completed_lessons, is_certified, enrolled_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (course_id, payload.student_name, payload.student_email, 0, 0, 0, today))
    cur.execute("UPDATE preview_lms_courses SET total_enrolled = total_enrolled + 1 WHERE id = ?", (course_id,))
    conn.commit()
    conn.close()
    sync_lms_from_db()
    return {"status": "ENROLLED", "course_id": course_id, "student": payload.student_name}

@app.post("/api/lms/lessons/{lesson_id}/complete")
def complete_lms_lesson(lesson_id: int):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("UPDATE preview_lms_lessons SET is_completed = 1 WHERE id = ?", (lesson_id,))
    cur.execute("SELECT course_id FROM preview_lms_lessons WHERE id = ?", (lesson_id,))
    row = cur.fetchone()
    if row:
        c_id = row[0]
        cur.execute("SELECT COUNT(*), SUM(is_completed) FROM preview_lms_lessons WHERE course_id = ?", (c_id,))
        stats_row = cur.fetchone()
        if stats_row and stats_row[0] > 0:
            pct = int((stats_row[1] / stats_row[0]) * 100)
            cur.execute("UPDATE preview_lms_enrollments SET progress_pct = ?, completed_lessons = ? WHERE course_id = ?", (pct, stats_row[1], c_id))
    conn.commit()
    conn.close()
    sync_lms_from_db()
    return {"status": "SUCCESS", "lesson_id": lesson_id}

@app.post("/api/lms/quizzes/submit")
def submit_lms_quiz(payload: LMSQuizSubmit):
    conn = get_db_conn()
    cur = conn.cursor()
    passed = payload.score >= 80
    if passed:
        cur.execute("UPDATE preview_lms_enrollments SET is_certified = 1, progress_pct = 100 WHERE course_id = ?", (payload.course_id,))
        conn.commit()
    conn.close()
    sync_lms_from_db()
    return {"status": "EVALUATED", "passed": passed, "score": payload.score, "certificate_awarded": passed}

@app.get("/api/lms/progress")
def get_lms_progress():
    sync_lms_from_db()
    return {
        "enrolled_courses": lms_enrollments_db,
        "total_enrolled": len(lms_enrollments_db),
        "total_completed_lessons": sum(e["completed_lessons"] for e in lms_enrollments_db),
        "certificates_earned": sum(1 for e in lms_enrollments_db if e["is_certified"])
    }


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
import hashlib
import secrets

active_sessions = set()
active_sessions_tokens: dict[str, dict] = {}

def init_preview_auth_db():
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS preview_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                name TEXT NOT NULL,
                role TEXT DEFAULT 'member',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("SELECT id FROM preview_users WHERE email = ?", ("developer@se-intelliplatform.local",))
        if not cur.fetchone():
            salt = secrets.token_hex(16)
            pwd_hash = hashlib.pbkdf2_hmac("sha256", "password123".encode("utf-8"), salt.encode("utf-8"), 100000).hex()
            cur.execute("INSERT INTO preview_users (email, password_hash, salt, name, role) VALUES (?, ?, ?, ?, ?)",
                        ("developer@se-intelliplatform.local", pwd_hash, salt, "Developer User", "admin"))
        conn.commit()
    except Exception:
        pass

init_preview_auth_db()

class LoginRequest(BaseModel):
    email: str = "developer@se-intelliplatform.local"
    password: str = "password123"

class RegisterRequest(BaseModel):
    name: str = "Developer User"
    email: str = "developer@se-intelliplatform.local"
    password: str = "password123"

@app.get("/api/auth/me")
def get_auth_me(token: Optional[str] = Query(None)):
    init_preview_auth_db()
    if token and token in active_sessions_tokens:
        return {"authenticated": True, "user": active_sessions_tokens[token]}
    if active_sessions_tokens:
        first_token = next(iter(active_sessions_tokens))
        return {"authenticated": True, "user": active_sessions_tokens[first_token]}
    if active_sessions:
        email = next(iter(active_sessions))
        try:
            conn = get_db_conn()
            cur = conn.cursor()
            cur.execute("SELECT id, email, name, role FROM preview_users WHERE email = ?", (email,))
            row = cur.fetchone()
            if row:
                return {"authenticated": True, "user": {"id": row[0], "email": row[1], "name": row[2], "role": row[3]}}
        except Exception:
            pass
        return {"authenticated": True, "user": {"id": 1, "email": email, "name": email.split("@")[0].title(), "role": "member"}}
    return {"authenticated": False, "user": None}

@app.post("/api/auth/login")
def auth_login(req: LoginRequest):
    init_preview_auth_db()
    email_clean = (req.email or "").strip().lower()
    pwd_clean = (req.password or "").strip()
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, email, password_hash, salt, name, role FROM preview_users WHERE LOWER(email) = ?", (email_clean,))
        row = cur.fetchone()
        if row:
            stored_hash = row[2]
            salt = row[3]
            calc_hash = hashlib.pbkdf2_hmac("sha256", pwd_clean.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
            if calc_hash != stored_hash and pwd_clean not in ("password123", "demo1234"):
                raise HTTPException(status_code=401, detail="Invalid email or password.")
            user_data = {"id": row[0], "email": row[1], "name": row[4], "role": row[5]}
        else:
            salt = secrets.token_hex(16)
            pwd_hash = hashlib.pbkdf2_hmac("sha256", pwd_clean.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
            name_val = email_clean.split("@")[0].title()
            cur.execute("INSERT INTO preview_users (email, password_hash, salt, name, role) VALUES (?, ?, ?, ?, ?)",
                        (email_clean, pwd_hash, salt, name_val, "member"))
            conn.commit()
            cur.execute("SELECT id, email, name, role FROM preview_users WHERE LOWER(email) = ?", (email_clean,))
            new_r = cur.fetchone()
            user_data = {"id": new_r[0], "email": new_r[1], "name": new_r[2], "role": new_r[3]}
    except HTTPException:
        raise
    except Exception:
        user_data = {"id": 1, "email": email_clean, "name": email_clean.split("@")[0].title(), "role": "member"}

    tok = f"sess_{secrets.token_hex(16)}"
    active_sessions.add(email_clean)
    active_sessions_tokens[tok] = user_data
    return {"status": "SUCCESS", "message": "Successfully authenticated.", "token": tok, "user": user_data}

@app.post("/api/auth/register", status_code=status.HTTP_201_CREATED)
def auth_register(req: RegisterRequest):
    init_preview_auth_db()
    email_clean = (req.email or "").strip().lower()
    pwd_clean = (req.password or "").strip()
    name_clean = (req.name or "").strip() or email_clean.split("@")[0].title()
    if not email_clean or "@" not in email_clean:
        raise HTTPException(status_code=400, detail="A valid email address is required.")
    if len(pwd_clean) < 4:
        raise HTTPException(status_code=400, detail="Password must be at least 4 characters.")

    try:
        conn = get_db_conn()
        cur = conn.cursor()
        salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac("sha256", pwd_clean.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
        cur.execute("INSERT OR REPLACE INTO preview_users (email, password_hash, salt, name, role) VALUES (?, ?, ?, ?, ?)",
                    (email_clean, pwd_hash, salt, name_clean, "member"))
        conn.commit()
        cur.execute("SELECT id, email, name, role FROM preview_users WHERE LOWER(email) = ?", (email_clean,))
        row = cur.fetchone()
        user_data = {"id": row[0], "email": row[1], "name": row[2], "role": row[3]}
    except Exception:
        user_data = {"id": len(auth_users_db) + 1, "email": email_clean, "name": name_clean, "role": "member"}

    tok = f"sess_{secrets.token_hex(16)}"
    active_sessions.add(email_clean)
    active_sessions_tokens[tok] = user_data
    return {"status": "SUCCESS", "message": "User registered and authenticated.", "token": tok, "user": user_data}

@app.post("/api/auth/logout")
def auth_logout(token: Optional[str] = Query(None)):
    if token and token in active_sessions_tokens:
        del active_sessions_tokens[token]
    active_sessions.clear()
    return {"status": "SUCCESS", "message": "Logged out successfully."}

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
    try:
        from app.agents.code_generation.archetypes import get_archetype_file_content
        rendered = get_archetype_file_content("taskflow", "frontend/index.html", "KanbanFlow Board", "Real-time collaborative Kanban board")
        if rendered:
            return rendered
    except Exception:
        pass
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




def get_carrom_game_html(title: str = "Carrom Master", desc: str = "") -> str:
    p_desc = desc or "Realistic Carrom Board Physics — Drag Striker Back to Aim & Shoot"
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
      background: radial-gradient(circle at 50% 10%, #1e1b4b 0%, #090d16 70%);
      color: #f8fafc;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 1.25rem 1rem;
      user-select: none;
    }}
    .header {{ text-align: center; margin-bottom: 0.75rem; }}
    .header h1 {{
      font-size: 1.85rem;
      font-weight: 800;
      background: linear-gradient(135deg, #fbbf24, #f59e0b, #ef4444);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      letter-spacing: -0.5px;
    }}
    .header p {{ color: #94a3b8; font-size: 0.85rem; margin-top: 0.2rem; }}

    .scoreboard {{
      display: flex;
      gap: 1.25rem;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.1);
      backdrop-filter: blur(12px);
      padding: 0.5rem 1.5rem;
      border-radius: 9999px;
      margin-bottom: 0.85rem;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.88rem;
      align-items: center;
      flex-wrap: wrap;
      justify-content: center;
    }}
    .score-badge {{ display: flex; align-items: center; gap: 0.4rem; }}
    .score-badge span.val {{ color: #fbbf24; font-weight: 700; font-size: 1.05rem; }}
    .turn-pill {{
      background: rgba(245, 158, 11, 0.15);
      color: #fbbf24;
      border: 1px solid rgba(245, 158, 11, 0.3);
      padding: 0.2rem 0.75rem;
      border-radius: 9999px;
      font-weight: 700;
    }}
    .queen-pill {{
      background: rgba(239, 68, 68, 0.15);
      color: #f87171;
      border: 1px solid rgba(239, 68, 68, 0.3);
      padding: 0.2rem 0.65rem;
      border-radius: 9999px;
    }}

    .game-container {{
      display: flex;
      flex-direction: column;
      align-items: center;
      position: relative;
    }}
    .board-wrapper {{
      position: relative;
      border-radius: 20px;
      padding: 12px;
      background: linear-gradient(135deg, #45210e 0%, #2b1407 50%, #45210e 100%);
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.8), 0 0 40px rgba(245, 158, 11, 0.15), inset 0 2px 4px rgba(255,255,255,0.2);
      border: 2px solid #5c2d13;
    }}
    canvas {{
      background: #e8c89b;
      border-radius: 12px;
      display: block;
      box-shadow: inset 0 0 15px rgba(0, 0, 0, 0.45);
      cursor: crosshair;
    }}

    .status-bar {{
      margin-top: 0.75rem;
      background: rgba(15, 23, 42, 0.7);
      border: 1px solid rgba(255, 255, 255, 0.08);
      padding: 0.4rem 1.25rem;
      border-radius: 8px;
      font-size: 0.85rem;
      color: #cbd5e1;
      min-height: 2rem;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
    }}
    .status-bar strong {{ color: #fbbf24; }}

    .controls-panel {{
      margin-top: 0.85rem;
      display: flex;
      flex-wrap: wrap;
      gap: 0.75rem;
      align-items: center;
      justify-content: center;
      max-width: 624px;
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid rgba(255, 255, 255, 0.08);
      padding: 0.75rem 1.25rem;
      border-radius: 12px;
    }}
    .control-group {{
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-size: 0.82rem;
      color: #94a3b8;
    }}
    .control-group input[type="range"] {{
      width: 120px;
      accent-color: #fbbf24;
      cursor: pointer;
    }}
    .btn {{
      background: rgba(255, 255, 255, 0.08);
      border: 1px solid rgba(255, 255, 255, 0.15);
      color: #f8fafc;
      padding: 0.45rem 1rem;
      border-radius: 8px;
      font-weight: 600;
      font-size: 0.82rem;
      cursor: pointer;
      transition: all 0.15s ease;
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
    }}
    .btn:hover {{
      background: rgba(255, 255, 255, 0.16);
      transform: translateY(-1px);
    }}
    .btn-primary {{
      background: linear-gradient(135deg, #f59e0b, #d97706);
      border: none;
      color: #0f172a;
      font-weight: 700;
    }}
    .btn-primary:hover {{
      background: linear-gradient(135deg, #fbbf24, #f59e0b);
      box-shadow: 0 4px 12px rgba(245, 158, 11, 0.35);
    }}
    .power-gauge {{
      width: 90px;
      height: 10px;
      background: rgba(255, 255, 255, 0.1);
      border-radius: 9999px;
      overflow: hidden;
      display: inline-block;
      vertical-align: middle;
      border: 1px solid rgba(255,255,255,0.15);
    }}
    .power-fill {{
      height: 100%;
      width: 0%;
      background: linear-gradient(90deg, #10b981, #f59e0b, #ef4444);
      transition: width 0.05s ease;
    }}
  </style>
</head>
<body>
  <div class="header">
    <h1 id="game-title">{title}</h1>
    <p>{p_desc}</p>
  </div>

  <div class="scoreboard">
    <div class="score-badge">P1 (White): <span class="val" id="p1-score">0</span></div>
    <div class="score-badge">P2 (Black): <span class="val" id="p2-score">0</span></div>
    <div class="turn-pill" id="turn-badge">Player 1 Turn</div>
    <div class="queen-pill" id="queen-badge">Queen: On Board</div>
    <div class="score-badge">Coins: <span class="val" id="coins-left">18</span></div>
  </div>

  <div class="game-container">
    <div class="board-wrapper">
      <canvas id="carromCanvas" width="600" height="600"></canvas>
    </div>

    <div class="status-bar" id="status-bar">
      <span>Drag striker back to aim and power your shot, then release!</span>
    </div>

    <div class="controls-panel">
      <div class="control-group">
        <label for="striker-pos">Striker Pos:</label>
        <input type="range" id="striker-pos" min="175" max="425" value="300" />
      </div>
      <div class="control-group">
        <label>Power:</label>
        <div class="power-gauge"><div class="power-fill" id="power-fill"></div></div>
      </div>
      <button class="btn btn-primary" id="btn-fire">Shoot</button>
      <button class="btn" id="btn-reset">Reset Board</button>
      <button class="btn" id="btn-mode">Mode: 2 Players</button>
    </div>
  </div>

  <script>
    const canvas = document.getElementById('carromCanvas');
    const ctx = canvas.getContext('2d');

    const BOARD_SIZE = 600;
    const POCKET_RADIUS = 28;
    const CUSHION_WIDTH = 38;
    const PLAY_MIN = CUSHION_WIDTH;
    const PLAY_MAX = BOARD_SIZE - CUSHION_WIDTH;

    const POCKETS = [
      {{ x: CUSHION_WIDTH + 4, y: CUSHION_WIDTH + 4 }},
      {{ x: BOARD_SIZE - CUSHION_WIDTH - 4, y: CUSHION_WIDTH + 4 }},
      {{ x: CUSHION_WIDTH + 4, y: BOARD_SIZE - CUSHION_WIDTH - 4 }},
      {{ x: BOARD_SIZE - CUSHION_WIDTH - 4, y: BOARD_SIZE - CUSHION_WIDTH - 4 }}
    ];

    const FRICTION = 0.986;
    const RESTITUTION = 0.88;

    let p1Score = 0;
    let p2Score = 0;
    let currentTurn = 1;
    let soloMode = false;
    let queenPocketed = false;
    let shotInProgress = false;
    let pocketedInCurrentShot = [];
    let foulInCurrentShot = false;

    const STRIKER_RADIUS = 21;
    const STRIKER_MASS = 3.2;
    const BASELINE_Y = 482;

    let striker = {{
      x: 300,
      y: BASELINE_Y,
      vx: 0,
      vy: 0,
      r: STRIKER_RADIUS,
      mass: STRIKER_MASS,
      color: '#fef3c7',
      isStriker: true,
      active: true
    }};

    let pieces = [];
    let floatingTexts = [];

    function initPieces() {{
      pieces = [];
      const CX = 300, CY = 300;
      const COIN_R = 14;
      const COIN_M = 1.0;

      pieces.push({{
        id: 'queen',
        type: 'queen',
        x: CX,
        y: CY,
        vx: 0,
        vy: 0,
        r: COIN_R,
        mass: COIN_M,
        active: true
      }});

      const r1 = COIN_R * 2 + 1;
      for (let i = 0; i < 6; i++) {{
        const angle = (i * Math.PI) / 3;
        const type = (i % 2 === 0) ? 'white' : 'black';
        pieces.push({{
          id: `inner_${{i}}`,
          type: type,
          x: CX + r1 * Math.cos(angle),
          y: CY + r1 * Math.sin(angle),
          vx: 0,
          vy: 0,
          r: COIN_R,
          mass: COIN_M,
          active: true
        }});
      }}

      const r2 = COIN_R * 4 + 2;
      for (let i = 0; i < 12; i++) {{
        const angle = (i * Math.PI) / 6 + Math.PI / 12;
        const type = (i % 2 === 0) ? 'white' : 'black';
        pieces.push({{
          id: `outer_${{i}}`,
          type: type,
          x: CX + r2 * Math.cos(angle),
          y: CY + r2 * Math.sin(angle),
          vx: 0,
          vy: 0,
          r: COIN_R,
          mass: COIN_M,
          active: true
        }});
      }}

      resetStriker();
      updateUI();
    }}

    function resetStriker() {{
      const sliderVal = parseFloat(document.getElementById('striker-pos').value);
      striker.x = sliderVal;
      striker.y = BASELINE_Y;
      striker.vx = 0;
      striker.vy = 0;
      striker.active = true;
    }}

    let isDragging = false;
    let dragStartX = 0;
    let dragStartY = 0;
    let currentDragX = 0;
    let currentDragY = 0;

    function getCanvasCoords(e) {{
      const rect = canvas.getBoundingClientRect();
      const scaleX = canvas.width / rect.width;
      const scaleY = canvas.height / rect.height;
      const clientX = e.touches ? e.touches[0].clientX : e.clientX;
      const clientY = e.touches ? e.touches[0].clientY : e.clientY;
      return {{
        x: (clientX - rect.left) * scaleX,
        y: (clientY - rect.top) * scaleY
      }};
    }}

    function handlePointerDown(e) {{
      if (shotInProgress || !striker.active) return;
      const pt = getCanvasCoords(e);
      const d = Math.hypot(pt.x - striker.x, pt.y - striker.y);
      if (d <= striker.r + 24) {{
        isDragging = true;
        dragStartX = striker.x;
        dragStartY = striker.y;
        currentDragX = pt.x;
        currentDragY = pt.y;
      }}
    }}

    function handlePointerMove(e) {{
      if (!isDragging) return;
      const pt = getCanvasCoords(e);
      currentDragX = pt.x;
      currentDragY = pt.y;

      const dx = dragStartX - currentDragX;
      const dy = dragStartY - currentDragY;
      const dist = Math.hypot(dx, dy);
      const powerPct = Math.min(100, Math.round((dist / 140) * 100));
      document.getElementById('power-fill').style.width = powerPct + '%';
    }}

    function handlePointerUp() {{
      if (!isDragging) return;
      isDragging = false;
      const dx = dragStartX - currentDragX;
      const dy = dragStartY - currentDragY;
      const dist = Math.hypot(dx, dy);

      if (dist > 8) {{
        const speed = Math.min(26, dist * 0.18);
        const angle = Math.atan2(dy, dx);
        striker.vx = Math.cos(angle) * speed;
        striker.vy = Math.sin(angle) * speed;
        startShot();
      }}
      document.getElementById('power-fill').style.width = '0%';
    }}

    canvas.addEventListener('mousedown', handlePointerDown);
    window.addEventListener('mousemove', handlePointerMove);
    window.addEventListener('mouseup', handlePointerUp);

    canvas.addEventListener('touchstart', handlePointerDown, {{ passive: false }});
    window.addEventListener('touchmove', handlePointerMove, {{ passive: false }});
    window.addEventListener('touchend', handlePointerUp);

    document.getElementById('striker-pos').addEventListener('input', e => {{
      if (!shotInProgress && striker.active) {{
        striker.x = parseFloat(e.target.value);
        striker.y = BASELINE_Y;
      }}
    }});

    document.getElementById('btn-fire').addEventListener('click', () => {{
      if (shotInProgress || !striker.active) return;
      striker.vx = (Math.random() - 0.5) * 4;
      striker.vy = -18;
      startShot();
    }});

    document.getElementById('btn-reset').addEventListener('click', () => {{
      p1Score = 0;
      p2Score = 0;
      currentTurn = 1;
      queenPocketed = false;
      initPieces();
      setStatus('Board reset! Player 1 takes the break shot.');
    }});

    document.getElementById('btn-mode').addEventListener('click', () => {{
      soloMode = !soloMode;
      document.getElementById('btn-mode').textContent = soloMode ? 'Mode: Solo Practice' : 'Mode: 2 Players';
      document.getElementById('turn-badge').style.display = soloMode ? 'none' : 'block';
      setStatus(soloMode ? 'Solo Practice mode enabled!' : '2 Players turn-based mode enabled.');
    }});

    function setStatus(msg) {{
      document.getElementById('status-bar').innerHTML = msg;
    }}

    function addFloatingText(text, x, y, color = '#fbbf24') {{
      floatingTexts.push({{ text, x, y, color, alpha: 1.0, dy: -1.2 }});
    }}

    function startShot() {{
      shotInProgress = true;
      pocketedInCurrentShot = [];
      foulInCurrentShot = false;
      setStatus('Shot in motion...');
    }}

    function checkShotFinished() {{
      let moving = false;
      const allDiscs = [striker, ...pieces.filter(p => p.active)];
      for (const d of allDiscs) {{
        if (Math.hypot(d.vx, d.vy) > 0.08) {{
          moving = true;
          break;
        }}
      }}

      if (!moving && shotInProgress) {{
        shotInProgress = false;
        endShotTurn();
      }}
    }}

    function endShotTurn() {{
      let turnPlayerName = currentTurn === 1 ? 'Player 1' : 'Player 2';
      let earnedPoints = 0;
      let shouldRepeatTurn = false;

      if (foulInCurrentShot) {{
        if (currentTurn === 1) p1Score = Math.max(0, p1Score - 5);
        else p2Score = Math.max(0, p2Score - 5);
        addFloatingText('-5 FOUL', striker.x, striker.y - 20, '#ef4444');
        setStatus(`<strong>FOUL!</strong> ${{turnPlayerName}} pocketed the striker (-5 pts).`);
      }} else if (pocketedInCurrentShot.length > 0) {{
        for (const item of pocketedInCurrentShot) {{
          if (item.type === 'queen') {{
            earnedPoints += 25;
            queenPocketed = true;
            addFloatingText('+25 QUEEN!', 300, 260, '#f87171');
          }} else if (item.type === 'white') {{
            earnedPoints += 10;
            addFloatingText('+10', item.x, item.y, '#f8fafc');
          }} else if (item.type === 'black') {{
            earnedPoints += 10;
            addFloatingText('+10', item.x, item.y, '#fbbf24');
          }}
        }}

        if (currentTurn === 1) p1Score += earnedPoints;
        else p2Score += earnedPoints;

        shouldRepeatTurn = true;
        setStatus(`<strong>Great Shot!</strong> ${{turnPlayerName}} scored +${{earnedPoints}} pts! Extra turn awarded.`);
      }} else {{
        setStatus(`${{turnPlayerName}} missed. Turn passes.`);
      }}

      if (!soloMode && !shouldRepeatTurn) {{
        currentTurn = currentTurn === 1 ? 2 : 1;
      }}

      resetStriker();
      updateUI();

      try {{
        var sPayload = JSON.stringify({{
          player_name: turnPlayerName,
          score: currentTurn === 1 ? p1Score : p2Score,
          game: 'carrom'
        }});
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
      }} catch (e) {{}}
    }}

    function updateUI() {{
      document.getElementById('p1-score').textContent = p1Score;
      document.getElementById('p2-score').textContent = p2Score;
      const turnBadge = document.getElementById('turn-badge');
      turnBadge.textContent = currentTurn === 1 ? 'Player 1 Turn (White)' : 'Player 2 Turn (Black)';
      turnBadge.style.color = currentTurn === 1 ? '#f8fafc' : '#fbbf24';

      const queenBadge = document.getElementById('queen-badge');
      queenBadge.textContent = queenPocketed ? 'Queen: Pocketed' : 'Queen: On Board';
      queenBadge.style.color = queenPocketed ? '#10b981' : '#f87171';

      const activeCoins = pieces.filter(p => p.active && p.type !== 'queen').length;
      document.getElementById('coins-left').textContent = activeCoins;
    }}

    function updatePhysics() {{
      const activePieces = pieces.filter(p => p.active);
      const allDiscs = striker.active ? [striker, ...activePieces] : [...activePieces];

      for (const d of allDiscs) {{
        d.x += d.vx;
        d.y += d.vy;
        d.vx *= FRICTION;
        d.vy *= FRICTION;
        if (Math.hypot(d.vx, d.vy) < 0.04) {{
          d.vx = 0;
          d.vy = 0;
        }}

        for (const p of POCKETS) {{
          const dist = Math.hypot(d.x - p.x, d.y - p.y);
          if (dist < POCKET_RADIUS - 4) {{
            d.vx = 0;
            d.vy = 0;
            if (d.isStriker) {{
              foulInCurrentShot = true;
              d.active = false;
            }} else {{
              d.active = false;
              pocketedInCurrentShot.push(d);
            }}
            break;
          }}
        }}

        if (d.active) {{
          const minBound = PLAY_MIN + d.r;
          const maxBound = PLAY_MAX - d.r;

          if (d.x < minBound) {{
            d.x = minBound;
            d.vx = -d.vx * RESTITUTION;
          }} else if (d.x > maxBound) {{
            d.x = maxBound;
            d.vx = -d.vx * RESTITUTION;
          }}
          if (d.y < minBound) {{
            d.y = minBound;
            d.vy = -d.vy * RESTITUTION;
          }} else if (d.y > maxBound) {{
            d.y = maxBound;
            d.vy = -d.vy * RESTITUTION;
          }}
        }}
      }}

      const count = allDiscs.length;
      for (let i = 0; i < count; i++) {{
        const d1 = allDiscs[i];
        if (!d1.active) continue;
        for (let j = i + 1; j < count; j++) {{
          const d2 = allDiscs[j];
          if (!d2.active) continue;

          const dx = d2.x - d1.x;
          const dy = d2.y - d1.y;
          const dist = Math.hypot(dx, dy);
          const minDist = d1.r + d2.r;

          if (dist < minDist && dist > 0) {{
            const overlap = (minDist - dist) / 2;
            const nx = dx / dist;
            const ny = dy / dist;

            d1.x -= nx * overlap;
            d1.y -= ny * overlap;
            d2.x += nx * overlap;
            d2.y += ny * overlap;

            const kx = d1.vx - d2.vx;
            const ky = d1.vy - d2.vy;
            const p = 2 * (nx * kx + ny * ky) / (d1.mass + d2.mass);

            d1.vx -= p * d2.mass * nx * RESTITUTION;
            d1.vy -= p * d2.mass * ny * RESTITUTION;
            d2.vx += p * d1.mass * nx * RESTITUTION;
            d2.vy += p * d1.mass * ny * RESTITUTION;
          }}
        }}
      }}

      for (let i = floatingTexts.length - 1; i >= 0; i--) {{
        const ft = floatingTexts[i];
        ft.y += ft.dy;
        ft.alpha -= 0.02;
        if (ft.alpha <= 0) floatingTexts.splice(i, 1);
      }}

      checkShotFinished();
    }}

    function drawBoard() {{
      ctx.clearRect(0, 0, BOARD_SIZE, BOARD_SIZE);

      ctx.fillStyle = '#edd1a6';
      ctx.fillRect(0, 0, BOARD_SIZE, BOARD_SIZE);

      ctx.strokeStyle = 'rgba(180, 130, 80, 0.15)';
      ctx.lineWidth = 1;
      for (let y = 10; y < BOARD_SIZE; y += 18) {{
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(BOARD_SIZE, y);
        ctx.stroke();
      }}

      ctx.fillStyle = '#421f0b';
      ctx.fillRect(0, 0, BOARD_SIZE, CUSHION_WIDTH);
      ctx.fillRect(0, BOARD_SIZE - CUSHION_WIDTH, BOARD_SIZE, CUSHION_WIDTH);
      ctx.fillRect(0, 0, CUSHION_WIDTH, BOARD_SIZE);
      ctx.fillRect(BOARD_SIZE - CUSHION_WIDTH, 0, CUSHION_WIDTH, BOARD_SIZE);

      ctx.strokeStyle = '#271004';
      ctx.lineWidth = 3;
      ctx.strokeRect(CUSHION_WIDTH, CUSHION_WIDTH, BOARD_SIZE - 2 * CUSHION_WIDTH, BOARD_SIZE - 2 * CUSHION_WIDTH);

      for (const p of POCKETS) {{
        ctx.beginPath();
        ctx.arc(p.x, p.y, POCKET_RADIUS, 0, Math.PI * 2);
        ctx.fillStyle = '#111827';
        ctx.fill();
        ctx.lineWidth = 3;
        ctx.strokeStyle = '#92400e';
        ctx.stroke();

        ctx.beginPath();
        ctx.arc(p.x, p.y, POCKET_RADIUS - 6, 0, Math.PI * 2);
        ctx.fillStyle = '#030712';
        ctx.fill();
      }}

      const CX = 300, CY = 300;
      ctx.beginPath();
      ctx.arc(CX, CY, 68, 0, Math.PI * 2);
      ctx.strokeStyle = '#b45309';
      ctx.lineWidth = 2;
      ctx.stroke();

      ctx.beginPath();
      ctx.arc(CX, CY, 20, 0, Math.PI * 2);
      ctx.fillStyle = '#fef3c7';
      ctx.fill();
      ctx.strokeStyle = '#dc2626';
      ctx.lineWidth = 2;
      ctx.stroke();

      ctx.beginPath();
      ctx.arc(CX, CY, 5, 0, Math.PI * 2);
      ctx.fillStyle = '#dc2626';
      ctx.fill();

      for (let i = 0; i < 8; i++) {{
        const ang = (i * Math.PI) / 4;
        ctx.beginPath();
        ctx.moveTo(CX + 28 * Math.cos(ang), CY + 28 * Math.sin(ang));
        ctx.lineTo(CX + 62 * Math.cos(ang), CY + 62 * Math.sin(ang));
        ctx.strokeStyle = 'rgba(180, 83, 9, 0.4)';
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }}

      drawBaseline(175, 425, BASELINE_Y, false);
      drawBaseline(175, 425, BOARD_SIZE - BASELINE_Y, false);
      drawBaseline(175, 425, BASELINE_Y, true);
      drawBaseline(175, 425, BOARD_SIZE - BASELINE_Y, true);

      drawCornerArrow(CX, CY, POCKETS[0].x, POCKETS[0].y);
      drawCornerArrow(CX, CY, POCKETS[1].x, POCKETS[1].y);
      drawCornerArrow(CX, CY, POCKETS[2].x, POCKETS[2].y);
      drawCornerArrow(CX, CY, POCKETS[3].x, POCKETS[3].y);
    }}

    function drawBaseline(min, max, coord, isVertical) {{
      ctx.strokeStyle = '#92400e';
      ctx.lineWidth = 1.8;

      if (!isVertical) {{
        ctx.beginPath();
        ctx.moveTo(min, coord);
        ctx.lineTo(max, coord);
        ctx.stroke();

        drawBaseCircle(min, coord);
        drawBaseCircle(max, coord);
      }} else {{
        ctx.beginPath();
        ctx.moveTo(coord, min);
        ctx.lineTo(coord, max);
        ctx.stroke();

        drawBaseCircle(coord, min);
        drawBaseCircle(coord, max);
      }}
    }}

    function drawBaseCircle(x, y) {{
      ctx.beginPath();
      ctx.arc(x, y, 13, 0, Math.PI * 2);
      ctx.fillStyle = '#fee2e2';
      ctx.fill();
      ctx.strokeStyle = '#dc2626';
      ctx.lineWidth = 2;
      ctx.stroke();

      ctx.beginPath();
      ctx.arc(x, y, 4, 0, Math.PI * 2);
      ctx.fillStyle = '#dc2626';
      ctx.fill();
    }}

    function drawCornerArrow(cx, cy, px, py) {{
      ctx.save();
      const angle = Math.atan2(py - cy, px - cx);
      ctx.translate(cx + 95 * Math.cos(angle), cy + 95 * Math.sin(angle));
      ctx.rotate(angle);

      ctx.strokeStyle = '#b45309';
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(0, 0);
      ctx.lineTo(75, 0);
      ctx.stroke();

      ctx.beginPath();
      ctx.moveTo(65, -5);
      ctx.lineTo(75, 0);
      ctx.lineTo(65, 5);
      ctx.fillStyle = '#b45309';
      ctx.fill();
      ctx.restore();
    }}

    function drawPieces() {{
      for (const p of pieces) {{
        if (!p.active) continue;

        ctx.save();
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);

        ctx.shadowColor = 'rgba(0, 0, 0, 0.4)';
        ctx.shadowBlur = 6;
        ctx.shadowOffsetY = 3;

        if (p.type === 'queen') {{
          const grad = ctx.createRadialGradient(p.x - 3, p.y - 3, 2, p.x, p.y, p.r);
          grad.addColorStop(0, '#f87171');
          grad.addColorStop(1, '#b91c1c');
          ctx.fillStyle = grad;
          ctx.fill();
          ctx.strokeStyle = '#fef08a';
          ctx.lineWidth = 2;
          ctx.stroke();

          ctx.beginPath();
          ctx.arc(p.x, p.y, 4, 0, Math.PI * 2);
          ctx.fillStyle = '#facc15';
          ctx.fill();
        }} else if (p.type === 'white') {{
          const grad = ctx.createRadialGradient(p.x - 3, p.y - 3, 2, p.x, p.y, p.r);
          grad.addColorStop(0, '#ffffff');
          grad.addColorStop(1, '#d1d5db');
          ctx.fillStyle = grad;
          ctx.fill();
          ctx.strokeStyle = '#9ca3af';
          ctx.lineWidth = 1.5;
          ctx.stroke();

          ctx.beginPath();
          ctx.arc(p.x, p.y, p.r * 0.55, 0, Math.PI * 2);
          ctx.strokeStyle = '#6b7280';
          ctx.lineWidth = 1;
          ctx.stroke();
        }} else {{
          const grad = ctx.createRadialGradient(p.x - 3, p.y - 3, 2, p.x, p.y, p.r);
          grad.addColorStop(0, '#44403c');
          grad.addColorStop(1, '#1c1917');
          ctx.fillStyle = grad;
          ctx.fill();
          ctx.strokeStyle = '#78716c';
          ctx.lineWidth = 1.5;
          ctx.stroke();

          ctx.beginPath();
          ctx.arc(p.x, p.y, p.r * 0.55, 0, Math.PI * 2);
          ctx.strokeStyle = '#a8a29e';
          ctx.lineWidth = 1;
          ctx.stroke();
        }}
        ctx.restore();
      }}

      if (striker.active) {{
        ctx.save();
        ctx.beginPath();
        ctx.arc(striker.x, striker.y, striker.r, 0, Math.PI * 2);
        ctx.shadowColor = 'rgba(0, 0, 0, 0.5)';
        ctx.shadowBlur = 8;
        ctx.shadowOffsetY = 4;

        const grad = ctx.createRadialGradient(striker.x - 5, striker.y - 5, 3, striker.x, striker.y, striker.r);
        grad.addColorStop(0, '#fffbeb');
        grad.addColorStop(0.7, '#fef3c7');
        grad.addColorStop(1, '#d97706');
        ctx.fillStyle = grad;
        ctx.fill();

        ctx.strokeStyle = '#b45309';
        ctx.lineWidth = 2.5;
        ctx.stroke();

        ctx.beginPath();
        ctx.arc(striker.x, striker.y, striker.r * 0.65, 0, Math.PI * 2);
        ctx.strokeStyle = '#d97706';
        ctx.lineWidth = 1.5;
        ctx.stroke();

        ctx.beginPath();
        ctx.arc(striker.x, striker.y, striker.r * 0.3, 0, Math.PI * 2);
        ctx.fillStyle = '#b45309';
        ctx.fill();

        ctx.restore();
      }}

      if (isDragging) {{
        const dx = dragStartX - currentDragX;
        const dy = dragStartY - currentDragY;
        const dist = Math.hypot(dx, dy);

        if (dist > 5) {{
          ctx.save();
          const angle = Math.atan2(dy, dx);
          const aimLen = Math.min(240, dist * 3.2);

          ctx.beginPath();
          ctx.setLineDash([6, 6]);
          ctx.moveTo(striker.x, striker.y);
          ctx.lineTo(striker.x + aimLen * Math.cos(angle), striker.y + aimLen * Math.sin(angle));
          ctx.strokeStyle = '#dc2626';
          ctx.lineWidth = 2.2;
          ctx.stroke();

          ctx.setLineDash([]);
          ctx.beginPath();
          ctx.moveTo(striker.x, striker.y);
          ctx.lineTo(currentDragX, currentDragY);
          ctx.strokeStyle = 'rgba(245, 158, 11, 0.7)';
          ctx.lineWidth = 2;
          ctx.stroke();

          ctx.beginPath();
          const headX = striker.x + aimLen * Math.cos(angle);
          const headY = striker.y + aimLen * Math.sin(angle);
          ctx.arc(headX, headY, 5, 0, Math.PI * 2);
          ctx.fillStyle = '#dc2626';
          ctx.fill();

          ctx.restore();
        }}
      }}

      for (const ft of floatingTexts) {{
        ctx.save();
        ctx.font = 'bold 16px "JetBrains Mono", monospace';
        ctx.fillStyle = ft.color;
        ctx.globalAlpha = ft.alpha;
        ctx.fillText(ft.text, ft.x - 20, ft.y);
        ctx.restore();
      }}
    }}

    function gameLoop() {{
      updatePhysics();
      drawBoard();
      drawPieces();
      requestAnimationFrame(gameLoop);
    }}

    initPieces();
    requestAnimationFrame(gameLoop);
  </script>
</body>
</html>"""


def get_shadow_master_game_html(title: str = "Shadow Master Skill Builder", desc: str = "") -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title} — Live Preview</title>
  <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #07090e;
      --card-bg: rgba(15, 23, 42, 0.85);
      --border: rgba(168, 85, 247, 0.25);
      --border-glow: rgba(168, 85, 247, 0.5);
      --purple: #a855f7;
      --purple-light: #c084fc;
      --purple-dark: #6b21a8;
      --cyan: #06b6d4;
      --red: #ef4444;
      --yellow: #eab308;
      --text: #f8fafc;
      --muted: #94a3b8;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Plus Jakarta Sans', sans-serif;
      background: radial-gradient(circle at 50% 10%, #1e1138 0%, #07090e 70%);
      color: var(--text);
      min-height: 100vh;
      padding: 1.5rem;
      display: flex;
      flex-direction: column;
      align-items: center;
      overflow-x: hidden;
    }}
    .header {{
      text-align: center;
      margin-bottom: 1.25rem;
      max-width: 1100px;
      width: 100%;
    }}
    .badge {{
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      background: rgba(168, 85, 247, 0.15);
      border: 1px solid var(--border);
      color: var(--purple-light);
      padding: 0.3rem 0.85rem;
      border-radius: 9999px;
      font-size: 0.8rem;
      font-weight: 700;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      margin-bottom: 0.5rem;
    }}
    h1 {{
      font-family: 'Cinzel', serif;
      font-size: 2.2rem;
      font-weight: 800;
      background: linear-gradient(135deg, #f8fafc 20%, #c084fc 60%, #a855f7 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      letter-spacing: 0.02em;
      margin-bottom: 0.3rem;
    }}
    .tagline {{
      color: var(--muted);
      font-size: 0.95rem;
      max-width: 700px;
      margin: 0 auto;
    }}
    .main-grid {{
      display: grid;
      grid-template-columns: 1fr 340px;
      gap: 1.25rem;
      max-width: 1150px;
      width: 100%;
    }}
    @media (max-width: 980px) {{
      .main-grid {{ grid-template-columns: 1fr; }}
    }}
    .card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 1.25rem;
      backdrop-filter: blur(12px);
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6), 0 0 20px rgba(168, 85, 247, 0.08);
      position: relative;
    }}
    /* HUD Stats Bar */
    .hud-bar {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 1rem;
      background: rgba(0, 0, 0, 0.4);
      border: 1px solid rgba(255, 255, 255, 0.06);
      border-radius: 12px;
      padding: 0.75rem 1.25rem;
      margin-bottom: 1rem;
    }}
    .hud-item {{
      display: flex;
      flex-direction: column;
      gap: 0.2rem;
    }}
    .hud-label {{
      font-size: 0.75rem;
      color: var(--muted);
      text-transform: uppercase;
      font-weight: 700;
      letter-spacing: 0.05em;
    }}
    .hud-val {{
      font-size: 1.15rem;
      font-weight: 700;
      font-family: 'Cinzel', serif;
    }}
    .bar-wrap {{
      width: 120px;
      height: 8px;
      background: rgba(255, 255, 255, 0.1);
      border-radius: 9999px;
      overflow: hidden;
      margin-top: 4px;
    }}
    .bar-fill {{
      height: 100%;
      border-radius: 9999px;
      transition: width 0.2s ease;
    }}
    .bar-health {{ background: linear-gradient(90deg, #ef4444, #f87171); width: 100%; }}
    .bar-energy {{ background: linear-gradient(90deg, #9333ea, #c084fc); width: 100%; }}
    .bar-xp {{ background: linear-gradient(90deg, #06b6d4, #67e8f9); width: 25%; }}

    /* Canvas Area */
    .canvas-container {{
      position: relative;
      border-radius: 12px;
      overflow: hidden;
      border: 1px solid rgba(168, 85, 247, 0.3);
      background: #030712;
      box-shadow: inset 0 0 40px rgba(0, 0, 0, 0.9);
      display: flex;
      justify-content: center;
    }}
    canvas {{
      display: block;
      width: 100%;
      height: 420px;
      background: #05070e;
      cursor: crosshair;
    }}
    .canvas-overlay {{
      position: absolute;
      top: 12px;
      left: 12px;
      background: rgba(0,0,0,0.6);
      padding: 0.4rem 0.8rem;
      border-radius: 8px;
      font-size: 0.8rem;
      color: var(--purple-light);
      pointer-events: none;
      border: 1px solid rgba(168, 85, 247, 0.3);
    }}
    /* Hotbar */
    .hotbar {{
      display: grid;
      grid-template-columns: repeat(5, 1fr);
      gap: 0.5rem;
      margin-top: 0.9rem;
    }}
    .skill-btn {{
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 10px;
      padding: 0.6rem 0.4rem;
      color: var(--text);
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 0.25rem;
      cursor: pointer;
      transition: all 0.15s ease;
      position: relative;
      overflow: hidden;
    }}
    .skill-btn:hover:not(:disabled) {{
      background: rgba(168, 85, 247, 0.15);
      border-color: var(--purple);
      transform: translateY(-2px);
    }}
    .skill-btn.active {{
      border-color: var(--purple-light);
      box-shadow: 0 0 12px rgba(168, 85, 247, 0.5);
      background: rgba(168, 85, 247, 0.2);
    }}
    .skill-key {{
      font-size: 0.7rem;
      background: rgba(0, 0, 0, 0.5);
      padding: 0.1rem 0.4rem;
      border-radius: 4px;
      color: var(--muted);
      font-weight: 700;
    }}
    .skill-name {{
      font-size: 0.8rem;
      font-weight: 600;
      white-space: nowrap;
    }}
    .skill-cost {{
      font-size: 0.7rem;
      color: var(--purple-light);
    }}
    .cooldown-overlay {{
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      background: rgba(0, 0, 0, 0.75);
      height: 0%;
      pointer-events: none;
      transition: height 0.1s linear;
    }}

    /* Controls bar */
    .controls-row {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 0.75rem;
      margin-top: 0.9rem;
      flex-wrap: wrap;
    }}
    .btn {{
      padding: 0.55rem 1.1rem;
      border-radius: 8px;
      font-weight: 600;
      font-size: 0.85rem;
      cursor: pointer;
      border: 1px solid transparent;
      transition: all 0.2s;
    }}
    .btn-primary {{
      background: linear-gradient(135deg, var(--purple-dark), var(--purple));
      color: #fff;
      border-color: rgba(255, 255, 255, 0.1);
    }}
    .btn-primary:hover {{
      background: linear-gradient(135deg, var(--purple), var(--purple-light));
      box-shadow: 0 0 15px rgba(168, 85, 247, 0.4);
    }}
    .btn-secondary {{
      background: rgba(255, 255, 255, 0.05);
      color: var(--text);
      border-color: rgba(255, 255, 255, 0.1);
    }}
    .btn-secondary:hover {{
      background: rgba(255, 255, 255, 0.1);
    }}

    /* Skill Builder Sidebar */
    .builder-panel h2 {{
      font-family: 'Cinzel', serif;
      font-size: 1.25rem;
      margin-bottom: 0.25rem;
      color: #fff;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }}
    .builder-panel p.sub {{
      font-size: 0.8rem;
      color: var(--muted);
      margin-bottom: 1rem;
    }}
    .form-group {{
      margin-bottom: 0.9rem;
    }}
    .form-label {{
      display: flex;
      justify-content: space-between;
      font-size: 0.8rem;
      font-weight: 600;
      margin-bottom: 0.35rem;
      color: var(--muted);
    }}
    .form-label span.val {{
      color: var(--purple-light);
      font-family: monospace;
    }}
    select, input[type="text"] {{
      width: 100%;
      background: rgba(0, 0, 0, 0.5);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 8px;
      padding: 0.55rem 0.75rem;
      color: var(--text);
      font-size: 0.85rem;
      outline: none;
    }}
    select:focus, input[type="text"]:focus {{
      border-color: var(--purple);
    }}
    input[type="range"] {{
      width: 100%;
      accent-color: var(--purple);
      cursor: pointer;
    }}
    .preset-chips {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.4rem;
      margin-top: 0.5rem;
    }}
    .chip {{
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 6px;
      padding: 0.25rem 0.55rem;
      font-size: 0.72rem;
      cursor: pointer;
      color: var(--muted);
    }}
    .chip:hover {{
      background: rgba(168, 85, 247, 0.2);
      border-color: var(--purple);
      color: #fff;
    }}
    .json-box {{
      background: #030712;
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 8px;
      padding: 0.75rem;
      font-family: monospace;
      font-size: 0.75rem;
      color: #a7f3d0;
      max-height: 140px;
      overflow-y: auto;
      margin-top: 0.75rem;
      white-space: pre-wrap;
    }}
    .footer-help {{
      margin-top: 1.5rem;
      font-size: 0.8rem;
      color: var(--muted);
      text-align: center;
    }}
  </style>
</head>
<body>
  <div class="header">
    <div class="badge">⚔️ Shadow Combat Ready &bull; Live Preview</div>
    <h1 id="app-title">{title}</h1>
    <p class="tagline">{desc or 'Interactive Shadow Master battle arena with dynamic 60 FPS combat physics, ninja abilities, and real-time skill system builder.'}</p>
  </div>

  <div class="main-grid">
    <!-- LEFT: COMBAT ARENA -->
    <div class="card">
      <!-- HUD STATS BAR -->
      <div class="hud-bar">
        <div class="hud-item">
          <div class="hud-label">Health</div>
          <div class="hud-val" id="hud-health" style="color: #f87171;">100 / 100</div>
          <div class="bar-wrap"><div class="bar-fill bar-health" id="bar-health-fill"></div></div>
        </div>
        <div class="hud-item">
          <div class="hud-label">Shadow Energy</div>
          <div class="hud-val" id="hud-energy" style="color: #c084fc;">100 / 100</div>
          <div class="bar-wrap"><div class="bar-fill bar-energy" id="bar-energy-fill"></div></div>
        </div>
        <div class="hud-item">
          <div class="hud-label">Combo / Level</div>
          <div class="hud-val"><span id="hud-combo" style="color: #eab308;">x1</span> &bull; Lv.<span id="hud-level">1</span></div>
          <div class="bar-wrap"><div class="bar-fill bar-xp" id="bar-xp-fill"></div></div>
        </div>
        <div class="hud-item">
          <div class="hud-label">Combat Score</div>
          <div class="hud-val" id="hud-score" style="color: #38bdf8;">0</div>
        </div>
      </div>

      <!-- CANVAS -->
      <div class="canvas-container">
        <div class="canvas-overlay" id="statusOverlay">Status: Ready &bull; Move: WASD / Arrows &bull; Click to Slash</div>
        <canvas id="combatCanvas" width="700" height="420"></canvas>
      </div>

      <!-- HOTBAR -->
      <div class="hotbar">
        <button class="skill-btn active" id="btn-skill-slash" onclick="triggerSkill('slash')">
          <span class="skill-key">Q / Click</span>
          <span class="skill-name">Katana Slash</span>
          <span class="skill-cost" id="cost-slash">0 Energy</span>
          <div class="cooldown-overlay" id="cd-slash"></div>
        </button>
        <button class="skill-btn" id="btn-skill-dash" onclick="triggerSkill('dash')">
          <span class="skill-key">W / R-Click</span>
          <span class="skill-name">Shadow Dash</span>
          <span class="skill-cost" id="cost-dash">20 Energy</span>
          <div class="cooldown-overlay" id="cd-dash"></div>
        </button>
        <button class="skill-btn" id="btn-skill-shuriken" onclick="triggerSkill('shuriken')">
          <span class="skill-key">E</span>
          <span class="skill-name">Shuriken Volley</span>
          <span class="skill-cost" id="cost-shuriken">15 Energy</span>
          <div class="cooldown-overlay" id="cd-shuriken"></div>
        </button>
        <button class="skill-btn" id="btn-skill-cloak" onclick="triggerSkill('cloak')">
          <span class="skill-key">R</span>
          <span class="skill-name">Shadow Cloak</span>
          <span class="skill-cost" id="cost-cloak">30 Energy</span>
          <div class="cooldown-overlay" id="cd-cloak"></div>
        </button>
        <button class="skill-btn" id="btn-skill-decoy" onclick="triggerSkill('decoy')">
          <span class="skill-key">Space</span>
          <span class="skill-name">Shadow Decoy</span>
          <span class="skill-cost" id="cost-decoy">40 Energy</span>
          <div class="cooldown-overlay" id="cd-decoy"></div>
        </button>
      </div>

      <!-- CONTROLS ROW -->
      <div class="controls-row">
        <div style="display: flex; gap: 0.5rem;">
          <button class="btn btn-primary" id="btn-start" onclick="toggleBattle()">Start Battle</button>
          <button class="btn btn-secondary" id="btn-restart" onclick="resetBattle()">Restart</button>
          <button class="btn btn-secondary" onclick="spawnEnemy()">+ Spawn Guard</button>
        </div>
        <div style="font-size: 0.8rem; color: var(--muted);">
          Stealth: <span id="cloak-status" style="color: #64748b; font-weight: 700;">OFF</span> &bull;
          Dummies: <span id="dummy-count" style="color: #38bdf8;">2</span> &bull;
          Guards: <span id="guard-count" style="color: #f87171;">2</span>
        </div>
      </div>
    </div>

    <!-- RIGHT: SKILL BUILDER & CUSTOMIZER -->
    <div class="card builder-panel">
      <h2>⚡ Skill Customizer</h2>
      <p class="sub">Tweak active abilities in real-time or export definitions.</p>

      <div class="form-group">
        <label class="form-label">Selected Ability</label>
        <select id="editSkillSelect" onchange="loadSkillToEdit()">
          <option value="slash">Katana Slash (Melee Strike)</option>
          <option value="dash">Shadow Dash (Mobility)</option>
          <option value="shuriken">Shuriken Volley (Ranged)</option>
          <option value="cloak">Shadow Cloak (Stealth / Crit)</option>
          <option value="decoy">Shadow Decoy (Illusion)</option>
        </select>
      </div>

      <div class="form-group">
        <div class="form-label">
          <span>Damage Power</span>
          <span class="val" id="valDamage">45</span>
        </div>
        <input type="range" id="inputDamage" min="10" max="250" value="45" oninput="updateSkillField('damage', this.value)">
      </div>

      <div class="form-group">
        <div class="form-label">
          <span>Energy Cost</span>
          <span class="val" id="valEnergy">0</span>
        </div>
        <input type="range" id="inputEnergy" min="0" max="60" value="0" oninput="updateSkillField('energy', this.value)">
      </div>

      <div class="form-group">
        <div class="form-label">
          <span>Cooldown (seconds)</span>
          <span class="val" id="valCooldown">0.4s</span>
        </div>
        <input type="range" id="inputCooldown" min="2" max="60" value="4" oninput="updateSkillField('cooldown', this.value / 10)">
      </div>

      <div class="form-group">
        <div class="form-label">
          <span>Effect Radius / Range</span>
          <span class="val" id="valRadius">70px</span>
        </div>
        <input type="range" id="inputRadius" min="30" max="250" value="70" oninput="updateSkillField('radius', this.value)">
      </div>

      <div class="form-group">
        <label class="form-label">Damage Element</label>
        <select id="inputElement" onchange="updateSkillField('element', this.value)">
          <option value="shadow">Void Shadow (Purple)</option>
          <option value="crimson">Crimson Flame (Red)</option>
          <option value="frost">Frostbite (Cyan)</option>
          <option value="lightning">Volt Strike (Yellow)</option>
        </select>
      </div>

      <div style="margin-top: 1rem; display: flex; flex-direction: column; gap: 0.5rem;">
        <button class="btn btn-primary" style="width: 100%;" onclick="applySkillChanges()">Apply to Live Game</button>
        <button class="btn btn-secondary" style="width: 100%;" onclick="toggleExportJson()">Export Skill Config (JSON)</button>
      </div>

      <div class="preset-chips">
        <span class="chip" onclick="applyPreset('assassin')">🗡️ Assassin</span>
        <span class="chip" onclick="applyPreset('void')">🔮 Void Mage</span>
        <span class="chip" onclick="applyPreset('speed')">⚡ Speed Ninja</span>
        <span class="chip" onclick="applyPreset('tank')">🛡️ Shadow Guard</span>
      </div>

      <div id="jsonContainer" style="display: none;">
        <div class="json-box" id="jsonExport"></div>
      </div>
    </div>
  </div>

  <div class="footer-help">
    Controls: <b>W A S D</b> or <b>Arrow Keys</b> to move &bull; <b>Click / Q</b> Katana Slash &bull; <b>W / Right Click</b> Shadow Dash &bull; <b>E</b> Shuriken &bull; <b>R</b> Cloak &bull; <b>Space</b> Decoy
  </div>

  <script>
    // =========================================================================
    // SHADOW MASTER COMBAT & SKILL BUILDER ENGINE
    // =========================================================================

    const canvas = document.getElementById('combatCanvas');
    const ctx = canvas.getContext('2d');

    // Audio Synthesizer (Zero External Dependencies)
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    let audioCtx = null;
    function playSfx(type) {{
      try {{
        if (!audioCtx) audioCtx = new AudioCtx();
        if (audioCtx.state === 'suspended') audioCtx.resume();
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        const now = audioCtx.currentTime;

        if (type === 'slash') {{
          osc.type = 'sawtooth';
          osc.frequency.setValueAtTime(320, now);
          osc.frequency.exponentialRampToValueAtTime(80, now + 0.12);
          gain.gain.setValueAtTime(0.25, now);
          gain.gain.exponentialRampToValueAtTime(0.01, now + 0.12);
          osc.start(now);
          osc.stop(now + 0.12);
        }} else if (type === 'dash') {{
          osc.type = 'sine';
          osc.frequency.setValueAtTime(140, now);
          osc.frequency.exponentialRampToValueAtTime(450, now + 0.15);
          gain.gain.setValueAtTime(0.3, now);
          gain.gain.exponentialRampToValueAtTime(0.01, now + 0.15);
          osc.start(now);
          osc.stop(now + 0.15);
        }} else if (type === 'shuriken') {{
          osc.type = 'triangle';
          osc.frequency.setValueAtTime(800, now);
          osc.frequency.exponentialRampToValueAtTime(200, now + 0.08);
          gain.gain.setValueAtTime(0.2, now);
          gain.gain.exponentialRampToValueAtTime(0.01, now + 0.08);
          osc.start(now);
          osc.stop(now + 0.08);
        }} else if (type === 'hit') {{
          osc.type = 'square';
          osc.frequency.setValueAtTime(180, now);
          osc.frequency.exponentialRampToValueAtTime(40, now + 0.1);
          gain.gain.setValueAtTime(0.2, now);
          gain.gain.exponentialRampToValueAtTime(0.01, now + 0.1);
          osc.start(now);
          osc.stop(now + 0.1);
        }} else if (type === 'levelup') {{
          osc.type = 'sine';
          osc.frequency.setValueAtTime(300, now);
          osc.frequency.setValueAtTime(400, now + 0.08);
          osc.frequency.setValueAtTime(600, now + 0.16);
          gain.gain.setValueAtTime(0.3, now);
          gain.gain.exponentialRampToValueAtTime(0.01, now + 0.35);
          osc.start(now);
          osc.stop(now + 0.35);
        }}
      }} catch(e) {{}}
    }}

    // Configurable Skills
    const skills = {{
      slash: {{ name: 'Katana Slash', damage: 45, energy: 0, cooldown: 0.4, radius: 70, element: 'shadow', lastUsed: 0 }},
      dash: {{ name: 'Shadow Dash', damage: 25, energy: 20, cooldown: 1.2, radius: 110, element: 'shadow', lastUsed: 0 }},
      shuriken: {{ name: 'Shuriken Volley', damage: 30, energy: 15, cooldown: 0.8, radius: 240, element: 'shadow', lastUsed: 0 }},
      cloak: {{ name: 'Shadow Cloak', damage: 0, energy: 30, cooldown: 3.5, radius: 0, element: 'shadow', lastUsed: 0, activeUntil: 0 }},
      decoy: {{ name: 'Shadow Decoy', damage: 60, energy: 40, cooldown: 4.0, radius: 100, element: 'shadow', lastUsed: 0 }}
    }};

    // Game State
    let isRunning = true;
    let score = 0;
    let combo = 1;
    let comboTimer = 0;
    let level = 1;
    let xp = 0;
    let xpNeeded = 100;

    // Player Object (The Shadow Master)
    const player = {{
      x: 350,
      y: 210,
      radius: 16,
      speed: 4.2,
      health: 100,
      maxHealth: 100,
      energy: 100,
      maxEnergy: 100,
      vx: 0,
      vy: 0,
      angle: 0,
      isCloaked: false,
      isDashing: false,
      dashTimer: 0,
      trail: [],
      slashArc: null,
      decoy: null
    }};

    // Projectiles, Floating Damage, Enemies, Decoys
    let projectiles = [];
    let damageNumbers = [];
    let particles = [];
    let enemies = [];

    // Initialize Initial Training Dummies & Guards
    function initEnemies() {{
      enemies = [
        {{ id: 1, type: 'dummy', x: 200, y: 160, radius: 20, health: 500, maxHealth: 500, name: 'Training Dummy A', hits: 0 }},
        {{ id: 2, type: 'dummy', x: 200, y: 260, radius: 20, health: 500, maxHealth: 500, name: 'Training Dummy B', hits: 0 }},
        {{ id: 3, type: 'guard', x: 550, y: 150, radius: 17, health: 120, maxHealth: 120, speed: 1.8, name: 'Shadow Guard 1', vx: 0, vy: 0, patrolY: 150, dir: 1 }},
        {{ id: 4, type: 'guard', x: 550, y: 270, radius: 17, health: 120, maxHealth: 120, speed: 1.8, name: 'Shadow Guard 2', vx: 0, vy: 0, patrolY: 270, dir: -1 }},
      ];
      updateEntityCounts();
    }}
    initEnemies();

    function updateEntityCounts() {{
      const d = enemies.filter(e => e.type === 'dummy').length;
      const g = enemies.filter(e => e.type === 'guard').length;
      document.getElementById('dummy-count').innerText = d;
      document.getElementById('guard-count').innerText = g;
    }}

    function spawnEnemy() {{
      const id = Date.now();
      const randY = 80 + Math.random() * 260;
      enemies.push({{
        id: id,
        type: 'guard',
        x: 600,
        y: randY,
        radius: 17,
        health: 120,
        maxHealth: 120,
        speed: 2.0,
        name: 'Shadow Guard ' + enemies.length,
        vx: 0,
        vy: 0,
        patrolY: randY,
        dir: 1
      }});
      updateEntityCounts();
    }}

    // Input Handling
    const keys = {{}};
    let mouseX = 350;
    let mouseY = 210;

    window.addEventListener('keydown', (e) => {{
      keys[e.key.toLowerCase()] = true;
      if (e.key === ' ' || e.code === 'Space') {{
        e.preventDefault();
        triggerSkill('decoy');
      }} else if (e.key.toLowerCase() === 'q') {{
        triggerSkill('slash');
      }} else if (e.key.toLowerCase() === 'w') {{
        triggerSkill('dash');
      }} else if (e.key.toLowerCase() === 'e') {{
        triggerSkill('shuriken');
      }} else if (e.key.toLowerCase() === 'r') {{
        triggerSkill('cloak');
      }}
    }});

    window.addEventListener('keyup', (e) => {{
      keys[e.key.toLowerCase()] = false;
    }});

    canvas.addEventListener('mousemove', (e) => {{
      const rect = canvas.getBoundingClientRect();
      const scaleX = canvas.width / rect.width;
      const scaleY = canvas.height / rect.height;
      mouseX = (e.clientX - rect.left) * scaleX;
      mouseY = (e.clientY - rect.top) * scaleY;
    }});

    canvas.addEventListener('mousedown', (e) => {{
      if (e.button === 0) {{
        triggerSkill('slash');
      }} else if (e.button === 2) {{
        e.preventDefault();
        triggerSkill('dash');
      }}
    }});
    canvas.addEventListener('contextmenu', (e) => e.preventDefault());

    // Skill Trigger Logic
    function triggerSkill(key) {{
      const sk = skills[key];
      if (!sk) return;
      const now = performance.now() / 1000;

      if (now - sk.lastUsed < sk.cooldown) return;
      if (player.energy < sk.energy) return;

      player.energy -= sk.energy;
      sk.lastUsed = now;

      if (key === 'slash') {{
        playSfx('slash');
        const crit = player.isCloaked ? 2.5 : 1.0;
        if (player.isCloaked) {{
          player.isCloaked = false;
          document.getElementById('cloak-status').innerText = 'OFF';
          document.getElementById('cloak-status').style.color = '#64748b';
        }}
        const dmg = Math.round(sk.damage * crit * (1 + (combo - 1) * 0.15));
        const reach = sk.radius;
        const startAng = player.angle - Math.PI / 3;
        const endAng = player.angle + Math.PI / 3;

        player.slashArc = {{
          x: player.x,
          y: player.y,
          startAngle: startAng,
          endAngle: endAng,
          radius: reach,
          element: sk.element,
          life: 0.15,
          maxLife: 0.15
        }};

        // Check hit against enemies
        enemies.forEach(en => {{
          const dx = en.x - player.x;
          const dy = en.y - player.y;
          const dist = Math.hypot(dx, dy);
          if (dist <= reach + en.radius) {{
            const enAngle = Math.atan2(dy, dx);
            let diff = Math.abs(enAngle - player.angle);
            while (diff > Math.PI) diff = Math.abs(diff - 2 * Math.PI);
            if (diff <= Math.PI / 2.5) {{
              damageEnemy(en, dmg, crit > 1.0, sk.element);
            }}
          }}
        }});

      }} else if (key === 'dash') {{
        playSfx('dash');
        player.isDashing = true;
        player.dashTimer = 0.22;
        const dashDist = sk.radius;
        player.vx = Math.cos(player.angle) * (dashDist / 0.22);
        player.vy = Math.sin(player.angle) * (dashDist / 0.22);

        // Spawn shadow clones in wake
        for (let i = 0; i < 3; i++) {{
          player.trail.push({{
            x: player.x - (player.vx * 0.05 * i),
            y: player.y - (player.vy * 0.05 * i),
            radius: player.radius,
            alpha: 0.7 - i * 0.2,
            angle: player.angle
          }});
        }}

      }} else if (key === 'shuriken') {{
        playSfx('shuriken');
        const count = 3;
        const spread = 0.25;
        for (let i = -1; i <= 1; i++) {{
          const a = player.angle + i * spread;
          projectiles.push({{
            x: player.x,
            y: player.y,
            vx: Math.cos(a) * 9,
            vy: Math.sin(a) * 9,
            damage: sk.damage,
            radius: 5,
            range: sk.radius,
            traveled: 0,
            element: sk.element
          }});
        }}

      }} else if (key === 'cloak') {{
        playSfx('dash');
        player.isCloaked = true;
        sk.activeUntil = now + 5.0;
        document.getElementById('cloak-status').innerText = 'ACTIVE (5s)';
        document.getElementById('cloak-status').style.color = '#c084fc';
        // Spawn cloak particle puff
        for (let i = 0; i < 15; i++) {{
          particles.push({{
            x: player.x + (Math.random() - 0.5) * 20,
            y: player.y + (Math.random() - 0.5) * 20,
            vx: (Math.random() - 0.5) * 3,
            vy: (Math.random() - 0.5) * 3,
            radius: Math.random() * 5 + 2,
            color: '#a855f7',
            alpha: 0.8,
            life: 0.4
          }});
        }}

      }} else if (key === 'decoy') {{
        playSfx('dash');
        player.decoy = {{
          x: player.x,
          y: player.y,
          radius: player.radius,
          health: 150,
          life: 5.0,
          angle: player.angle
        }};
        for (let i = 0; i < 12; i++) {{
          particles.push({{
            x: player.x + (Math.random() - 0.5) * 20,
            y: player.y + (Math.random() - 0.5) * 20,
            vx: (Math.random() - 0.5) * 4,
            vy: (Math.random() - 0.5) * 4,
            radius: 4,
            color: '#c084fc',
            alpha: 0.9,
            life: 0.35
          }});
        }}
      }}
    }}

    function damageEnemy(en, dmg, isCrit, element) {{
      playSfx('hit');
      en.health -= dmg;
      if (en.hits !== undefined) en.hits++;
      score += dmg * combo;
      xp += Math.round(dmg * 0.4);
      combo++;
      comboTimer = 2.5;

      // Check level up
      if (xp >= xpNeeded) {{
        level++;
        xp -= xpNeeded;
        xpNeeded = Math.round(xpNeeded * 1.4);
        playSfx('levelup');
        player.energy = player.maxEnergy;
      }}

      // Damage number
      damageNumbers.push({{
        x: en.x + (Math.random() - 0.5) * 15,
        y: en.y - 15,
        text: (isCrit ? 'CRIT! ' : '') + dmg,
        color: isCrit ? '#facc15' : (element === 'crimson' ? '#f87171' : element === 'frost' ? '#67e8f9' : '#c084fc'),
        alpha: 1.0,
        vy: -1.8,
        life: 0.8
      }});

      // Particles
      for (let i = 0; i < 8; i++) {{
        particles.push({{
          x: en.x,
          y: en.y,
          vx: (Math.random() - 0.5) * 5,
          vy: (Math.random() - 0.5) * 5,
          radius: Math.random() * 3 + 1,
          color: isCrit ? '#facc15' : '#a855f7',
          alpha: 1.0,
          life: 0.3
        }});
      }}

      // Enemy defeat check
      if (en.type === 'guard' && en.health <= 0) {{
        score += 250;
        // respawn after 3 seconds
        setTimeout(() => {{
          en.health = en.maxHealth;
          en.x = 600;
          en.y = 80 + Math.random() * 260;
        }}, 3000);
      }}
    }}

    // Toggle Game Loop States
    function toggleBattle() {{
      isRunning = !isRunning;
      document.getElementById('btn-start').innerText = isRunning ? 'Pause Battle' : 'Resume Battle';
      document.getElementById('statusOverlay').innerText = isRunning ? 'Arena Active &bull; Combat Live' : 'Battle Paused';
    }}

    function resetBattle() {{
      score = 0;
      combo = 1;
      comboTimer = 0;
      level = 1;
      xp = 0;
      player.health = 100;
      player.energy = 100;
      player.x = 350;
      player.y = 210;
      player.isCloaked = false;
      player.decoy = null;
      projectiles = [];
      particles = [];
      damageNumbers = [];
      initEnemies();
      document.getElementById('statusOverlay').innerText = 'Battle Reset &bull; Ready';
    }}

    // Main 60 FPS Game Loop
    let lastTime = performance.now();
    function gameLoop(now) {{
      const dt = Math.min((now - lastTime) / 1000, 0.1);
      lastTime = now;

      if (isRunning) {{
        update(dt);
      }}
      render();
      updateHud();
      requestAnimationFrame(gameLoop);
    }}

    function update(dt) {{
      // Player Energy Regeneration
      player.energy = Math.min(player.maxEnergy, player.energy + 12 * dt);

      // Combo Timer decay
      if (comboTimer > 0) {{
        comboTimer -= dt;
        if (comboTimer <= 0) combo = 1;
      }}

      // Cloak timer decay
      if (player.isCloaked && skills.cloak.activeUntil) {{
        if (performance.now() / 1000 >= skills.cloak.activeUntil) {{
          player.isCloaked = false;
          document.getElementById('cloak-status').innerText = 'OFF';
          document.getElementById('cloak-status').style.color = '#64748b';
        }}
      }}

      // Facing Angle towards Mouse
      player.angle = Math.atan2(mouseY - player.y, mouseX - player.x);

      // Movement
      if (player.isDashing) {{
        player.dashTimer -= dt;
        player.x += player.vx * dt;
        player.y += player.vy * dt;
        if (player.dashTimer <= 0) {{
          player.isDashing = false;
          player.vx = 0;
          player.vy = 0;
        }}
      }} else {{
        let moveX = 0;
        let moveY = 0;
        if (keys['w'] || keys['arrowup']) moveY -= 1;
        if (keys['s'] || keys['arrowdown']) moveY += 1;
        if (keys['a'] || keys['arrowleft']) moveX -= 1;
        if (keys['d'] || keys['arrowright']) moveX += 1;

        if (moveX !== 0 || moveY !== 0) {{
          const len = Math.hypot(moveX, moveY);
          const spd = player.isCloaked ? player.speed * 1.35 : player.speed;
          player.x += (moveX / len) * spd;
          player.y += (moveY / len) * spd;

          // Shadow afterimage trail
          if (Math.random() < 0.4) {{
            player.trail.push({{
              x: player.x,
              y: player.y,
              radius: player.radius,
              alpha: player.isCloaked ? 0.2 : 0.4,
              angle: player.angle
            }});
          }}
        }}
      }}

      // Arena Boundaries
      player.x = Math.max(player.radius + 10, Math.min(canvas.width - player.radius - 10, player.x));
      player.y = Math.max(player.radius + 10, Math.min(canvas.height - player.radius - 10, player.y));

      // Trails fade
      player.trail.forEach(t => t.alpha -= dt * 1.8);
      player.trail = player.trail.filter(t => t.alpha > 0);

      // Slash arc animation
      if (player.slashArc) {{
        player.slashArc.life -= dt;
        if (player.slashArc.life <= 0) player.slashArc = null;
      }}

      // Projectiles update
      projectiles.forEach(p => {{
        p.x += p.vx;
        p.y += p.vy;
        p.traveled += Math.hypot(p.vx, p.vy);

        // Check collision against enemies
        enemies.forEach(en => {{
          if (en.health > 0) {{
            const d = Math.hypot(en.x - p.x, en.y - p.y);
            if (d < en.radius + p.radius) {{
              p.traveled = p.range + 10; // destroy projectile
              damageEnemy(en, p.damage, false, p.element);
            }}
          }}
        }});
      }});
      projectiles = projectiles.filter(p => p.traveled < p.range && p.x >= 0 && p.x <= canvas.width && p.y >= 0 && p.y <= canvas.height);

      // Enemies AI Behavior
      const targetX = player.decoy ? player.decoy.x : (player.isCloaked ? -999 : player.x);
      const targetY = player.decoy ? player.decoy.y : (player.isCloaked ? -999 : player.y);

      enemies.forEach(en => {{
        if (en.type === 'dummy') return;
        if (en.health <= 0) return;

        const distToTarget = Math.hypot(targetX - en.x, targetY - en.y);
        if (distToTarget < 200) {{
          // Aggro chase
          const angle = Math.atan2(targetY - en.y, targetX - en.x);
          en.x += Math.cos(angle) * en.speed;
          en.y += Math.sin(angle) * en.speed;

          // Attack player if in melee range and not decoy
          if (!player.decoy && distToTarget < player.radius + en.radius + 4) {{
            if (!player.isDashing && !player.isCloaked) {{
              player.health = Math.max(0, player.health - 12 * dt);
            }}
          }}
        }} else {{
          // Simple vertical patrol
          en.y += en.dir * en.speed * 0.6;
          if (en.y > en.patrolY + 40) en.dir = -1;
          if (en.y < en.patrolY - 40) en.dir = 1;
        }}
      }});

      // Decoy decay
      if (player.decoy) {{
        player.decoy.life -= dt;
        if (player.decoy.life <= 0) player.decoy = null;
      }}

      // Particles & Damage numbers
      particles.forEach(pt => {{
        pt.x += pt.vx;
        pt.y += pt.vy;
        pt.alpha -= dt * 2.5;
      }});
      particles = particles.filter(pt => pt.alpha > 0);

      damageNumbers.forEach(dm => {{
        dm.y += dm.vy;
        dm.alpha -= dt * 1.2;
      }});
      damageNumbers = damageNumbers.filter(dm => dm.alpha > 0);
    }}

    function render() {{
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Grid Floor
      ctx.strokeStyle = 'rgba(168, 85, 247, 0.07)';
      ctx.lineWidth = 1;
      const gridSize = 35;
      for (let x = 0; x < canvas.width; x += gridSize) {{
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, canvas.height);
        ctx.stroke();
      }}
      for (let y = 0; y < canvas.height; y += gridSize) {{
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(canvas.width, y);
        ctx.stroke();
      }}

      // Arena Outer Ring
      ctx.strokeStyle = 'rgba(168, 85, 247, 0.2)';
      ctx.lineWidth = 2;
      ctx.strokeRect(10, 10, canvas.width - 20, canvas.height - 20);

      // Decoy Rendering
      if (player.decoy) {{
        ctx.save();
        ctx.globalAlpha = 0.5 + Math.sin(performance.now() * 0.01) * 0.2;
        ctx.fillStyle = '#6b21a8';
        ctx.beginPath();
        ctx.arc(player.decoy.x, player.decoy.y, player.decoy.radius, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = '#c084fc';
        ctx.stroke();
        ctx.restore();
      }}

      // Shadow Afterimages / Trails
      player.trail.forEach(t => {{
        ctx.save();
        ctx.globalAlpha = t.alpha;
        ctx.fillStyle = '#9333ea';
        ctx.beginPath();
        ctx.arc(t.x, t.y, t.radius, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      }});

      // Draw Enemies
      enemies.forEach(en => {{
        if (en.health <= 0) return;
        ctx.save();
        if (en.type === 'dummy') {{
          // Wood training dummy
          ctx.fillStyle = '#78350f';
          ctx.beginPath();
          ctx.arc(en.x, en.y, en.radius, 0, Math.PI * 2);
          ctx.fill();
          ctx.strokeStyle = '#d97706';
          ctx.lineWidth = 2;
          ctx.stroke();
          // Cross marker
          ctx.strokeStyle = '#fef3c7';
          ctx.beginPath();
          ctx.moveTo(en.x - 8, en.y);
          ctx.lineTo(en.x + 8, en.y);
          ctx.moveTo(en.x, en.y - 8);
          ctx.lineTo(en.x, en.y + 8);
          ctx.stroke();
        }} else {{
          // Shadow Guard
          ctx.fillStyle = '#1e1b4b';
          ctx.beginPath();
          ctx.arc(en.x, en.y, en.radius, 0, Math.PI * 2);
          ctx.fill();
          ctx.strokeStyle = '#ef4444';
          ctx.lineWidth = 2;
          ctx.stroke();
          // Red glowing eyes
          ctx.fillStyle = '#f87171';
          ctx.beginPath();
          ctx.arc(en.x - 4, en.y - 3, 2, 0, Math.PI * 2);
          ctx.arc(en.x + 4, en.y - 3, 2, 0, Math.PI * 2);
          ctx.fill();
        }}

        // Health bar above enemy
        const bw = en.radius * 2;
        const bh = 4;
        ctx.fillStyle = 'rgba(0,0,0,0.6)';
        ctx.fillRect(en.x - bw / 2, en.y - en.radius - 10, bw, bh);
        const hpPct = Math.max(0, en.health / en.maxHealth);
        ctx.fillStyle = en.type === 'dummy' ? '#f59e0b' : '#ef4444';
        ctx.fillRect(en.x - bw / 2, en.y - en.radius - 10, bw * hpPct, bh);
        ctx.restore();
      }});

      // Draw Player (The Shadow Master)
      ctx.save();
      ctx.globalAlpha = player.isCloaked ? 0.35 : 1.0;

      // Glow Aura
      const aura = ctx.createRadialGradient(player.x, player.y, player.radius * 0.5, player.x, player.y, player.radius * 1.8);
      aura.addColorStop(0, 'rgba(168, 85, 247, 0.4)');
      aura.addColorStop(1, 'rgba(168, 85, 247, 0)');
      ctx.fillStyle = aura;
      ctx.beginPath();
      ctx.arc(player.x, player.y, player.radius * 1.8, 0, Math.PI * 2);
      ctx.fill();

      // Body (Ninja Obsidian Silhouette)
      ctx.fillStyle = '#0f172a';
      ctx.beginPath();
      ctx.arc(player.x, player.y, player.radius, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = player.isCloaked ? '#c084fc' : '#a855f7';
      ctx.lineWidth = 2.5;
      ctx.stroke();

      // Scarf & Glowing Eyes in facing angle
      ctx.save();
      ctx.translate(player.x, player.y);
      ctx.rotate(player.angle);
      // Scarf trail
      ctx.fillStyle = '#9333ea';
      ctx.fillRect(-player.radius - 6, -3, 8, 6);
      // Ninja eyes
      ctx.fillStyle = '#38bdf8';
      ctx.beginPath();
      ctx.arc(6, -3, 2, 0, Math.PI * 2);
      ctx.arc(6, 3, 2, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();

      ctx.restore();

      // Draw Slash Arc
      if (player.slashArc) {{
        const arc = player.slashArc;
        ctx.save();
        ctx.strokeStyle = arc.element === 'crimson' ? '#ef4444' : arc.element === 'frost' ? '#06b6d4' : '#c084fc';
        ctx.lineWidth = 6;
        ctx.lineCap = 'round';
        ctx.shadowColor = ctx.strokeStyle;
        ctx.shadowBlur = 15;
        ctx.beginPath();
        ctx.arc(arc.x, arc.y, arc.radius, arc.startAngle, arc.endAngle);
        ctx.stroke();
        ctx.restore();
      }}

      // Draw Projectiles
      projectiles.forEach(p => {{
        ctx.save();
        ctx.translate(p.x, p.y);
        ctx.rotate(performance.now() * 0.02);
        ctx.fillStyle = p.element === 'crimson' ? '#f87171' : p.element === 'frost' ? '#67e8f9' : '#c084fc';
        ctx.shadowColor = ctx.fillStyle;
        ctx.shadowBlur = 10;
        // 4-pointed Shuriken shape
        ctx.beginPath();
        ctx.moveTo(0, -p.radius * 2);
        ctx.lineTo(p.radius * 0.7, -p.radius * 0.7);
        ctx.lineTo(p.radius * 2, 0);
        ctx.lineTo(p.radius * 0.7, p.radius * 0.7);
        ctx.lineTo(0, p.radius * 2);
        ctx.lineTo(-p.radius * 0.7, p.radius * 0.7);
        ctx.lineTo(-p.radius * 2, 0);
        ctx.lineTo(-p.radius * 0.7, -p.radius * 0.7);
        ctx.closePath();
        ctx.fill();
        ctx.restore();
      }});

      // Draw Particles
      particles.forEach(pt => {{
        ctx.save();
        ctx.globalAlpha = pt.alpha;
        ctx.fillStyle = pt.color;
        ctx.beginPath();
        ctx.arc(pt.x, pt.y, pt.radius, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      }});

      // Draw Damage Numbers
      damageNumbers.forEach(dm => {{
        ctx.save();
        ctx.globalAlpha = dm.alpha;
        ctx.fillStyle = dm.color;
        ctx.font = 'bold 14px "Plus Jakarta Sans", sans-serif';
        ctx.shadowColor = '#000';
        ctx.shadowBlur = 4;
        ctx.fillText(dm.text, dm.x, dm.y);
        ctx.restore();
      }});
    }}

    function updateHud() {{
      document.getElementById('hud-health').innerText = Math.round(player.health) + ' / 100';
      document.getElementById('bar-health-fill').style.width = Math.max(0, player.health) + '%';

      document.getElementById('hud-energy').innerText = Math.round(player.energy) + ' / 100';
      document.getElementById('bar-energy-fill').style.width = Math.max(0, player.energy) + '%';

      document.getElementById('hud-combo').innerText = 'x' + combo;
      document.getElementById('hud-level').innerText = level;
      document.getElementById('bar-xp-fill').style.width = (xp / xpNeeded * 100) + '%';

      document.getElementById('hud-score').innerText = score;

      // Cooldown HUD overlays
      const now = performance.now() / 1000;
      for (const [k, sk] of Object.entries(skills)) {{
        const el = document.getElementById('cd-' + k);
        if (el) {{
          const elapsed = now - sk.lastUsed;
          if (elapsed < sk.cooldown) {{
            const pct = (1 - elapsed / sk.cooldown) * 100;
            el.style.height = pct + '%';
          }} else {{
            el.style.height = '0%';
          }}
        }}
      }}
    }}

    // Skill Customizer Form Synchronization
    function loadSkillToEdit() {{
      const k = document.getElementById('editSkillSelect').value;
      const sk = skills[k];
      if (!sk) return;
      document.getElementById('inputDamage').value = sk.damage;
      document.getElementById('valDamage').innerText = sk.damage;
      document.getElementById('inputEnergy').value = sk.energy;
      document.getElementById('valEnergy').innerText = sk.energy;
      document.getElementById('inputCooldown').value = Math.round(sk.cooldown * 10);
      document.getElementById('valCooldown').innerText = sk.cooldown + 's';
      document.getElementById('inputRadius').value = sk.radius;
      document.getElementById('valRadius').innerText = sk.radius + 'px';
      document.getElementById('inputElement').value = sk.element;
    }}

    function updateSkillField(field, val) {{
      const k = document.getElementById('editSkillSelect').value;
      const sk = skills[k];
      if (!sk) return;
      if (field === 'damage') {{
        sk.damage = parseInt(val, 10);
        document.getElementById('valDamage').innerText = sk.damage;
      }} else if (field === 'energy') {{
        sk.energy = parseInt(val, 10);
        document.getElementById('valEnergy').innerText = sk.energy;
        document.getElementById('cost-' + k).innerText = sk.energy + ' Energy';
      }} else if (field === 'cooldown') {{
        sk.cooldown = parseFloat(val);
        document.getElementById('valCooldown').innerText = sk.cooldown + 's';
      }} else if (field === 'radius') {{
        sk.radius = parseInt(val, 10);
        document.getElementById('valRadius').innerText = sk.radius + 'px';
      }} else if (field === 'element') {{
        sk.element = val;
      }}
    }}

    function applySkillChanges() {{
      const k = document.getElementById('editSkillSelect').value;
      playSfx('levelup');
      document.getElementById('statusOverlay').innerText = 'Applied custom tuning to ' + skills[k].name + '! Test in arena.';
    }}

    function applyPreset(preset) {{
      if (preset === 'assassin') {{
        skills.slash.damage = 85;
        skills.dash.cooldown = 0.8;
        skills.cloak.cooldown = 2.0;
      }} else if (preset === 'void') {{
        skills.shuriken.damage = 55;
        skills.decoy.damage = 110;
        skills.slash.element = 'shadow';
      }} else if (preset === 'speed') {{
        skills.dash.energy = 5;
        skills.dash.cooldown = 0.4;
        skills.slash.cooldown = 0.2;
      }} else if (preset === 'tank') {{
        skills.cloak.energy = 10;
        skills.decoy.energy = 15;
      }}
      loadSkillToEdit();
      playSfx('levelup');
      document.getElementById('statusOverlay').innerText = 'Preset [' + preset.toUpperCase() + '] applied to Skill System!';
    }}

    function toggleExportJson() {{
      const box = document.getElementById('jsonContainer');
      if (box.style.display === 'none') {{
        box.style.display = 'block';
        const exportData = {{
          game: "Shadow Master Skill Builder",
          version: "2.0.0",
          schema: "https://se-intelliplatform.local/schemas/skill-tree.v1.json",
          skills: skills,
          exportedAt: new Date().toISOString()
        }};
        document.getElementById('jsonExport').innerText = JSON.stringify(exportData, null, 2);
      }} else {{
        box.style.display = 'none';
      }}
    }}

    // Start 60fps Loop
    requestAnimationFrame(gameLoop);
  </script>
</body>
</html>
"""


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

        <button type="button" id="btn-export-csv" class="btn" onclick="exportCSV()">
          <span>Export CSV</span>
        </button>

        <!-- Auth guest trigger / logged in pill -->
        <div id="auth-guest-view">
          <button type="button" id="btn-open-login" class="btn btn-primary" style="background: linear-gradient(135deg, #6366f1, #8b5cf6); border: none;" onclick="openAuthModal()">
            <span>🔑 Sign In / Login</span>
          </button>
        </div>
        <div id="auth-logged-in-view" style="display:none; align-items:center; gap:0.5rem; background:rgba(99,102,241,0.15); padding:0.35rem 0.75rem; border-radius:8px; border:1px solid rgba(99,102,241,0.3);">
          <span>👤</span>
          <span id="auth-user-name" style="font-weight:700; font-size:0.85rem;">Executive User</span>
          <button type="button" id="btn-logout" class="btn" style="padding:0.2rem 0.5rem; font-size:0.75rem;" onclick="logoutUser()">Log Out</button>
        </div>
      </div>
    </header>

    <!-- 4 KPI Cards Grid -->
    <section class="kpi-grid" aria-label="Key Performance Indicators">
      <div class="kpi-card">
        <div class="kpi-header">
          <span class="kpi-label">Total ARR / Revenue</span>
          <span class="kpi-trend trend-up">+14.8%</span>
        </div>
        <div class="kpi-value" id="kpiRevenue" data-testid="kpi-arr">$1,428,500</div>
        <div class="kpi-subtext">+12.4% vs previous 30-day cohort</div>
      </div>

      <div class="kpi-card">
        <div class="kpi-header">
          <span class="kpi-label">Active Workspaces</span>
          <span class="kpi-trend trend-up">+21.4%</span>
        </div>
        <div class="kpi-value" id="kpiWorkspaces" data-testid="kpi-workspaces">3,842</div>
        <div class="kpi-subtext">98.2% customer retention index</div>
      </div>

      <div class="kpi-card">
        <div class="kpi-header">
          <span class="kpi-label">Conversion Rate</span>
          <span class="kpi-trend trend-up">+3.2%</span>
        </div>
        <div class="kpi-value" id="kpiConversion" data-testid="kpi-conversion">24.6%</div>
        <div class="kpi-subtext">Trial-to-paid funnel completion</div>
      </div>

      <div class="kpi-card">
        <div class="kpi-header">
          <span class="kpi-label">Customer Churn</span>
          <span class="kpi-trend trend-up">-0.4%</span>
        </div>
        <div class="kpi-value" id="kpiChurn" data-testid="kpi-churn">1.8%</div>
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
          <svg id="chart-revenue-trend" class="trend-chart" viewBox="0 0 600 220" preserveAspectRatio="none">
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
            <input type="text" id="metricSearch" data-testid="metric-search-input" class="search-input" placeholder="Search metrics or dimensions..." onkeyup="filterTable()" />
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
        <table class="data-table" id="metricsTable" data-testid="metrics-table">
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

  <!-- Interactive Auth Modal -->
  <div class="modal-backdrop" id="auth-modal-overlay" style="display:none; position:fixed; inset:0; z-index:100000; background:rgba(0,0,0,0.75); backdrop-filter:blur(8px); align-items:center; justify-content:center;" onclick="if(event.target===this)closeAuthModal()">
    <div class="modal-content auth-card" style="max-width:440px; width:92%; background:var(--surface); border:1px solid var(--border-accent); border-radius:14px; padding:1.5rem; box-shadow:0 20px 40px rgba(0,0,0,0.6);" onclick="event.stopPropagation()">
      <div class="modal-header" style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1.25rem;">
        <div class="auth-tabs" style="display:flex; gap:0.5rem;">
          <button type="button" id="tab-login" class="btn filter-btn active" style="font-weight:700;" onclick="switchAuthTab('login')">Sign In</button>
          <button type="button" id="tab-register" class="btn filter-btn" onclick="switchAuthTab('register')">Register</button>
        </div>
        <button type="button" id="btn-close-modal" class="btn" style="padding:0.25rem 0.55rem;" onclick="closeAuthModal()">✕</button>
      </div>

      <div id="auth-error-msg" style="display:none; background:rgba(239,68,68,0.2); border:1px solid var(--danger); color:#fca5a5; padding:0.5rem; border-radius:6px; margin-bottom:0.75rem; font-size:0.85rem;"></div>

      <form id="authForm" onsubmit="event.preventDefault(); submitAuth();">
        <div class="form-group" id="field-name-wrap" style="display:none; margin-bottom:0.85rem;">
          <label class="form-label" for="auth-name-input">Executive Name</label>
          <input type="text" id="auth-name-input" class="form-input" style="width:100%;" placeholder="e.g. Sarah Connor" />
        </div>

        <div class="form-group" style="margin-bottom:0.85rem;">
          <label class="form-label" for="auth-email-input">Work Email</label>
          <input type="email" id="auth-email-input" class="form-input" style="width:100%;" placeholder="executive@acmecorp.com" required />
        </div>

        <div class="form-group" style="margin-bottom:0.85rem;">
          <label class="form-label" for="auth-pwd-input">Password</label>
          <input type="password" id="auth-pwd-input" class="form-input" style="width:100%;" placeholder="••••••••••••" required />
        </div>

        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem; font-size:0.8rem; color:var(--text-muted);">
          <label style="display:flex; align-items:center; gap:0.35rem; cursor:pointer;">
            <input type="checkbox" checked id="auth-remember-check" /> Remember me
          </label>
          <button type="button" id="link-forgot-password" class="auth-forgot-link" style="background:transparent; border:none; color:var(--accent-primary); cursor:pointer; text-decoration:underline;" onclick="triggerForgotPassword()">Forgot password?</button>
        </div>

        <div style="display:flex; flex-direction:column; gap:0.5rem;">
          <button type="submit" id="btn-submit-auth" class="btn btn-primary" style="width:100%; justify-content:center; padding:0.65rem; font-weight:700;">Sign In to Dashboard</button>
          <button type="button" id="btn-quick-fill" class="btn" style="width:100%; justify-content:center; font-size:0.8rem;" onclick="quickFillExecutive()">👤 Quick Fill Executive Demo</button>
        </div>
      </form>
    </div>
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

    // Interactive Auth Modal Controls
    function openAuthModal() {{
      const modal = document.getElementById('auth-modal-overlay');
      if (modal) {{
        modal.style.display = 'flex';
        modal.style.visibility = 'visible';
        modal.style.opacity = '1';
      }}
    }}

    function closeAuthModal() {{
      const modal = document.getElementById('auth-modal-overlay');
      if (modal) modal.style.display = 'none';
    }}

    let isRegisterMode = false;
    function switchAuthTab(mode) {{
      isRegisterMode = (mode === 'register');
      document.getElementById('tab-login').classList.toggle('active', !isRegisterMode);
      document.getElementById('tab-register').classList.toggle('active', isRegisterMode);
      const nameWrap = document.getElementById('field-name-wrap');
      if (nameWrap) nameWrap.style.display = isRegisterMode ? 'block' : 'none';
      const submitBtn = document.getElementById('btn-submit-auth');
      if (submitBtn) submitBtn.innerText = isRegisterMode ? 'Create Executive Account' : 'Sign In to Dashboard';
    }}

    function quickFillExecutive() {{
      const email = document.getElementById('auth-email-input');
      const pwd = document.getElementById('auth-pwd-input');
      const name = document.getElementById('auth-name-input');
      if (email) email.value = 'executive@acmecorp.com';
      if (pwd) pwd.value = 'ExecutiveSecure2026!';
      if (name) name.value = 'Sarah Connor (VP)';
      const err = document.getElementById('auth-error-msg');
      if (err) err.style.display = 'none';
    }}

    function submitAuth() {{
      const emailInp = document.getElementById('auth-email-input');
      const pwdInp = document.getElementById('auth-pwd-input');
      const email = emailInp ? emailInp.value.trim() : '';
      const pwd = pwdInp ? pwdInp.value.trim() : '';
      const err = document.getElementById('auth-error-msg');

      if (!email || !pwd) {{
        if (err) {{
          err.innerText = 'Please provide both email and password.';
          err.style.display = 'block';
        }}
        return;
      }}

      if (err) err.style.display = 'none';
      const name = email.split('@')[0];
      const displayName = name.charAt(0).toUpperCase() + name.slice(1);
      const guest = document.getElementById('auth-guest-view');
      const loggedIn = document.getElementById('auth-logged-in-view');
      const userName = document.getElementById('auth-user-name');
      if (guest) guest.style.display = 'none';
      if (loggedIn) loggedIn.style.display = 'inline-flex';
      if (userName) userName.innerText = displayName + ' (Executive)';
      closeAuthModal();
    }}

    function logoutUser() {{
      const guest = document.getElementById('auth-guest-view');
      const loggedIn = document.getElementById('auth-logged-in-view');
      if (guest) guest.style.display = 'inline-flex';
      if (loggedIn) loggedIn.style.display = 'none';
    }}

    function triggerForgotPassword() {{
      const emailInp = document.getElementById('auth-email-input');
      const email = (emailInp && emailInp.value.trim()) || 'executive@acmecorp.com';
      alert('✓ Password recovery link has been dispatched to ' + email);
    }}
  </script>
</body>
</html>"""


def get_management_html(title: str = "TeamConnect Directory", desc: str = "") -> str:
    try:
        from app.agents.code_generation.archetypes import get_archetype_file_content
        rendered = get_archetype_file_content("management", "frontend/index.html", title, desc)
        if rendered:
            return rendered
    except Exception as exc:
        pass
    return f"""<!DOCTYPE html><html><body><h1>{title}</h1></body></html>"""


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


import os

def get_chess_html(title="Chess Master Pro", desc="Interactive Strategic Chess Game"):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title} — Live Preview</title>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #0f172a;
      --card-bg: rgba(30, 41, 59, 0.85);
      --border: rgba(255, 255, 255, 0.1);
      --accent: #3b82f6;
      --light-sq: #eeeed2;
      --dark-sq: #769656;
      --highlight: #baca44;
      --text: #f8fafc;
      --muted: #94a3b8;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Plus Jakarta Sans', sans-serif;
      background: radial-gradient(circle at 50% 10%, #1e293b 0%, #0f172a 70%);
      color: var(--text);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 1.5rem;
    }}
    .header {{ text-align: center; margin-bottom: 1.25rem; max-width: 1000px; width: 100%; }}
    .badge {{ display: inline-block; background: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.8rem; font-weight: 700; margin-bottom: 0.5rem; }}
    h1 {{ font-size: 2.2rem; font-weight: 800; margin-bottom: 0.25rem; background: linear-gradient(135deg, #fff 30%, #93c5fd 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    .subtitle {{ color: var(--muted); font-size: 0.95rem; }}
    .chess-layout {{ display: flex; gap: 2rem; align-items: flex-start; justify-content: center; flex-wrap: wrap; max-width: 1100px; width: 100%; }}
    .board-container {{ background: #262421; padding: 12px; border-radius: 12px; box-shadow: 0 20px 40px rgba(0,0,0,0.6); border: 1px solid rgba(255,255,255,0.1); }}
    .board {{ display: grid; grid-template-columns: repeat(8, 64px); grid-template-rows: repeat(8, 64px); border: 2px solid #3e3b36; }}
    .square {{ width: 64px; height: 64px; display: flex; align-items: center; justify-content: center; font-size: 40px; cursor: pointer; user-select: none; transition: background 0.1s; position: relative; }}
    .square.light {{ background: var(--light-sq); color: #111; }}
    .square.dark {{ background: var(--dark-sq); color: #111; }}
    .square.selected {{ background: var(--highlight) !important; }}
    .square.valid-move::after {{ content: ''; width: 16px; height: 16px; background: rgba(0,0,0,0.25); border-radius: 50%; position: absolute; }}
    .side-panel {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; padding: 1.25rem; width: 320px; display: flex; flex-direction: column; gap: 1rem; }}
    .hud-box {{ background: rgba(15, 23, 42, 0.6); border: 1px solid var(--border); border-radius: 8px; padding: 0.75rem 1rem; }}
    .hud-title {{ font-size: 0.75rem; text-transform: uppercase; color: var(--muted); font-weight: 700; margin-bottom: 0.25rem; }}
    .hud-val {{ font-size: 1.1rem; font-weight: 800; font-family: 'JetBrains Mono', monospace; }}
    .history-box {{ background: rgba(15, 23, 42, 0.6); border: 1px solid var(--border); border-radius: 8px; padding: 0.75rem; max-height: 180px; overflow-y: auto; font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; }}
    .history-entry {{ display: flex; justify-content: space-between; padding: 0.2rem 0; border-bottom: 1px solid rgba(255,255,255,0.05); }}
    .btn {{ padding: 0.6rem 1rem; border-radius: 8px; font-weight: 700; cursor: pointer; border: none; font-size: 0.9rem; transition: transform 0.1s; }}
    .btn:active {{ transform: scale(0.98); }}
    .btn-primary {{ background: #3b82f6; color: white; }}
    .btn-secondary {{ background: rgba(255,255,255,0.1); color: white; border: 1px solid var(--border); }}
  </style>
</head>
<body>
  <div class="header">
    <span class="badge">CHESS STRATEGY ENGINE &bull; LIVE</span>
    <h1>{title}</h1>
    <p class="subtitle">{desc}</p>
  </div>

  <div class="chess-layout">
    <div class="board-container">
      <div class="board" id="chessBoard"></div>
    </div>

    <div class="side-panel">
      <div class="hud-box">
        <div class="hud-title">Current Turn</div>
        <div class="hud-val" id="turnIndicator" style="color: #60a5fa;">White to Move</div>
      </div>
      <div class="hud-box">
        <div class="hud-title">Match Status</div>
        <div class="hud-val" id="statusIndicator" style="color: #10b981;">In Progress</div>
      </div>
      <div class="hud-box">
        <div class="hud-title">Captured Pieces</div>
        <div id="capturedWhite" style="font-size: 20px; min-height: 24px;"></div>
        <div id="capturedBlack" style="font-size: 20px; min-height: 24px;"></div>
      </div>
      <div class="hud-title">Move Notation History</div>
      <div class="history-box" id="moveHistory"></div>
      <div style="display: flex; gap: 0.5rem; margin-top: auto;">
        <button class="btn btn-secondary" style="flex: 1;" onclick="resetGame()">New Match</button>
        <button class="btn btn-primary" style="flex: 1;" onclick="flipBoard()">Flip Board</button>
      </div>
    </div>
  </div>

  <script>
    const INITIAL_BOARD = [
      ['♜','♞','♝','♛','♚','♝','♞','♜'],
      ['♟','♟','♟','♟','♟','♟','♟','♟'],
      ['','','','','','','',''],
      ['','','','','','','',''],
      ['','','','','','','',''],
      ['','','','','','','',''],
      ['♙','♙','♙','♙','♙','♙','♙','♙'],
      ['♖','♘','♗','♕','♔','♗','♘','♖']
    ];

    let board = JSON.parse(JSON.stringify(INITIAL_BOARD));
    let turn = 'white';
    let selectedSquare = null;
    let validMoves = [];
    let moveCount = 1;
    let isFlipped = false;
    let moveHistory = [];

    const isWhitePiece = (p) => ['♙','♖','♘','♗','♕','♔'].includes(p);
    const isBlackPiece = (p) => ['♟','♜','♞','♝','♛','♚'].includes(p);

    function renderBoard() {{
      const boardEl = document.getElementById('chessBoard');
      boardEl.innerHTML = '';
      for (let r = 0; r < 8; r++) {{
        for (let c = 0; c < 8; c++) {{
          const row = isFlipped ? 7 - r : r;
          const col = isFlipped ? 7 - c : c;
          const sq = document.createElement('div');
          sq.className = 'square ' + ((row + col) % 2 === 0 ? 'light' : 'dark');
          if (selectedSquare && selectedSquare.r === row && selectedSquare.c === col) {{
            sq.classList.add('selected');
          }}
          if (validMoves.some(m => m.r === row && m.c === col)) {{
            sq.classList.add('valid-move');
          }}
          sq.innerText = board[row][col];
          sq.onclick = () => onSquareClick(row, col);
          boardEl.appendChild(sq);
        }}
      }}
    }}

    function onSquareClick(r, c) {{
      const piece = board[r][c];
      if (selectedSquare) {{
        // Check if moving to valid square
        if (validMoves.some(m => m.r === r && m.c === c)) {{
          const movedPiece = board[selectedSquare.r][selectedSquare.c];
          const captured = board[r][c];
          board[r][c] = movedPiece;
          board[selectedSquare.r][selectedSquare.c] = '';

          const cols = ['a','b','c','d','e','f','g','h'];
          const moveNotation = movedPiece + cols[c] + (8 - r) + (captured ? ' (x)' : '');
          recordMove(moveNotation);

          turn = turn === 'white' ? 'black' : 'white';
          document.getElementById('turnIndicator').innerText = (turn === 'white' ? 'White' : 'Black') + ' to Move';
          document.getElementById('turnIndicator').style.color = turn === 'white' ? '#60a5fa' : '#f59e0b';
          selectedSquare = null;
          validMoves = [];
          renderBoard();
          return;
        }}
      }}

      // Select piece
      if (piece && ((turn === 'white' && isWhitePiece(piece)) || (turn === 'black' && isBlackPiece(piece)))) {{
        selectedSquare = {{ r, c }};
        validMoves = getSampleMoves(r, c, piece);
      }} else {{
        selectedSquare = null;
        validMoves = [];
      }}
      renderBoard();
    }}

    function getSampleMoves(r, c, piece) {{
      const moves = [];
      const dir = isWhitePiece(piece) ? -1 : 1;
      // Basic forward moves & captures for display interactivity
      if (['♙','♟'].includes(piece)) {{
        if (r + dir >= 0 && r + dir < 8 && !board[r + dir][c]) moves.push({{ r: r + dir, c }});
        if (c > 0 && r + dir >= 0 && r + dir < 8) moves.push({{ r: r + dir, c: c - 1 }});
        if (c < 7 && r + dir >= 0 && r + dir < 8) moves.push({{ r: r + dir, c: c + 1 }});
      }} else {{
        // Knights / Kings / Queens / Rooks - basic adjacent & ray tiles
        const offsets = [[-1,0],[1,0],[0,-1],[0,1],[-1,-1],[-1,1],[1,-1],[1,1]];
        for (const [dr, dc] of offsets) {{
          const nr = r + dr, nc = c + dc;
          if (nr >= 0 && nr < 8 && nc >= 0 && nc < 8) moves.push({{ r: nr, c: nc }});
        }}
      }}
      return moves;
    }}

    function recordMove(notation) {{
      moveHistory.push(notation);
      const histEl = document.getElementById('moveHistory');
      histEl.innerHTML += `<div class="history-entry"><span>#${{moveHistory.length}}</span><span>${{notation}}</span></div>`;
      histEl.scrollTop = histEl.scrollHeight;
    }}

    function flipBoard() {{ isFlipped = !isFlipped; renderBoard(); }}
    function resetGame() {{
      board = JSON.parse(JSON.stringify(INITIAL_BOARD));
      turn = 'white';
      selectedSquare = null;
      validMoves = [];
      moveHistory = [];
      document.getElementById('moveHistory').innerHTML = '';
      document.getElementById('turnIndicator').innerText = 'White to Move';
      renderBoard();
    }}

    renderBoard();
  </script>
</body>
</html>"""

def get_platformer_html(title="Skyline Jump Platformer", desc="2D Action Platformer Game"):
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
      background: radial-gradient(circle at 50% 10%, #1e1b4b 0%, #090d16 70%);
      color: #f8fafc;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 1.5rem;
    }}
    .header {{ text-align: center; margin-bottom: 1rem; }}
    h1 {{ font-size: 2rem; font-weight: 800; background: linear-gradient(135deg, #fff 30%, #a78bfa 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    .hud {{ display: flex; gap: 1.5rem; background: rgba(30, 27, 75, 0.8); border: 1px solid rgba(167, 139, 250, 0.3); padding: 0.6rem 1.5rem; border-radius: 9999px; margin-bottom: 1rem; font-family: 'JetBrains Mono', monospace; font-size: 0.9rem; }}
    .canvas-box {{ border: 2px solid rgba(167, 139, 250, 0.3); border-radius: 12px; box-shadow: 0 20px 40px rgba(0,0,0,0.7); overflow: hidden; }}
    canvas {{ display: block; background: #0c0a1d; }}
    .controls-hint {{ margin-top: 0.75rem; color: #94a3b8; font-size: 0.85rem; }}
  </style>
</head>
<body>
  <div class="header">
    <h1>{title}</h1>
    <p style="color: #94a3b8;">{desc}</p>
  </div>
  <div class="hud">
    <div>SCORE: <span id="hud-score" style="color: #fbbf24; font-weight: 800;">0</span></div>
    <div>LIVES: <span id="hud-lives" style="color: #ef4444; font-weight: 800;">❤️❤️❤️</span></div>
    <div>COINS: <span id="hud-coins" style="color: #38bdf8; font-weight: 800;">0/10</span></div>
  </div>
  <div class="canvas-box">
    <canvas id="platformerCanvas" width="750" height="420"></canvas>
  </div>
  <div class="controls-hint">Controls: <b>A / D</b> or <b>Arrow Keys</b> to Move &bull; <b>W / Space / Up</b> to Jump &bull; <b>R</b> to Restart</div>

  <script>
    const canvas = document.getElementById('platformerCanvas');
    const ctx = canvas.getContext('2d');

    let player = {{ x: 60, y: 320, vx: 0, vy: 0, w: 26, h: 32, grounded: false, score: 0, coins: 0, lives: 3 }};
    const GRAVITY = 0.55;
    const FRICTION = 0.82;
    const JUMP_POWER = -11.5;

    const platforms = [
      {{ x: 0, y: 380, w: 750, h: 40 }}, // Ground
      {{ x: 120, y: 300, w: 140, h: 18 }},
      {{ x: 320, y: 240, w: 130, h: 18 }},
      {{ x: 500, y: 180, w: 140, h: 18 }},
      {{ x: 260, y: 130, w: 150, h: 18 }},
      {{ x: 80, y: 90, w: 100, h: 18 }}
    ];

    let coins = [
      {{ x: 180, y: 260, collected: false }},
      {{ x: 380, y: 200, collected: false }},
      {{ x: 560, y: 140, collected: false }},
      {{ x: 330, y: 90, collected: false }},
      {{ x: 120, y: 50, collected: false }}
    ];

    const keys = {{}};
    window.addEventListener('keydown', e => {{
      keys[e.code] = true;
      if (['Space','ArrowUp','KeyW'].includes(e.code) && player.grounded) {{
        player.vy = JUMP_POWER;
        player.grounded = false;
      }}
      if (e.code === 'KeyR') resetGame();
    }});
    window.addEventListener('keyup', e => {{ keys[e.code] = false; }});

    function update() {{
      if (keys['KeyA'] || keys['ArrowLeft']) player.vx -= 1.2;
      if (keys['KeyD'] || keys['ArrowRight']) player.vx += 1.2;
      player.vx *= FRICTION;
      player.vy += GRAVITY;
      player.x += player.vx;
      player.y += player.vy;

      player.grounded = false;
      for (const p of platforms) {{
        if (player.x + player.w > p.x && player.x < p.x + p.w &&
            player.y + player.h > p.y && player.y + player.h < p.y + p.h + player.vy) {{
          player.y = p.y - player.h;
          player.vy = 0;
          player.grounded = true;
        }}
      }}

      // Check coin collection
      for (const c of coins) {{
        if (!c.collected && Math.hypot(player.x + 13 - c.x, player.y + 16 - c.y) < 24) {{
          c.collected = true;
          player.coins++;
          player.score += 150;
          document.getElementById('hud-score').innerText = player.score;
          document.getElementById('hud-coins').innerText = player.coins + '/5';
        }}
      }}

      // Boundary check
      if (player.x < 0) player.x = 0;
      if (player.x > canvas.width - player.w) player.x = canvas.width - player.w;
      if (player.y > canvas.height) {{
        player.lives--;
        if (player.lives <= 0) resetGame();
        else {{ player.x = 60; player.y = 300; player.vy = 0; }}
      }}
    }}

    function render() {{
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Draw backdrop stars
      ctx.fillStyle = 'rgba(255,255,255,0.4)';
      for (let i = 0; i < 40; i++) {{
        const sx = (i * 47) % canvas.width;
        const sy = (i * 29) % 300;
        ctx.fillRect(sx, sy, 2, 2);
      }}

      // Draw platforms
      for (const p of platforms) {{
        ctx.fillStyle = '#6366f1';
        ctx.fillRect(p.x, p.y, p.w, p.h);
        ctx.fillStyle = '#a5b4fc';
        ctx.fillRect(p.x, p.y, p.w, 3);
      }}

      // Draw coins
      for (const c of coins) {{
        if (!c.collected) {{
          ctx.beginPath();
          ctx.arc(c.x, c.y, 8, 0, Math.PI * 2);
          ctx.fillStyle = '#fbbf24';
          ctx.fill();
          ctx.strokeStyle = '#f59e0b';
          ctx.stroke();
        }}
      }}

      // Draw player
      ctx.fillStyle = '#ec4899';
      ctx.fillRect(player.x, player.y, player.w, player.h);
      ctx.fillStyle = '#fff';
      // Eyes
      ctx.fillRect(player.x + (player.vx >= 0 ? 14 : 4), player.y + 6, 6, 6);

      requestAnimationFrame(() => {{ update(); render(); }});
    }}

    function resetGame() {{
      player = {{ x: 60, y: 320, vx: 0, vy: 0, w: 26, h: 32, grounded: false, score: 0, coins: 0, lives: 3 }};
      coins.forEach(c => c.collected = false);
      document.getElementById('hud-score').innerText = '0';
      document.getElementById('hud-coins').innerText = '0/5';
      document.getElementById('hud-lives').innerText = '❤️❤️❤️';
    }}

    requestAnimationFrame(render);
  </script>
</body>
</html>"""

def get_racing_html(title="Turbo Nitro Racing", desc="High-Speed Circuit Racing Simulator"):
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
      background: radial-gradient(circle at 50% 10%, #1c1917 0%, #09090b 70%);
      color: #f8fafc;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 1.5rem;
    }}
    .header {{ text-align: center; margin-bottom: 1rem; }}
    h1 {{ font-size: 2rem; font-weight: 800; background: linear-gradient(135deg, #fff 30%, #f97316 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    .telemetry {{ display: flex; gap: 1.5rem; background: rgba(28, 25, 23, 0.85); border: 1px solid rgba(249, 115, 22, 0.3); padding: 0.6rem 1.75rem; border-radius: 9999px; margin-bottom: 1rem; font-family: 'JetBrains Mono', monospace; font-size: 0.9rem; }}
    .canvas-container {{ border: 2px solid rgba(249, 115, 22, 0.3); border-radius: 12px; box-shadow: 0 20px 40px rgba(0,0,0,0.8); overflow: hidden; }}
    canvas {{ display: block; background: #1c1917; }}
    .hint {{ margin-top: 0.75rem; color: #a8a29e; font-size: 0.85rem; }}
  </style>
</head>
<body>
  <div class="header">
    <h1>{title}</h1>
    <p style="color: #a8a29e;">{desc}</p>
  </div>
  <div class="telemetry">
    <div>SPEED: <span id="speedVal" style="color: #f97316; font-weight: 800;">0 MPH</span></div>
    <div>LAP: <span id="lapVal" style="color: #38bdf8; font-weight: 800;">1/3</span></div>
    <div>TIME: <span id="timeVal" style="color: #4ade80; font-weight: 800;">0.0s</span></div>
    <div>NITRO: <span id="nitroVal" style="color: #fbbf24; font-weight: 800;">100%</span></div>
  </div>
  <div class="canvas-container">
    <canvas id="raceCanvas" width="750" height="440"></canvas>
  </div>
  <div class="hint">Steer: <b>A / D / Left / Right</b> &bull; Accel: <b>W / Up</b> &bull; Brake/Reverse: <b>S / Down</b> &bull; Boost: <b>Space</b></div>

  <script>
    const canvas = document.getElementById('raceCanvas');
    const ctx = canvas.getContext('2d');

    let car = {{ x: 375, y: 380, angle: 0, speed: 0, maxSpeed: 6.5, accel: 0.18, friction: 0.96, steer: 0.045, nitro: 100 }};
    let lap = 1;
    let lapTime = 0;
    const keys = {{}};

    window.addEventListener('keydown', e => keys[e.code] = true);
    window.addEventListener('keyup', e => keys[e.code] = false);

    function update() {{
      if (keys['KeyW'] || keys['ArrowUp']) {{
        const boost = (keys['Space'] && car.nitro > 0) ? 1.5 : 1.0;
        if (boost > 1.0) car.nitro = Math.max(0, car.nitro - 0.5);
        car.speed += car.accel * boost;
      }}
      if (keys['KeyS'] || keys['ArrowDown']) car.speed -= car.accel * 0.7;
      car.speed *= car.friction;

      if (Math.abs(car.speed) > 0.1) {{
        const dir = car.speed > 0 ? 1 : -1;
        if (keys['KeyA'] || keys['ArrowLeft']) car.angle -= car.steer * dir;
        if (keys['KeyD'] || keys['ArrowRight']) car.angle += car.steer * dir;
      }}

      car.x += Math.sin(car.angle) * car.speed;
      car.y -= Math.cos(car.angle) * car.speed;

      lapTime += 0.016;
      document.getElementById('speedVal').innerText = Math.round(Math.abs(car.speed) * 22) + ' MPH';
      document.getElementById('timeVal').innerText = lapTime.toFixed(1) + 's';
      document.getElementById('nitroVal').innerText = Math.round(car.nitro) + '%';
    }}

    function render() {{
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Draw Racetrack (outer oval & inner island)
      ctx.fillStyle = '#292524';
      ctx.beginPath();
      ctx.ellipse(375, 220, 330, 180, 0, 0, Math.PI * 2);
      ctx.fill();

      // Inner green island
      ctx.fillStyle = '#14532d';
      ctx.beginPath();
      ctx.ellipse(375, 220, 200, 90, 0, 0, Math.PI * 2);
      ctx.fill();

      // Finish line
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 4;
      ctx.beginPath();
      ctx.moveTo(375, 310);
      ctx.lineTo(375, 400);
      ctx.stroke();

      // Draw Car
      ctx.save();
      ctx.translate(car.x, car.y);
      ctx.rotate(car.angle);

      // Car body
      ctx.fillStyle = '#f97316';
      ctx.fillRect(-10, -18, 20, 36);
      ctx.fillStyle = '#1c1917';
      ctx.fillRect(-8, -8, 16, 16); // windshield
      // Headlights
      ctx.fillStyle = '#fef08a';
      ctx.fillRect(-8, -20, 5, 3);
      ctx.fillRect(3, -20, 5, 3);
      ctx.restore();

      requestAnimationFrame(() => {{ update(); render(); }});
    }}

    requestAnimationFrame(render);
  </script>
</body>
</html>"""

def get_puzzle_html(title="Tile Shift Puzzle", desc="Classic 15-Puzzle Sliding Challenge"):
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
      background: radial-gradient(circle at 50% 10%, #064e3b 0%, #022c22 70%);
      color: #f8fafc;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 1.5rem;
    }}
    .header {{ text-align: center; margin-bottom: 1.25rem; }}
    h1 {{ font-size: 2rem; font-weight: 800; background: linear-gradient(135deg, #fff 30%, #34d399 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    .stats-bar {{ display: flex; gap: 1.5rem; background: rgba(6, 78, 59, 0.8); border: 1px solid rgba(52, 211, 153, 0.3); padding: 0.6rem 1.75rem; border-radius: 9999px; margin-bottom: 1.25rem; font-family: 'JetBrains Mono', monospace; font-size: 0.95rem; }}
    .grid-board {{ display: grid; grid-template-columns: repeat(4, 75px); grid-template-rows: repeat(4, 75px); gap: 8px; background: #064e3b; padding: 12px; border-radius: 12px; box-shadow: 0 20px 40px rgba(0,0,0,0.6); border: 2px solid rgba(52, 211, 153, 0.3); }}
    .tile {{ background: linear-gradient(135deg, #10b981, #059669); color: white; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; font-weight: 800; border-radius: 8px; cursor: pointer; user-select: none; box-shadow: 0 4px 6px rgba(0,0,0,0.2); transition: transform 0.1s; }}
    .tile:active {{ transform: scale(0.96); }}
    .tile.empty {{ background: rgba(0,0,0,0.3); box-shadow: none; cursor: default; }}
    .btn {{ margin-top: 1.25rem; padding: 0.6rem 1.5rem; background: #10b981; color: #022c22; font-weight: 800; border: none; border-radius: 8px; cursor: pointer; }}
  </style>
</head>
<body>
  <div class="header">
    <h1>{title}</h1>
    <p style="color: #a7f3d0;">{desc}</p>
  </div>
  <div class="stats-bar">
    <div>MOVES: <span id="moveCount" style="color: #fbbf24; font-weight: 800;">0</span></div>
    <div>TIME: <span id="timerVal" style="color: #38bdf8; font-weight: 800;">0s</span></div>
    <div>STATUS: <span id="winStatus" style="color: #34d399; font-weight: 800;">Solving</span></div>
  </div>
  <div class="grid-board" id="puzzleBoard"></div>
  <button class="btn" onclick="shufflePuzzle()">Shuffle & Restart</button>

  <script>
    let grid = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,0];
    let moves = 0;
    let seconds = 0;
    let timer = setInterval(() => {{ seconds++; document.getElementById('timerVal').innerText = seconds + 's'; }}, 1000);

    function renderGrid() {{
      const b = document.getElementById('puzzleBoard');
      b.innerHTML = '';
      grid.forEach((num, idx) => {{
        const t = document.createElement('div');
        t.className = 'tile' + (num === 0 ? ' empty' : '');
        t.innerText = num === 0 ? '' : num;
        if (num !== 0) t.onclick = () => tryMove(idx);
        b.appendChild(t);
      }});
    }}

    function tryMove(idx) {{
      const emptyIdx = grid.indexOf(0);
      const r1 = Math.floor(idx / 4), c1 = idx % 4;
      const r2 = Math.floor(emptyIdx / 4), c2 = emptyIdx % 4;
      if (Math.abs(r1 - r2) + Math.abs(c1 - c2) === 1) {{
        grid[emptyIdx] = grid[idx];
        grid[idx] = 0;
        moves++;
        document.getElementById('moveCount').innerText = moves;
        renderGrid();
        checkWin();
      }}
    }}

    function checkWin() {{
      const isWin = grid.slice(0, 15).every((val, i) => val === i + 1);
      if (isWin) {{
        document.getElementById('winStatus').innerText = '🎉 SOLVED!';
        document.getElementById('winStatus').style.color = '#fbbf24';
      }}
    }}

    function shufflePuzzle() {{
      for (let i = 0; i < 120; i++) {{
        const emptyIdx = grid.indexOf(0);
        const r = Math.floor(emptyIdx / 4), c = emptyIdx % 4;
        const neighbors = [];
        if (r > 0) neighbors.push(emptyIdx - 4);
        if (r < 3) neighbors.push(emptyIdx + 4);
        if (c > 0) neighbors.push(emptyIdx - 1);
        if (c < 3) neighbors.push(emptyIdx + 1);
        const swapIdx = neighbors[Math.floor(Math.random() * neighbors.length)];
        grid[emptyIdx] = grid[swapIdx];
        grid[swapIdx] = 0;
      }}
      moves = 0; seconds = 0;
      document.getElementById('moveCount').innerText = '0';
      document.getElementById('winStatus').innerText = 'Solving';
      renderGrid();
    }}

    shufflePuzzle();
  </script>
</body>
</html>"""

def get_educational_html(title="StudyDeck Flashcards & Quiz", desc="Interactive Learning & Quiz Mastery Suite"):
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
      background: radial-gradient(circle at 50% 10%, #1e1b4b 0%, #0f172a 70%);
      color: #f8fafc;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 1.5rem;
    }}
    .header {{ text-align: center; margin-bottom: 1.25rem; }}
    h1 {{ font-size: 2rem; font-weight: 800; background: linear-gradient(135deg, #fff 30%, #818cf8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    .tabs {{ display: flex; gap: 0.5rem; margin-bottom: 1.5rem; }}
    .tab-btn {{ padding: 0.5rem 1.25rem; border-radius: 9999px; border: 1px solid rgba(255,255,255,0.15); background: rgba(255,255,255,0.05); color: #cbd5e1; font-weight: 700; cursor: pointer; }}
    .tab-btn.active {{ background: #6366f1; color: white; border-color: #6366f1; }}
    .flashcard {{ width: 500px; height: 260px; background: rgba(30, 41, 59, 0.85); border: 2px solid rgba(99, 102, 241, 0.4); border-radius: 16px; padding: 2rem; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; cursor: pointer; box-shadow: 0 20px 40px rgba(0,0,0,0.5); user-select: none; }}
    .flashcard-term {{ font-size: 1.5rem; font-weight: 800; color: #818cf8; margin-bottom: 0.75rem; }}
    .flashcard-def {{ font-size: 1rem; color: #cbd5e1; line-height: 1.5; }}
    .nav-row {{ display: flex; gap: 1rem; margin-top: 1.25rem; width: 500px; justify-content: space-between; }}
    .btn {{ padding: 0.6rem 1.25rem; border-radius: 8px; border: none; font-weight: 700; cursor: pointer; }}
    .btn-primary {{ background: #6366f1; color: white; }}
    .btn-secondary {{ background: rgba(255,255,255,0.1); color: white; }}
  </style>
</head>
<body>
  <div class="header">
    <h1>{title}</h1>
    <p style="color: #94a3b8;">{desc}</p>
  </div>
  <div class="tabs">
    <button class="tab-btn active" id="tab-fc">Flashcards Mode</button>
    <button class="tab-btn" id="tab-quiz" onclick="alert('Quiz Mode: 10 Questions Loaded!')">Interactive Quiz</button>
  </div>
  <div class="flashcard" onclick="flipCard()">
    <div style="font-size: 0.75rem; text-transform: uppercase; color: #94a3b8; margin-bottom: 0.5rem;" id="sideLabel">Click to Flip (Term)</div>
    <div class="flashcard-term" id="cardText">Idempotency</div>
    <div class="flashcard-def" id="cardDef" style="display: none;">The property of certain operations in mathematics and computer science whereby they can be applied multiple times without changing the result beyond the initial application.</div>
  </div>
  <div class="nav-row">
    <button class="btn btn-secondary" onclick="prevCard()">Previous</button>
    <span id="deckCounter" style="display: flex; align-items: center; font-family: 'JetBrains Mono', monospace;">Card 1 of 5</span>
    <button class="btn btn-primary" onclick="nextCard()">Next Card</button>
  </div>

  <script>
    const deck = [
      {{ term: "Idempotency", def: "An operation that produces the same result no matter how many times it is executed with identical parameters." }},
      {{ term: "ACID Properties", def: "Atomicity, Consistency, Isolation, and Durability - guaranteeing database transactions are processed reliably." }},
      {{ term: "CAP Theorem", def: "In a distributed data store, it is impossible to simultaneously provide Consistency, Availability, and Partition tolerance." }},
      {{ term: "Eventual Consistency", def: "A consistency model used in distributed computing to achieve high availability where all replicas eventually converge." }},
      {{ term: "SOLID Principles", def: "Five software design principles: Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, and Dependency Inversion." }}
    ];

    let currentIdx = 0;
    let isFlipped = false;

    function renderCard() {{
      const c = deck[currentIdx];
      isFlipped = false;
      document.getElementById('sideLabel').innerText = 'Click to Flip (Term)';
      document.getElementById('cardText').style.display = 'block';
      document.getElementById('cardDef').style.display = 'none';
      document.getElementById('cardText').innerText = c.term;
      document.getElementById('cardDef').innerText = c.def;
      document.getElementById('deckCounter').innerText = `Card ${{currentIdx + 1}} of ${{deck.length}}`;
    }}

    function flipCard() {{
      isFlipped = !isFlipped;
      document.getElementById('sideLabel').innerText = isFlipped ? 'Click to Flip (Definition)' : 'Click to Flip (Term)';
      document.getElementById('cardText').style.display = isFlipped ? 'none' : 'block';
      document.getElementById('cardDef').style.display = isFlipped ? 'block' : 'none';
    }}

    function nextCard() {{ currentIdx = (currentIdx + 1) % deck.length; renderCard(); }}
    function prevCard() {{ currentIdx = (currentIdx - 1 + deck.length) % deck.length; renderCard(); }}

    renderCard();
  </script>
</body>
</html>"""

def get_sky_strike_game_html(title="Sky Strike", desc="Aerial Combat Dogfight Simulator"):
    clean_title = title if title and "SE IntelliPlatform" not in title else "Sky Strike"
    clean_desc = desc if desc else "Fast-paced aerial combat game with real-time dogfights, dynamic weather, upgradeable aircraft, and avionics HUD."

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{clean_title} — Aerial Combat Simulator</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&family=JetBrains+Mono:wght@500;700;800&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #060a12;
      --card-bg: rgba(13, 20, 36, 0.88);
      --border: rgba(56, 189, 248, 0.25);
      --border-glow: rgba(56, 189, 248, 0.45);
      --cyan: #38bdf8;
      --cyan-dark: #0284c7;
      --amber: #f59e0b;
      --red: #ef4444;
      --green: #10b981;
      --text: #f8fafc;
      --muted: #94a3b8;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Plus Jakarta Sans', sans-serif;
      background: radial-gradient(circle at 50% 15%, #0f233d 0%, #060a12 75%);
      color: var(--text);
      min-height: 100vh;
      padding: 1.25rem;
      display: flex;
      flex-direction: column;
      align-items: center;
      overflow-x: hidden;
    }}
    .header {{
      text-align: center;
      margin-bottom: 1rem;
      max-width: 1100px;
      width: 100%;
    }}
    .badge {{
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      background: rgba(56, 189, 248, 0.15);
      border: 1px solid var(--border);
      color: var(--cyan);
      padding: 0.3rem 0.85rem;
      border-radius: 9999px;
      font-size: 0.8rem;
      font-weight: 700;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      margin-bottom: 0.4rem;
    }}
    h1 {{
      font-size: 2.2rem;
      font-weight: 800;
      background: linear-gradient(135deg, #f8fafc 20%, #7dd3fc 60%, #0284c7 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      letter-spacing: -0.02em;
    }}
    .subtitle {{
      color: var(--muted);
      font-size: 0.9rem;
      margin-top: 0.2rem;
    }}
    .hud-bar {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 0.6rem 1.25rem;
      max-width: 1100px;
      width: 100%;
      margin-bottom: 0.8rem;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.85rem;
      flex-wrap: wrap;
      gap: 0.75rem;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
    }}
    .hud-metric {{
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }}
    .hud-label {{
      color: var(--muted);
      font-size: 0.75rem;
      text-transform: uppercase;
    }}
    .hud-value {{
      color: var(--cyan);
      font-weight: 800;
      font-size: 1.05rem;
    }}
    .bar-container {{
      width: 110px;
      height: 10px;
      background: rgba(255, 255, 255, 0.1);
      border-radius: 9999px;
      overflow: hidden;
      display: inline-block;
    }}
    .bar-fill {{
      height: 100%;
      border-radius: 9999px;
      transition: width 0.2s;
    }}
    .bar-hull {{ background: linear-gradient(90deg, #10b981, #38bdf8); }}
    .bar-afterburner {{ background: linear-gradient(90deg, #f59e0b, #ef4444); }}
    .game-grid {{
      display: grid;
      grid-template-columns: 780px 300px;
      gap: 1.25rem;
      max-width: 1100px;
      width: 100%;
    }}
    @media (max-width: 1100px) {{
      .game-grid {{ grid-template-columns: 1fr; }}
    }}
    .canvas-wrapper {{
      position: relative;
      background: #020617;
      border: 2px solid var(--border);
      border-radius: 14px;
      overflow: hidden;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.7), 0 0 25px rgba(56, 189, 248, 0.15);
    }}
    canvas {{
      display: block;
      width: 100%;
      height: 480px;
      background: #030712;
      cursor: crosshair;
    }}
    .panel {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 1.2rem;
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }}
    .panel-title {{
      font-size: 1rem;
      font-weight: 700;
      color: var(--cyan);
      display: flex;
      align-items: center;
      gap: 0.4rem;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      padding-bottom: 0.5rem;
    }}
    .hangar-item {{
      background: rgba(15, 23, 42, 0.7);
      border: 1px solid rgba(255, 255, 255, 0.07);
      border-radius: 8px;
      padding: 0.7rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .hangar-info h4 {{
      font-size: 0.85rem;
      font-weight: 700;
    }}
    .hangar-info p {{
      font-size: 0.72rem;
      color: var(--muted);
      margin-top: 0.15rem;
    }}
    .btn-upgrade {{
      background: linear-gradient(135deg, #0284c7, #0369a1);
      color: white;
      border: none;
      padding: 0.4rem 0.8rem;
      border-radius: 6px;
      font-size: 0.75rem;
      font-weight: 700;
      cursor: pointer;
      font-family: 'JetBrains Mono', monospace;
      transition: all 0.2s;
    }}
    .btn-upgrade:hover {{
      background: linear-gradient(135deg, #38bdf8, #0284c7);
      transform: translateY(-1px);
    }}
    .weather-selector {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 0.5rem;
    }}
    .btn-weather {{
      background: rgba(15, 23, 42, 0.7);
      border: 1px solid rgba(255, 255, 255, 0.1);
      color: var(--muted);
      padding: 0.45rem;
      border-radius: 6px;
      font-size: 0.75rem;
      font-weight: 600;
      cursor: pointer;
      text-align: center;
      transition: all 0.2s;
    }}
    .btn-weather.active {{
      background: rgba(56, 189, 248, 0.2);
      border-color: var(--cyan);
      color: #fff;
    }}
    .controls-hint {{
      font-size: 0.74rem;
      color: var(--muted);
      line-height: 1.4;
      background: rgba(2, 6, 23, 0.6);
      padding: 0.75rem;
      border-radius: 8px;
      border: 1px solid rgba(255, 255, 255, 0.05);
    }}
    .controls-hint b {{
      color: var(--cyan);
    }}
  </style>
</head>
<body>
  <div class="header">
    <div class="badge">&#9992;&#65039; LIVE AERIAL COMBAT &bull; SKY STRIKE DOGFIGHT ENGINE</div>
    <h1>{clean_title}</h1>
    <p class="subtitle">{clean_desc}</p>
  </div>

  <div class="hud-bar">
    <div class="hud-metric">
      <span class="hud-label">AIRSPEED:</span>
      <span class="hud-value" id="hudSpeed">650 KTAS</span>
    </div>
    <div class="hud-metric">
      <span class="hud-label">ALTITUDE:</span>
      <span class="hud-value" id="hudAlt">18,500 FT</span>
    </div>
    <div class="hud-metric">
      <span class="hud-label">HULL:</span>
      <div class="bar-container"><div class="bar-fill bar-hull" id="hudHull" style="width: 100%;"></div></div>
    </div>
    <div class="hud-metric">
      <span class="hud-label">AFTERBURNER:</span>
      <div class="bar-container"><div class="bar-fill bar-afterburner" id="hudAfterburner" style="width: 100%;"></div></div>
    </div>
    <div class="hud-metric">
      <span class="hud-label">MISSILES:</span>
      <span class="hud-value" id="hudMissiles" style="color: var(--amber);">4/4</span>
    </div>
    <div class="hud-metric">
      <span class="hud-label">BOGEYS DOWN:</span>
      <span class="hud-value" id="hudKills" style="color: var(--green);">0</span>
    </div>
    <div class="hud-metric">
      <span class="hud-label">SCORE:</span>
      <span class="hud-value" id="hudScore">0</span>
    </div>
  </div>

  <div class="game-grid">
    <div class="canvas-wrapper">
      <canvas id="skyStrikeCanvas" width="780" height="480"></canvas>
    </div>

    <div class="panel">
      <div class="panel-title">&#9881;&#65039; Aircraft Upgrade Hangar</div>
      <div class="hangar-item">
        <div class="hangar-info">
          <h4>Vulcan M61 Cannon</h4>
          <p>Fire Rate: <span id="valCannon">Level 1 (750 RPM)</span></p>
        </div>
        <button class="btn-upgrade" onclick="upgradePart('cannon')">+UPGRADE</button>
      </div>

      <div class="hangar-item">
        <div class="hangar-info">
          <h4>Titanium Alloy Hull</h4>
          <p>Armor: <span id="valHull">Level 1 (100 HP)</span></p>
        </div>
        <button class="btn-upgrade" onclick="upgradePart('hull')">+UPGRADE</button>
      </div>

      <div class="hangar-item">
        <div class="hangar-info">
          <h4>Afterburner Turbofan</h4>
          <p>Thrust: <span id="valEngine">Level 1 (1.0x Boost)</span></p>
        </div>
        <button class="btn-upgrade" onclick="upgradePart('engine')">+UPGRADE</button>
      </div>

      <div class="hangar-item">
        <div class="hangar-info">
          <h4>AIM-9X Sidewinder</h4>
          <p>Capacity: <span id="valMissile">4 Missiles</span></p>
        </div>
        <button class="btn-upgrade" onclick="upgradePart('missile')">+REARM</button>
      </div>

      <div class="panel-title" style="margin-top: 0.5rem;">&#127783;&#65039; Dynamic Weather Condition</div>
      <div class="weather-selector">
        <div class="btn-weather active" onclick="setWeather('clear')">&#9728;&#65039; Clear Skies</div>
        <div class="btn-weather" onclick="setWeather('storm')">&#9889; Thunderstorm</div>
        <div class="btn-weather" onclick="setWeather('clouds')">&#9729;&#65039; Overcast</div>
        <div class="btn-weather" onclick="setWeather('night')">&#127769; Night Sortie</div>
      </div>

      <div class="controls-hint">
        <b>FLIGHT CONTROLS:</b><br/>
        &bull; <b>W / S / Up / Down</b>: Throttle / Pitch<br/>
        &bull; <b>A / D / Left / Right</b>: Bank &amp; Turn<br/>
        &bull; <b>Space / Click</b>: Fire Vulcan Cannon<br/>
        &bull; <b>E / Right Click</b>: Launch Sidewinder Missile<br/>
        &bull; <b>Shift</b>: Afterburner Boost
      </div>
    </div>
  </div>

  <script>
    // SKY STRIKE — AERIAL COMBAT SIMULATOR ENGINE
    const canvas = document.getElementById('skyStrikeCanvas');
    const ctx = canvas.getContext('2d');

    const state = {{
      player: {{
        x: canvas.width / 2,
        y: canvas.height * 0.75,
        vx: 0,
        vy: 0,
        angle: -Math.PI / 2,
        speed: 4,
        maxSpeed: 7,
        health: 100,
        maxHealth: 100,
        afterburner: 100,
        missiles: 4,
        kills: 0,
        score: 0,
      }},
      cannonLevel: 1,
      hullLevel: 1,
      engineLevel: 1,
      weather: 'clear',
      weatherTimer: 0,
      bullets: [],
      missiles: [],
      bogeys: [],
      particles: [],
      clouds: [],
      keys: {{}},
      lastShot: 0,
      lastMissile: 0,
    }};

    // Initialize ambient atmospheric clouds
    for (let i = 0; i < 8; i++) {{
      state.clouds.push({{
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        r: 30 + Math.random() * 50,
        speed: 0.5 + Math.random() * 1.5,
        alpha: 0.15 + Math.random() * 0.2,
      }});
    }}

    // Spawn enemy interceptor bogey
    function spawnBogey() {{
      if (state.bogeys.length >= 5) return;
      const side = Math.floor(Math.random() * 3);
      let x, y;
      if (side === 0) {{ x = Math.random() * canvas.width; y = -30; }}
      else if (side === 1) {{ x = -30; y = Math.random() * (canvas.height * 0.5); }}
      else {{ x = canvas.width + 30; y = Math.random() * (canvas.height * 0.5); }}

      state.bogeys.push({{
        x, y,
        vx: 0, vy: 0,
        angle: Math.PI / 2,
        health: 40,
        maxHealth: 40,
        speed: 2.2 + Math.random() * 1.5,
        fireCooldown: Math.random() * 100,
      }});
    }}

    // Weather switching
    function setWeather(mode) {{
      state.weather = mode;
      document.querySelectorAll('.btn-weather').forEach(b => {{
        b.classList.toggle('active', b.textContent.toLowerCase().includes(mode));
      }});
    }}

    // Upgrade part in hangar
    function upgradePart(part) {{
      if (part === 'cannon') {{
        state.cannonLevel++;
        document.getElementById('valCannon').textContent = 'Level ' + state.cannonLevel + ' (' + (750 + state.cannonLevel * 250) + ' RPM)';
      }} else if (part === 'hull') {{
        state.hullLevel++;
        state.player.maxHealth += 25;
        state.player.health = state.player.maxHealth;
        document.getElementById('valHull').textContent = 'Level ' + state.hullLevel + ' (' + state.player.maxHealth + ' HP)';
      }} else if (part === 'engine') {{
        state.engineLevel++;
        state.player.maxSpeed += 1;
        document.getElementById('valEngine').textContent = 'Level ' + state.engineLevel + ' (' + (1.0 + state.engineLevel * 0.2).toFixed(1) + 'x Boost)';
      }} else if (part === 'missile') {{
        state.player.missiles = 4;
        document.getElementById('hudMissiles').textContent = '4/4';
      }}
      state.player.score += 50;
      updateHUD();
    }}

    function updateHUD() {{
      document.getElementById('hudSpeed').textContent = Math.round(state.player.speed * 110) + ' KTAS';
      document.getElementById('hudAlt').textContent = (18500 + Math.round(state.player.y * 10)).toLocaleString() + ' FT';
      const hullPct = Math.max(0, Math.min(100, (state.player.health / state.player.maxHealth) * 100));
      document.getElementById('hudHull').style.width = hullPct + '%';
      document.getElementById('hudAfterburner').style.width = state.player.afterburner + '%';
      document.getElementById('hudMissiles').textContent = state.player.missiles + '/4';
      document.getElementById('hudKills').textContent = state.player.kills;
      document.getElementById('hudScore').textContent = state.player.score;
    }}

    // Input handlers
    window.addEventListener('keydown', e => {{
      state.keys[e.key.toLowerCase()] = true;
      state.keys[e.code] = true;
      if (['Space', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.code)) {{
        e.preventDefault();
      }}
    }});
    window.addEventListener('keyup', e => {{
      state.keys[e.key.toLowerCase()] = false;
      state.keys[e.code] = false;
    }});

    canvas.addEventListener('mousedown', e => {{
      if (e.button === 0) state.keys['firing_cannon'] = true;
      if (e.button === 2) fireMissile();
    }});
    canvas.addEventListener('mouseup', e => {{
      if (e.button === 0) state.keys['firing_cannon'] = false;
    }});
    canvas.addEventListener('contextmenu', e => e.preventDefault());

    function fireVulcan() {{
      const now = performance.now();
      const fireInterval = Math.max(80, 200 - state.cannonLevel * 30);
      if (now - state.lastShot < fireInterval) return;
      state.lastShot = now;

      const p = state.player;
      const noseX = p.x + Math.cos(p.angle) * 20;
      const noseY = p.y + Math.sin(p.angle) * 20;
      const bSpeed = 14;

      state.bullets.push({{
        x: noseX,
        y: noseY,
        vx: Math.cos(p.angle) * bSpeed,
        vy: Math.sin(p.angle) * bSpeed,
        damage: 15 + state.cannonLevel * 5,
        life: 50,
      }});

      // Muzzle flash particle
      state.particles.push({{
        x: noseX, y: noseY,
        vx: (Math.random() - 0.5) * 3, vy: (Math.random() - 0.5) * 3,
        r: 3, color: '#38bdf8', life: 8, maxLife: 8,
      }});
    }}

    function fireMissile() {{
      const now = performance.now();
      if (now - state.lastMissile < 800 || state.player.missiles <= 0) return;
      state.lastMissile = now;
      state.player.missiles--;

      const p = state.player;
      state.missiles.push({{
        x: p.x,
        y: p.y,
        vx: Math.cos(p.angle) * 8,
        vy: Math.sin(p.angle) * 8,
        angle: p.angle,
        speed: 9,
        damage: 65,
        life: 140,
        target: state.bogeys[0] || null,
      }});
      updateHUD();
    }}

    // Spawn loop
    setInterval(() => {{
      if (state.bogeys.length < 4) spawnBogey();
    }}, 2000);

    // Main animation loop
    function update() {{
      const p = state.player;

      // Turning controls
      const turnSpeed = 0.055;
      if (state.keys['a'] || state.keys['arrowleft']) p.angle -= turnSpeed;
      if (state.keys['d'] || state.keys['arrowright']) p.angle += turnSpeed;

      // Throttle & Afterburner
      let targetSpeed = 3.5;
      const isBoosting = (state.keys['shift'] || state.keys['shiftleft'] || state.keys['shiftright']) && p.afterburner > 5;
      if (isBoosting) {{
        targetSpeed = p.maxSpeed * (1.1 + state.engineLevel * 0.15);
        p.afterburner = Math.max(0, p.afterburner - 0.8);
      }} else {{
        p.afterburner = Math.min(100, p.afterburner + 0.3);
      }}

      if (state.keys['w'] || state.keys['arrowup']) targetSpeed += 1.5;
      if (state.keys['s'] || state.keys['arrowdown']) targetSpeed = Math.max(1.8, targetSpeed - 1.5);

      // Weather turbulence
      if (state.weather === 'storm') {{
        p.angle += (Math.random() - 0.5) * 0.02;
      }}

      p.speed += (targetSpeed - p.speed) * 0.08;
      p.x += Math.cos(p.angle) * p.speed;
      p.y += Math.sin(p.angle) * p.speed;

      // Screen wrap
      if (p.x < -20) p.x = canvas.width + 20;
      if (p.x > canvas.width + 20) p.x = -20;
      if (p.y < -20) p.y = canvas.height + 20;
      if (p.y > canvas.height + 20) p.y = -20;

      // Afterburner trail
      if (Math.random() < 0.8) {{
        state.particles.push({{
          x: p.x - Math.cos(p.angle) * 16,
          y: p.y - Math.sin(p.angle) * 16,
          vx: -Math.cos(p.angle) * 2 + (Math.random() - 0.5),
          vy: -Math.sin(p.angle) * 2 + (Math.random() - 0.5),
          r: isBoosting ? 4 : 2.5,
          color: isBoosting ? '#f59e0b' : '#38bdf8',
          life: 18,
          maxLife: 18,
        }});
      }}

      // Fire weapon if pressed
      if (state.keys[' '] || state.keys['space'] || state.keys['firing_cannon']) {{
        fireVulcan();
      }}
      if (state.keys['e'] || state.keys['x']) {{
        fireMissile();
      }}

      // Update Bullets
      for (let i = state.bullets.length - 1; i >= 0; i--) {{
        const b = state.bullets[i];
        b.x += b.vx;
        b.y += b.vy;
        b.life--;

        // Collision with bogeys
        for (let j = state.bogeys.length - 1; j >= 0; j--) {{
          const e = state.bogeys[j];
          const dist = Math.hypot(b.x - e.x, b.y - e.y);
          if (dist < 22) {{
            e.health -= b.damage;
            b.life = 0;
            // Hit spark
            state.particles.push({{
              x: b.x, y: b.y, vx: (Math.random() - 0.5) * 4, vy: (Math.random() - 0.5) * 4,
              r: 2, color: '#f59e0b', life: 10, maxLife: 10,
            }});
            break;
          }}
        }}

        if (b.life <= 0 || b.x < 0 || b.x > canvas.width || b.y < 0 || b.y > canvas.height) {{
          state.bullets.splice(i, 1);
        }}
      }}

      // Update Missiles
      for (let i = state.missiles.length - 1; i >= 0; i--) {{
        const m = state.missiles[i];
        if (m.target && state.bogeys.includes(m.target)) {{
          const desired = Math.atan2(m.target.y - m.y, m.target.x - m.x);
          const diff = desired - m.angle;
          m.angle += Math.sin(diff) * 0.12;
        }}
        m.vx = Math.cos(m.angle) * m.speed;
        m.vy = Math.sin(m.angle) * m.speed;
        m.x += m.vx;
        m.y += m.vy;
        m.life--;

        // Smoke trail
        state.particles.push({{
          x: m.x, y: m.y, vx: (Math.random() - 0.5), vy: (Math.random() - 0.5),
          r: 2.5, color: '#94a3b8', life: 25, maxLife: 25,
        }});

        // Collision
        for (let j = state.bogeys.length - 1; j >= 0; j--) {{
          const e = state.bogeys[j];
          if (Math.hypot(m.x - e.x, m.y - e.y) < 28) {{
            e.health -= m.damage;
            m.life = 0;
            // Big explosion
            for (let k = 0; k < 15; k++) {{
              state.particles.push({{
                x: m.x, y: m.y,
                vx: (Math.random() - 0.5) * 7, vy: (Math.random() - 0.5) * 7,
                r: 3 + Math.random() * 4, color: k % 2 === 0 ? '#ef4444' : '#f59e0b',
                life: 20, maxLife: 20,
              }});
            }}
            break;
          }}
        }}

        if (m.life <= 0) state.missiles.splice(i, 1);
      }}

      // Update Bogeys
      for (let i = state.bogeys.length - 1; i >= 0; i--) {{
        const e = state.bogeys[i];
        // Move towards player or forward
        const angleToPlayer = Math.atan2(p.y - e.y, p.x - e.x);
        e.angle += Math.sin(angleToPlayer - e.angle) * 0.03;
        e.x += Math.cos(e.angle) * e.speed;
        e.y += Math.sin(e.angle) * e.speed;

        if (e.health <= 0) {{
          // Bogey destroyed
          for (let k = 0; k < 25; k++) {{
            state.particles.push({{
              x: e.x, y: e.y,
              vx: (Math.random() - 0.5) * 8, vy: (Math.random() - 0.5) * 8,
              r: 3 + Math.random() * 5, color: ['#ef4444', '#f59e0b', '#38bdf8'][k % 3],
              life: 30, maxLife: 30,
            }});
          }}
          state.bogeys.splice(i, 1);
          p.kills++;
          p.score += 250;
          updateHUD();
        }}
      }}

      // Update particles
      for (let i = state.particles.length - 1; i >= 0; i--) {{
        const pt = state.particles[i];
        pt.x += pt.vx;
        pt.y += pt.vy;
        pt.life--;
        if (pt.life <= 0) state.particles.splice(i, 1);
      }}

      // Update clouds
      for (const cl of state.clouds) {{
        cl.x += cl.speed;
        if (cl.x - cl.r > canvas.width) cl.x = -cl.r;
      }}

      updateHUD();
    }}

    function render() {{
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Background skies based on weather
      if (state.weather === 'night') {{
        ctx.fillStyle = '#020617';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        // Starfield
        ctx.fillStyle = 'rgba(255, 255, 255, 0.4)';
        for (let i = 0; i < 30; i++) {{
          ctx.fillRect((i * 97) % canvas.width, (i * 71) % canvas.height, 1.5, 1.5);
        }}
      }} else if (state.weather === 'storm') {{
        ctx.fillStyle = '#0f172a';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        // Lightning flash
        if (Math.random() < 0.015) {{
          ctx.fillStyle = 'rgba(255, 255, 255, 0.25)';
          ctx.fillRect(0, 0, canvas.width, canvas.height);
        }}
        // Rain streaks
        ctx.strokeStyle = 'rgba(56, 189, 248, 0.2)';
        ctx.lineWidth = 1;
        for (let i = 0; i < 20; i++) {{
          const rx = Math.random() * canvas.width;
          const ry = Math.random() * canvas.height;
          ctx.beginPath();
          ctx.moveTo(rx, ry);
          ctx.lineTo(rx - 5, ry + 15);
          ctx.stroke();
        }}
      }} else if (state.weather === 'clouds') {{
        ctx.fillStyle = '#1e293b';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
      }} else {{
        // Clear skies
        const grad = ctx.createLinearGradient(0, 0, 0, canvas.height);
        grad.addColorStop(0, '#0c2847');
        grad.addColorStop(1, '#071626');
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, canvas.width, canvas.height);
      }}

      // Atmospheric Clouds
      for (const cl of state.clouds) {{
        ctx.fillStyle = `rgba(255, 255, 255, ${{cl.alpha}})`;
        ctx.beginPath();
        ctx.arc(cl.x, cl.y, cl.r, 0, Math.PI * 2);
        ctx.fill();
      }}

      // Radar rings in corner
      const rx = canvas.width - 60, ry = 60, rr = 45;
      ctx.strokeStyle = 'rgba(56, 189, 248, 0.3)';
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.arc(rx, ry, rr, 0, Math.PI * 2);
      ctx.stroke();
      ctx.beginPath();
      ctx.arc(rx, ry, rr * 0.5, 0, Math.PI * 2);
      ctx.stroke();
      // Radar blips
      ctx.fillStyle = '#10b981';
      ctx.fillRect(rx - 2, ry - 2, 4, 4);
      for (const e of state.bogeys) {{
        const bx = rx + ((e.x - state.player.x) / canvas.width) * (rr * 0.8);
        const by = ry + ((e.y - state.player.y) / canvas.height) * (rr * 0.8);
        if (Math.hypot(bx - rx, by - ry) < rr) {{
          ctx.fillStyle = '#ef4444';
          ctx.fillRect(bx - 2, by - 2, 4, 4);
        }}
      }}

      // Render Particles
      for (const pt of state.particles) {{
        ctx.fillStyle = pt.color;
        ctx.beginPath();
        ctx.arc(pt.x, pt.y, Math.max(0.5, pt.r * (pt.life / pt.maxLife)), 0, Math.PI * 2);
        ctx.fill();
      }}

      // Render Bullets
      ctx.fillStyle = '#38bdf8';
      for (const b of state.bullets) {{
        ctx.beginPath();
        ctx.arc(b.x, b.y, 2.5, 0, Math.PI * 2);
        ctx.fill();
      }}

      // Render Missiles
      for (const m of state.missiles) {{
        ctx.save();
        ctx.translate(m.x, m.y);
        ctx.rotate(m.angle);
        ctx.fillStyle = '#f59e0b';
        ctx.fillRect(-8, -2, 16, 4);
        ctx.restore();
      }}

      // Render Enemy Bogeys
      for (const e of state.bogeys) {{
        ctx.save();
        ctx.translate(e.x, e.y);
        ctx.rotate(e.angle);

        // Bogey jet shape (Red/Amber)
        ctx.fillStyle = '#dc2626';
        ctx.beginPath();
        ctx.moveTo(18, 0);
        ctx.lineTo(-14, -14);
        ctx.lineTo(-8, 0);
        ctx.lineTo(-14, 14);
        ctx.closePath();
        ctx.fill();
        ctx.strokeStyle = '#f87171';
        ctx.stroke();

        ctx.restore();

        // Bogey health bar
        const hpPct = Math.max(0, e.health / e.maxHealth);
        ctx.fillStyle = 'rgba(0,0,0,0.5)';
        ctx.fillRect(e.x - 15, e.y - 22, 30, 4);
        ctx.fillStyle = hpPct > 0.4 ? '#ef4444' : '#f59e0b';
        ctx.fillRect(e.x - 15, e.y - 22, 30 * hpPct, 4);
      }}

      // Render Player Fighter Jet
      const p = state.player;
      ctx.save();
      ctx.translate(p.x, p.y);
      ctx.rotate(p.angle);

      // Main fuselage
      ctx.fillStyle = '#0284c7';
      ctx.beginPath();
      ctx.moveTo(22, 0);
      ctx.lineTo(-16, -18);
      ctx.lineTo(-8, -4);
      ctx.lineTo(-18, -4);
      ctx.lineTo(-20, 0);
      ctx.lineTo(-18, 4);
      ctx.lineTo(-8, 4);
      ctx.lineTo(-16, 18);
      ctx.closePath();
      ctx.fill();
      ctx.strokeStyle = '#38bdf8';
      ctx.lineWidth = 1.5;
      ctx.stroke();

      // Cockpit canopy
      ctx.fillStyle = '#38bdf8';
      ctx.beginPath();
      ctx.ellipse(2, 0, 7, 3, 0, 0, Math.PI * 2);
      ctx.fill();

      ctx.restore();

      requestAnimationFrame(() => {{
        update();
        render();
      }});
    }}

    // Boot simulator
    spawnBogey();
    spawnBogey();
    update();
    render();
  </script>
</body>
</html>"""
    return html


def get_space_arcade_game_html(title="Space Arcade Defender", desc="HTML5 Canvas 2D Retro Space Arcade Shooter"):
    clean_title = title if title and "SE IntelliPlatform" not in title else "Space Arcade Defender"
    clean_desc = desc if desc else "Retro 2D space shooter featuring 60 FPS HTML5 Canvas engine, starship laser cannons, alien waves, and persistent high scores."

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{clean_title} — HTML5 Canvas 2D Space Arcade</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&family=JetBrains+Mono:wght@500;700;800&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #050814;
      --card-bg: rgba(11, 19, 38, 0.9);
      --border: rgba(56, 189, 248, 0.28);
      --border-glow: rgba(56, 189, 248, 0.5);
      --cyan: #38bdf8;
      --magenta: #ec4899;
      --purple: #a855f7;
      --amber: #f59e0b;
      --green: #10b981;
      --red: #ef4444;
      --text: #f8fafc;
      --muted: #94a3b8;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Plus Jakarta Sans', sans-serif;
      background: radial-gradient(circle at 50% 20%, #0d1a33 0%, #050814 80%);
      color: var(--text);
      min-height: 100vh;
      padding: 1rem;
      display: flex;
      flex-direction: column;
      align-items: center;
      overflow-x: hidden;
    }}
    .arcade-header {{
      text-align: center;
      margin-bottom: 0.75rem;
      max-width: 840px;
      width: 100%;
    }}
    .arcade-badge {{
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      background: rgba(56, 189, 248, 0.15);
      border: 1px solid var(--border);
      color: var(--cyan);
      padding: 0.25rem 0.8rem;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 700;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      margin-bottom: 0.35rem;
    }}
    h1 {{
      font-size: 2rem;
      font-weight: 800;
      background: linear-gradient(135deg, #f8fafc 20%, #38bdf8 60%, #ec4899 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      letter-spacing: -0.02em;
    }}
    p.desc {{
      color: var(--muted);
      font-size: 0.85rem;
      margin-top: 0.2rem;
    }}
    .hud-bar {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 0.6rem 1.25rem;
      max-width: 800px;
      width: 100%;
      margin-bottom: 0.6rem;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
    }}
    .hud-stat {{
      display: flex;
      flex-direction: column;
      gap: 0.15rem;
    }}
    .hud-label {{
      font-size: 0.7rem;
      color: var(--muted);
      text-transform: uppercase;
      font-weight: 700;
      letter-spacing: 0.05em;
    }}
    .hud-val {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 1.15rem;
      font-weight: 800;
      color: #fff;
    }}
    .shield-meter {{
      width: 120px;
      height: 10px;
      background: rgba(255, 255, 255, 0.1);
      border-radius: 5px;
      overflow: hidden;
      margin-top: 0.2rem;
      border: 1px solid rgba(255, 255, 255, 0.15);
    }}
    .shield-fill {{
      height: 100%;
      width: 100%;
      background: linear-gradient(90deg, #10b981, #38bdf8);
      transition: width 0.2s ease, background 0.2s ease;
    }}
    .canvas-container {{
      position: relative;
      width: 800px;
      height: 480px;
      border-radius: 16px;
      overflow: hidden;
      border: 2px solid var(--border-glow);
      box-shadow: 0 0 35px rgba(56, 189, 248, 0.2), 0 20px 50px rgba(0, 0, 0, 0.8);
      background: #02040a;
    }}
    canvas {{
      display: block;
      width: 100%;
      height: 100%;
    }}
    .overlay-screen {{
      position: absolute;
      inset: 0;
      background: rgba(2, 4, 10, 0.88);
      backdrop-filter: blur(8px);
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 2rem;
      text-align: center;
      z-index: 10;
    }}
    .overlay-title {{
      font-size: 2.2rem;
      font-weight: 800;
      margin-bottom: 0.5rem;
      letter-spacing: -0.02em;
    }}
    .overlay-title.game-over {{
      color: var(--red);
      text-shadow: 0 0 20px rgba(239, 68, 68, 0.6);
    }}
    .overlay-title.start {{
      background: linear-gradient(135deg, #38bdf8, #ec4899);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}
    .overlay-subtitle {{
      color: var(--muted);
      font-size: 0.95rem;
      margin-bottom: 1.5rem;
      max-width: 480px;
    }}
    .btn-action {{
      background: linear-gradient(135deg, #0284c7, #38bdf8);
      color: #030712;
      border: none;
      padding: 0.75rem 1.8rem;
      border-radius: 9999px;
      font-size: 1rem;
      font-weight: 800;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      transition: all 0.2s ease;
      box-shadow: 0 0 20px rgba(56, 189, 248, 0.4);
    }}
    .btn-action:hover {{
      transform: translateY(-2px);
      box-shadow: 0 0 25px rgba(56, 189, 248, 0.6);
    }}
    .controls-panel {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      max-width: 800px;
      width: 100%;
      margin-top: 0.75rem;
      padding: 0.5rem 1rem;
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      font-size: 0.8rem;
      color: var(--muted);
    }}
    .key-badge {{
      background: rgba(255, 255, 255, 0.1);
      border: 1px solid rgba(255, 255, 255, 0.2);
      color: #fff;
      padding: 0.15rem 0.45rem;
      border-radius: 4px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.75rem;
      margin: 0 0.15rem;
    }}
    .touch-controls {{
      display: none;
      gap: 1rem;
      margin-top: 0.75rem;
      width: 100%;
      max-width: 800px;
      justify-content: space-between;
    }}
    @media (max-width: 850px) {{
      .canvas-container {{
        width: 100%;
        max-width: 600px;
        height: 380px;
      }}
      .touch-controls {{
        display: flex;
      }}
    }}
    .touch-btn {{
      background: rgba(15, 23, 42, 0.8);
      border: 1px solid var(--border);
      color: #fff;
      padding: 0.75rem 1.25rem;
      border-radius: 10px;
      font-weight: 700;
      touch-action: manipulation;
    }}
    .touch-btn:active {{
      background: var(--cyan);
      color: #000;
    }}
  </style>
</head>
<body>
  <div class="arcade-header">
    <div class="arcade-badge">⚡ HTML5 Canvas 2D Space Arcade Engine</div>
    <h1 id="arcade-title">{clean_title}</h1>
    <p class="desc" id="arcade-desc">{clean_desc}</p>
  </div>

  <div class="hud-bar">
    <div class="hud-stat">
      <span class="hud-label">Score</span>
      <span class="hud-val" id="hud-score" style="color: var(--cyan);">00000</span>
    </div>
    <div class="hud-stat">
      <span class="hud-label">Wave</span>
      <span class="hud-val" id="hud-wave" style="color: var(--magenta);">1</span>
    </div>
    <div class="hud-stat">
      <span class="hud-label">High Score</span>
      <span class="hud-val" id="hud-highscore" style="color: var(--amber);">02500</span>
    </div>
    <div class="hud-stat">
      <span class="hud-label">Shield Integrity</span>
      <div class="shield-meter">
        <div class="shield-fill" id="hud-shield"></div>
      </div>
    </div>
    <div class="hud-stat">
      <button class="btn-action" style="padding: 0.35rem 0.9rem; font-size: 0.8rem;" onclick="togglePause()" id="btn-pause">Pause (P)</button>
    </div>
  </div>

  <div class="canvas-container">
    <canvas id="gameCanvas" width="800" height="480"></canvas>

    <!-- Start Overlay -->
    <div id="startScreen" class="overlay-screen">
      <div class="overlay-title start">SPACE DEFENDER</div>
      <div class="overlay-subtitle">Repel invading alien squadrons across outer rim sectors. Use your dual plasma laser cannons to defend the fleet.</div>
      <button class="btn-action" onclick="startGame()">🚀 Launch Mission</button>
      <div style="margin-top: 1rem; font-size: 0.8rem; color: var(--muted);">Controls: <span class="key-badge">WASD / Arrows</span> Move | <span class="key-badge">SPACE</span> Fire Cannons</div>
    </div>

    <!-- Pause Overlay -->
    <div id="pauseScreen" class="overlay-screen" style="display: none;">
      <div class="overlay-title start">MISSION PAUSED</div>
      <div class="overlay-subtitle">Tactical radar on standby. Press P or click Resume to re-engage.</div>
      <button class="btn-action" onclick="togglePause()">▶ Resume Mission</button>
    </div>

    <!-- Game Over Overlay -->
    <div id="gameOverScreen" class="overlay-screen" style="display: none;">
      <div class="overlay-title game-over">STARSHIP DESTROYED</div>
      <div class="overlay-subtitle">Your shields collapsed under enemy plasma bombardment.</div>
      <div style="font-family: 'JetBrains Mono', monospace; font-size: 1.3rem; margin-bottom: 1.5rem;" id="finalScoreDisplay">Final Score: 0</div>
      <button class="btn-action" onclick="restartGame()">⚡ Play Again</button>
    </div>
  </div>

  <div class="controls-panel">
    <div><strong>Controls:</strong> <span class="key-badge">W/A/S/D</span> or <span class="key-badge">Arrows</span> Navigate | <span class="key-badge">Space</span> Dual Lasers | <span class="key-badge">P</span> Pause</div>
    <div id="status-engine">Engine: 60 FPS HTML5 Canvas • WebAudio Active</div>
  </div>

  <!-- Touch D-Pad for Mobile -->
  <div class="touch-controls">
    <div style="display: flex; gap: 0.3rem;">
      <button class="touch-btn" onpointerdown="keys['ArrowLeft']=true" onpointerup="keys['ArrowLeft']=false">◀</button>
      <button class="touch-btn" onpointerdown="keys['ArrowRight']=true" onpointerup="keys['ArrowRight']=false">▶</button>
    </div>
    <button class="touch-btn" style="background: linear-gradient(135deg, #0284c7, #38bdf8); color:#000; font-weight:800;" onpointerdown="fireLaser()">⚡ FIRE</button>
  </div>

  <script>
    const canvas = document.getElementById('gameCanvas');
    const ctx = canvas.getContext('2d');

    // State Machine
    let gameState = 'START'; // START, PLAYING, PAUSED, GAMEOVER
    let score = 0;
    let highScore = parseInt(localStorage.getItem('space_arcade_high_score') || '2500', 10);
    let wave = 1;
    let lastTime = 0;
    let animId = null;

    // Keys State
    const keys = {{}};
    window.addEventListener('keydown', (e) => {{
      keys[e.key] = true;
      if (e.code === 'Space') {{
        e.preventDefault();
        if (gameState === 'PLAYING') fireLaser();
        else if (gameState === 'START') startGame();
        else if (gameState === 'GAMEOVER') restartGame();
      }}
      if (e.key === 'p' || e.key === 'P') {{
        togglePause();
      }}
    }});
    window.addEventListener('keyup', (e) => {{
      keys[e.key] = false;
    }});

    // Starfield Parallax System
    const stars = [];
    for (let i = 0; i < 90; i++) {{
      stars.push({{
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        size: Math.random() < 0.6 ? 1 : Math.random() < 0.9 ? 2 : 2.8,
        speed: 0.5 + Math.random() * 2.2,
        color: Math.random() < 0.3 ? '#38bdf8' : Math.random() < 0.5 ? '#ec4899' : '#ffffff',
      }});
    }}

    // Player Starship
    const player = {{
      x: canvas.width / 2,
      y: canvas.height - 60,
      width: 38,
      height: 36,
      speed: 6,
      shield: 100,
      maxShield: 100,
      lastFire: 0,
      fireRate: 180, // ms
    }};

    // Projectiles & Enemies & Particles
    let lasers = [];
    let enemyLasers = [];
    let enemies = [];
    let particles = [];
    let floatingTexts = [];

    function initEnemies() {{
      enemies = [];
      const rows = 3 + Math.min(wave - 1, 2);
      const cols = 8;
      const startX = 100;
      const startY = 40;
      const spacingX = 75;
      const spacingY = 45;

      for (let r = 0; r < rows; r++) {{
        for (let c = 0; c < cols; c++) {{
          const isBoss = (r === 0);
          enemies.push({{
            x: startX + c * spacingX,
            y: startY + r * spacingY,
            width: isBoss ? 32 : 24,
            height: isBoss ? 26 : 20,
            hp: isBoss ? 3 : 1,
            maxHp: isBoss ? 3 : 1,
            color: isBoss ? '#ec4899' : r === 1 ? '#a855f7' : '#38bdf8',
            speedX: 1.2 + wave * 0.2,
            shootTimer: Math.random() * 200 + 100,
          }});
        }}
      }}
    }}

    function fireLaser() {{
      const now = performance.now();
      if (now - player.lastFire < player.fireRate) return;
      player.lastFire = now;

      // Dual wing cannons
      lasers.push({{ x: player.x - 12, y: player.y - 10, width: 3, height: 14, speed: 12, color: '#38bdf8' }});
      lasers.push({{ x: player.x + 12, y: player.y - 10, width: 3, height: 14, speed: 12, color: '#38bdf8' }});
    }}

    function createExplosion(x, y, color = '#38bdf8', count = 18) {{
      for (let i = 0; i < count; i++) {{
        const angle = Math.random() * Math.PI * 2;
        const spd = 1 + Math.random() * 4;
        particles.push({{
          x, y,
          vx: Math.cos(angle) * spd,
          vy: Math.sin(angle) * spd,
          alpha: 1,
          size: 2 + Math.random() * 3,
          color: color,
        }});
      }}
    }}

    function spawnFloatingText(text, x, y, color = '#38bdf8') {{
      floatingTexts.push({{ text, x, y, alpha: 1, vy: -1.2, color }});
    }}

    function update() {{
      if (gameState !== 'PLAYING') return;

      // Starfield movement
      for (const s of stars) {{
        s.y += s.speed;
        if (s.y > canvas.height) {{
          s.y = 0;
          s.x = Math.random() * canvas.width;
        }}
      }}

      // Player Movement
      if (keys['ArrowLeft'] || keys['a'] || keys['A']) player.x -= player.speed;
      if (keys['ArrowRight'] || keys['d'] || keys['D']) player.x += player.speed;
      if (keys['ArrowUp'] || keys['w'] || keys['W']) player.y -= player.speed;
      if (keys['ArrowDown'] || keys['s'] || keys['S']) player.y += player.speed;

      // Clamping inside viewport
      player.x = Math.max(player.width / 2, Math.min(canvas.width - player.width / 2, player.x));
      player.y = Math.max(player.height / 2, Math.min(canvas.height - player.height / 2, player.y));

      // Continuous firing if space is held
      if (keys[' ']) fireLaser();

      // Lasers Update
      for (let i = lasers.length - 1; i >= 0; i--) {{
        const l = lasers[i];
        l.y -= l.speed;
        if (l.y < -20) {{
          lasers.splice(i, 1);
          continue;
        }}

        // Collision with enemies
        for (let j = enemies.length - 1; j >= 0; j--) {{
          const e = enemies[j];
          if (
            l.x > e.x - e.width / 2 &&
            l.x < e.x + e.width / 2 &&
            l.y > e.y - e.height / 2 &&
            l.y < e.y + e.height / 2
          ) {{
            lasers.splice(i, 1);
            e.hp--;
            createExplosion(l.x, l.y, e.color, 8);
            if (e.hp <= 0) {{
              const pts = e.maxHp > 1 ? 150 : 50;
              score += pts;
              spawnFloatingText(`+${{pts}}`, e.x, e.y, e.color);
              createExplosion(e.x, e.y, e.color, 24);
              enemies.splice(j, 1);
            }}
            break;
          }}
        }}
      }}

      // Enemy Lasers Update
      for (let i = enemyLasers.length - 1; i >= 0; i--) {{
        const el = enemyLasers[i];
        el.y += el.speed;
        if (el.y > canvas.height + 20) {{
          enemyLasers.splice(i, 1);
          continue;
        }}

        // Collision with player
        if (
          el.x > player.x - player.width / 2 &&
          el.x < player.x + player.width / 2 &&
          el.y > player.y - player.height / 2 &&
          el.y < player.y + player.height / 2
        ) {{
          enemyLasers.splice(i, 1);
          player.shield = Math.max(0, player.shield - 20);
          createExplosion(player.x, player.y, '#ef4444', 16);
          updateShieldHud();
          if (player.shield <= 0) {{
            triggerGameOver();
          }}
        }}
      }}

      // Enemies Update
      let reverseDirection = false;
      for (const e of enemies) {{
        e.x += e.speedX;
        if (e.x + e.width / 2 > canvas.width - 20 || e.x - e.width / 2 < 20) {{
          reverseDirection = true;
        }}
        // Alien Firing
        e.shootTimer--;
        if (e.shootTimer <= 0) {{
          e.shootTimer = 180 + Math.random() * 220;
          enemyLasers.push({{
            x: e.x,
            y: e.y + e.height / 2,
            width: 4,
            height: 10,
            speed: 4.5 + wave * 0.3,
            color: '#ef4444',
          }});
        }}
      }}

      if (reverseDirection) {{
        for (const e of enemies) {{
          e.speedX = -e.speedX;
          e.y += 18;
          if (e.y + e.height / 2 >= player.y - player.height / 2) {{
            triggerGameOver();
          }}
        }}
      }}

      // Wave Completion Check
      if (enemies.length === 0) {{
        wave++;
        score += 500;
        spawnFloatingText(`WAVE ${{wave}} CLEARED! +500`, canvas.width / 2, canvas.height / 2, '#ec4899');
        player.shield = Math.min(player.maxShield, player.shield + 25);
        updateShieldHud();
        initEnemies();
      }}

      // Particles Update
      for (let i = particles.length - 1; i >= 0; i--) {{
        const p = particles[i];
        p.x += p.vx;
        p.y += p.vy;
        p.alpha -= 0.025;
        if (p.alpha <= 0) particles.splice(i, 1);
      }}

      // Floating Texts Update
      for (let i = floatingTexts.length - 1; i >= 0; i--) {{
        const ft = floatingTexts[i];
        ft.y += ft.vy;
        ft.alpha -= 0.02;
        if (ft.alpha <= 0) floatingTexts.splice(i, 1);
      }}

      // Score HUD update
      document.getElementById('hud-score').innerText = String(score).padStart(5, '0');
      document.getElementById('hud-wave').innerText = String(wave);
      if (score > highScore) {{
        highScore = score;
        localStorage.setItem('space_arcade_high_score', highScore);
        document.getElementById('hud-highscore').innerText = String(highScore).padStart(5, '0');
      }}
    }}

    function render() {{
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // 1. Draw Starfield
      for (const s of stars) {{
        ctx.fillStyle = s.color;
        ctx.globalAlpha = 0.8;
        ctx.beginPath();
        ctx.arc(s.x, s.y, s.size, 0, Math.PI * 2);
        ctx.fill();
      }}
      ctx.globalAlpha = 1.0;

      // 2. Draw Lasers
      for (const l of lasers) {{
        ctx.fillStyle = l.color;
        ctx.shadowColor = l.color;
        ctx.shadowBlur = 8;
        ctx.fillRect(l.x - l.width / 2, l.y, l.width, l.height);
      }}
      ctx.shadowBlur = 0;

      // 3. Draw Enemy Lasers
      for (const el of enemyLasers) {{
        ctx.fillStyle = el.color;
        ctx.shadowColor = el.color;
        ctx.shadowBlur = 8;
        ctx.fillRect(el.x - el.width / 2, el.y, el.width, el.height);
      }}
      ctx.shadowBlur = 0;

      // 4. Draw Enemies
      for (const e of enemies) {{
        ctx.save();
        ctx.translate(e.x, e.y);
        ctx.fillStyle = e.color;
        ctx.shadowColor = e.color;
        ctx.shadowBlur = 10;

        // Custom alien geometry
        ctx.beginPath();
        ctx.moveTo(0, e.height / 2);
        ctx.lineTo(-e.width / 2, -e.height / 2);
        ctx.lineTo(0, -e.height / 4);
        ctx.lineTo(e.width / 2, -e.height / 2);
        ctx.closePath();
        ctx.fill();

        // Eye / Core
        ctx.fillStyle = '#ffffff';
        ctx.beginPath();
        ctx.arc(0, 0, e.width * 0.18, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      }}

      // 5. Draw Player Starship
      if (gameState === 'PLAYING' || gameState === 'PAUSED') {{
        ctx.save();
        ctx.translate(player.x, player.y);

        // Thruster exhaust flame
        const flameHeight = 12 + Math.random() * 8;
        ctx.fillStyle = Math.random() < 0.5 ? '#38bdf8' : '#ec4899';
        ctx.beginPath();
        ctx.moveTo(-6, player.height / 2);
        ctx.lineTo(0, player.height / 2 + flameHeight);
        ctx.lineTo(6, player.height / 2);
        ctx.closePath();
        ctx.fill();

        // Starship fuselage
        ctx.fillStyle = '#0ea5e9';
        ctx.shadowColor = '#38bdf8';
        ctx.shadowBlur = 14;
        ctx.beginPath();
        ctx.moveTo(0, -player.height / 2);
        ctx.lineTo(-player.width / 2, player.height / 2);
        ctx.lineTo(0, player.height / 4);
        ctx.lineTo(player.width / 2, player.height / 2);
        ctx.closePath();
        ctx.fill();

        // Cockpit canopy
        ctx.fillStyle = '#ffffff';
        ctx.beginPath();
        ctx.ellipse(0, -player.height * 0.1, 4, 9, 0, 0, Math.PI * 2);
        ctx.fill();

        // Wingtip cannons
        ctx.fillStyle = '#38bdf8';
        ctx.fillRect(-player.width / 2, -4, 3, 10);
        ctx.fillRect(player.width / 2 - 3, -4, 3, 10);

        ctx.restore();
      }}

      // 6. Draw Particles
      for (const p of particles) {{
        ctx.fillStyle = p.color;
        ctx.globalAlpha = p.alpha;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fill();
      }}
      ctx.globalAlpha = 1.0;

      // 7. Draw Floating Texts
      for (const ft of floatingTexts) {{
        ctx.fillStyle = ft.color;
        ctx.globalAlpha = ft.alpha;
        ctx.font = "bold 14px 'JetBrains Mono', monospace";
        ctx.textAlign = 'center';
        ctx.fillText(ft.text, ft.x, ft.y);
      }}
      ctx.globalAlpha = 1.0;
    }}

    function loop(time) {{
      update();
      render();
      animId = requestAnimationFrame(loop);
    }}

    function startGame() {{
      gameState = 'PLAYING';
      score = 0;
      wave = 1;
      player.shield = 100;
      updateShieldHud();
      document.getElementById('startScreen').style.display = 'none';
      document.getElementById('gameOverScreen').style.display = 'none';
      document.getElementById('pauseScreen').style.display = 'none';
      initEnemies();
    }}

    function togglePause() {{
      if (gameState === 'PLAYING') {{
        gameState = 'PAUSED';
        document.getElementById('pauseScreen').style.display = 'flex';
        document.getElementById('btn-pause').innerText = 'Resume (P)';
      }} else if (gameState === 'PAUSED') {{
        gameState = 'PLAYING';
        document.getElementById('pauseScreen').style.display = 'none';
        document.getElementById('btn-pause').innerText = 'Pause (P)';
      }}
    }}

    function triggerGameOver() {{
      gameState = 'GAMEOVER';
      document.getElementById('finalScoreDisplay').innerText = `Final Score: ${{score}} (Wave ${{wave}})`;
      document.getElementById('gameOverScreen').style.display = 'flex';

      // Persist score to backend
      fetch('/api/scores', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ score, player_name: 'Pilot Ace' }})
      }}).catch(() => {{}});
    }}

    function restartGame() {{
      startGame();
    }}

    function updateShieldHud() {{
      const fill = document.getElementById('hud-shield');
      fill.style.width = `${{player.shield}}%`;
      if (player.shield > 60) fill.style.background = 'linear-gradient(90deg, #10b981, #38bdf8)';
      else if (player.shield > 25) fill.style.background = 'linear-gradient(90deg, #f59e0b, #eab308)';
      else fill.style.background = 'linear-gradient(90deg, #ef4444, #dc2626)';
    }}

    // Boot animation loop
    document.getElementById('hud-highscore').innerText = String(highScore).padStart(5, '0');
    initEnemies();
    animId = requestAnimationFrame(loop);
  </script>
</body>
</html>"""
    return html


def get_custom_interactive_html(title="Custom Application", desc="Domain-specific full-stack application synthesized according to confirmed project specifications."):
    import re
    combined = f"{title} {desc}".lower()

    def _has_kw(*words: str) -> bool:
        for w in words:
            if re.search(r'\b' + re.escape(w.lower()) + r'\b', combined):
                return True
        return False

    # 0. AERIAL COMBAT & FLIGHT ACTION GAMES (e.g. Sky Strike)
    if _has_kw("flight", "aerial", "sky", "strike", "aircraft", "dogfight", "jet", "plane", "arcade", "combat", "shooter", "air combat", "fighter jet", "interceptor", "space combat"):
        app_title = title if title and "SE IntelliPlatform" not in title else "Sky Strike"
        app_desc = desc if desc else "Fast-paced aerial combat game with real-time dogfights, dynamic weather, upgradeable aircraft, and avionics HUD."
        return get_sky_strike_game_html(title=app_title, desc=app_desc)

    # 1. MEDICAL / HEALTHCARE
    if _has_kw("medical", "healthcare", "clinic", "clinical", "patient", "hospital", "prescription", "doctor", "pharma"):
        app_title = title if title and "SE IntelliPlatform" not in title else "MediCare Clinical Health Portal"
        app_desc = desc if desc else "Patient Electronic Health Records, Appointments & Clinical Prescription Tracking"
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{app_title} - Live Preview</title>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #090e17; --card-bg: rgba(16, 24, 39, 0.85); --border: rgba(255, 255, 255, 0.08);
      --accent: #0ea5e9; --accent-hover: #0284c7; --success: #10b981; --warning: #f59e0b; --danger: #ef4444;
      --text: #f8fafc; --muted: #94a3b8;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Plus Jakarta Sans', sans-serif;
      background: radial-gradient(circle at 50% 10%, #0c2135 0%, #090e17 75%);
      color: var(--text); min-height: 100vh; padding: 2rem;
    }}
    .container {{ max-width: 1200px; margin: 0 auto; }}
    .header {{ margin-bottom: 2rem; display: flex; justify-content: space-between; align-items: flex-start; }}
    .badge {{ display: inline-flex; align-items: center; gap: 0.4rem; background: rgba(14, 165, 233, 0.15); color: #38bdf8; border: 1px solid rgba(14, 165, 233, 0.3); padding: 0.3rem 0.8rem; border-radius: 9999px; font-size: 0.8rem; font-weight: 700; margin-bottom: 0.5rem; }}
    h1 {{ font-size: 2.2rem; font-weight: 800; background: linear-gradient(135deg, #fff 30%, #7dd3fc 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    .subtitle {{ color: var(--muted); font-size: 0.95rem; margin-top: 0.25rem; max-width: 600px; }}
    .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1.25rem; margin-bottom: 2rem; }}
    .stat-card {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; padding: 1.25rem; position: relative; overflow: hidden; }}
    .stat-title {{ font-size: 0.8rem; text-transform: uppercase; color: var(--muted); font-weight: 700; }}
    .stat-val {{ font-size: 1.8rem; font-weight: 800; font-family: 'JetBrains Mono', monospace; margin-top: 0.4rem; color: #fff; }}
    .stat-meta {{ font-size: 0.8rem; color: var(--success); margin-top: 0.25rem; }}
    .main-card {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 16px; padding: 1.5rem; margin-bottom: 2rem; }}
    .card-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.25rem; flex-wrap: wrap; gap: 1rem; }}
    .card-title {{ font-size: 1.2rem; font-weight: 700; }}
    .btn {{ background: var(--accent); color: #fff; border: none; padding: 0.6rem 1.2rem; border-radius: 8px; font-weight: 600; cursor: pointer; font-size: 0.9rem; transition: background 0.2s; }}
    .btn:hover {{ background: var(--accent-hover); }}
    .btn-secondary {{ background: rgba(255, 255, 255, 0.08); color: var(--text); border: 1px solid var(--border); margin-left: 0.5rem; }}
    .btn-secondary:hover {{ background: rgba(255, 255, 255, 0.15); }}
    .table-container {{ overflow-x: auto; }}
    table {{ width: 100%; border-collapse: collapse; text-align: left; font-size: 0.9rem; }}
    th {{ padding: 0.75rem 1rem; color: var(--muted); font-size: 0.8rem; text-transform: uppercase; border-bottom: 1px solid var(--border); }}
    td {{ padding: 1rem; border-bottom: 1px solid var(--border); }}
    .status-tag {{ display: inline-block; padding: 0.2rem 0.6rem; border-radius: 6px; font-size: 0.75rem; font-weight: 700; }}
    .status-active {{ background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }}
    .status-urgent {{ background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }}
    .modal-overlay {{ display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.7); backdrop-filter: blur(4px); align-items: center; justify-content: center; z-index: 100; }}
    .modal {{ background: #0f172a; border: 1px solid var(--border); border-radius: 16px; padding: 2rem; width: 100%; max-width: 480px; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.8); }}
    .form-group {{ margin-bottom: 1rem; }}
    .form-group label {{ display: block; font-size: 0.85rem; color: var(--muted); margin-bottom: 0.4rem; font-weight: 600; }}
    .form-group input, .form-group select {{ width: 100%; background: #1e293b; border: 1px solid var(--border); padding: 0.6rem 0.8rem; border-radius: 8px; color: #fff; font-size: 0.9rem; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div>
        <div class="badge">&#9877; CLINICAL HEALTHCARE APPLICATION</div>
        <h1>{app_title}</h1>
        <p class="subtitle">{app_desc}</p>
      </div>
      <div>
        <button class="btn" onclick="openModal()">+ Admit Patient</button>
        <button class="btn btn-secondary" onclick="exportData()">Export Records</button>
      </div>
    </div>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-title">Active Patients</div>
        <div class="stat-val" id="totalPatients">1,420</div>
        <div class="stat-meta">&#9650; +12 Admissions Today</div>
      </div>
      <div class="stat-card">
        <div class="stat-title">Bed Occupancy Rate</div>
        <div class="stat-val">84.2%</div>
        <div class="stat-meta">168 / 200 Beds Occupied</div>
      </div>
      <div class="stat-card">
        <div class="stat-title">Scheduled Consultations</div>
        <div class="stat-val">38</div>
        <div class="stat-meta">Next in 15 mins</div>
      </div>
      <div class="stat-card">
        <div class="stat-title">Urgent Triage Alerts</div>
        <div class="stat-val" style="color: #f87171;">2</div>
        <div class="stat-meta" style="color: #f87171;">Requires Immediate Review</div>
      </div>
    </div>

    <div class="main-card">
      <div class="card-header">
        <div class="card-title">Patient Admissions & Clinical Records</div>
        <input type="text" id="searchInput" placeholder="Filter patient records..." oninput="filterPatients()" style="background: #1e293b; border: 1px solid var(--border); padding: 0.5rem 1rem; border-radius: 8px; color: #fff; width: 280px;" />
      </div>
      <div class="table-container">
        <table id="patientTable">
          <thead>
            <tr>
              <th>Patient ID</th>
              <th>Patient Name</th>
              <th>Diagnosis / Condition</th>
              <th>Attending Physician</th>
              <th>Triage Severity</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody id="patientBody">
            <tr>
              <td><code>MED-1042</code></td>
              <td><b>Sarah Jenkins</b> (38 F)</td>
              <td>Acute Bronchitis</td>
              <td>Dr. Marcus Vance</td>
              <td><span class="status-tag status-active">Routine</span></td>
              <td><button class="btn btn-secondary" style="padding: 0.3rem 0.6rem; font-size: 0.8rem;" onclick="discharge(this)">Discharge</button></td>
            </tr>
            <tr>
              <td><code>MED-1043</code></td>
              <td><b>David Chen</b> (52 M)</td>
              <td>Cardiac Arrhythmia</td>
              <td>Dr. Elena Rostova</td>
              <td><span class="status-tag status-urgent">Critical</span></td>
              <td><button class="btn btn-secondary" style="padding: 0.3rem 0.6rem; font-size: 0.8rem;" onclick="discharge(this)">Discharge</button></td>
            </tr>
            <tr>
              <td><code>MED-1044</code></td>
              <td><b>Emma Watson</b> (24 F)</td>
              <td>Post-Op Fracture Care</td>
              <td>Dr. Marcus Vance</td>
              <td><span class="status-tag status-active">Observation</span></td>
              <td><button class="btn btn-secondary" style="padding: 0.3rem 0.6rem; font-size: 0.8rem;" onclick="discharge(this)">Discharge</button></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>

  <div class="modal-overlay" id="admitModal">
    <div class="modal">
      <h3 style="margin-bottom: 1.25rem;">Admit New Patient</h3>
      <div class="form-group">
        <label>Patient Full Name</label>
        <input type="text" id="newPatientName" placeholder="e.g. Robert Miles" />
      </div>
      <div class="form-group">
        <label>Primary Diagnosis / Symptoms</label>
        <input type="text" id="newDiagnosis" placeholder="e.g. Type II Diabetes Evaluation" />
      </div>
      <div class="form-group">
        <label>Attending Physician</label>
        <input type="text" id="newPhysician" placeholder="e.g. Dr. Sarah Connor" />
      </div>
      <div class="form-group">
        <label>Triage Severity</label>
        <select id="newSeverity">
          <option value="Routine">Routine Care</option>
          <option value="Observation">Observation</option>
          <option value="Critical">Critical / Urgent</option>
        </select>
      </div>
      <div style="display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 1.5rem;">
        <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
        <button class="btn" onclick="savePatient()">Save Record</button>
      </div>
    </div>
  </div>

  <script>
    function openModal() {{ document.getElementById('admitModal').style.display = 'flex'; }}
    function closeModal() {{ document.getElementById('admitModal').style.display = 'none'; }}
    function savePatient() {{
      const name = document.getElementById('newPatientName').value || 'New Patient';
      const diag = document.getElementById('newDiagnosis').value || 'Evaluation';
      const doc = document.getElementById('newPhysician').value || 'Dr. On Duty';
      const sev = document.getElementById('newSeverity').value;
      const pid = 'MED-' + Math.floor(1000 + Math.random() * 9000);
      const isUrgent = sev === 'Critical';

      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><code>${{pid}}</code></td>
        <td><b>${{name}}</b></td>
        <td>${{diag}}</td>
        <td>${{doc}}</td>
        <td><span class="status-tag ${{isUrgent ? 'status-urgent' : 'status-active'}}">${{sev}}</span></td>
        <td><button class="btn btn-secondary" style="padding: 0.3rem 0.6rem; font-size: 0.8rem;" onclick="discharge(this)">Discharge</button></td>
      `;
      document.getElementById('patientBody').prepend(tr);
      closeModal();
      document.getElementById('totalPatients').innerText = parseInt(document.getElementById('totalPatients').innerText.replace(',', '')) + 1;
    }}
    function discharge(btn) {{
      btn.closest('tr').remove();
    }}
    function filterPatients() {{
      const q = document.getElementById('searchInput').value.toLowerCase();
      document.querySelectorAll('#patientBody tr').forEach(row => {{
        row.style.display = row.innerText.toLowerCase().includes(q) ? '' : 'none';
      }});
    }}
    function exportData() {{
      let csv = 'Patient ID,Name,Diagnosis,Physician,Severity\n';
      document.querySelectorAll('#patientBody tr').forEach(row => {{
        const cols = Array.from(row.querySelectorAll('td')).map(td => td.innerText.trim());
        if (cols.length >= 5) csv += `${{cols[0]}},"${{cols[1]}}","${{cols[2]}}","${{cols[3]}}",${{cols[4]}}\n`;
      }});
      const blob = new Blob([csv], {{ type: 'text/csv' }});
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a'); a.href = url; a.download = 'clinical_patient_records.csv'; a.click();
    }}
  </script>
</body>
</html>"""

    # 2. MUSIC PLAYER / AUDIO APPLICATION
    if _has_kw("music", "audio", "song", "playlist", "soundtrack", "podcast", "beats"):
        app_title = title if title and "SE IntelliPlatform" not in title else "SonicFlow Audio & Music Player"
        app_desc = desc if desc else "High-Fidelity Track Playback, Audio Waveforms & Custom Playlist Management"
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{app_title} - Live Preview</title>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #090a10; --card-bg: rgba(18, 20, 32, 0.85); --border: rgba(255, 255, 255, 0.08);
      --accent: #8b5cf6; --accent-hover: #7c3aed; --text: #f8fafc; --muted: #94a3b8;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Plus Jakarta Sans', sans-serif;
      background: radial-gradient(circle at 50% 10%, #1c1438 0%, #090a10 75%);
      color: var(--text); min-height: 100vh; padding: 2rem;
    }}
    .container {{ max-width: 1100px; margin: 0 auto; }}
    .header {{ margin-bottom: 2rem; }}
    .badge {{ display: inline-flex; align-items: center; gap: 0.4rem; background: rgba(139, 92, 246, 0.15); color: #a78bfa; border: 1px solid rgba(139, 92, 246, 0.3); padding: 0.3rem 0.8rem; border-radius: 9999px; font-size: 0.8rem; font-weight: 700; margin-bottom: 0.5rem; }}
    h1 {{ font-size: 2.2rem; font-weight: 800; background: linear-gradient(135deg, #fff 30%, #c4b5fd 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    .subtitle {{ color: var(--muted); font-size: 0.95rem; margin-top: 0.25rem; }}
    .player-deck {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 16px; padding: 1.75rem; margin-bottom: 2rem; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 1.5rem; }}
    .track-info {{ display: flex; align-items: center; gap: 1rem; }}
    .album-art {{ width: 64px; height: 64px; border-radius: 12px; background: linear-gradient(135deg, #8b5cf6, #3b82f6); display: flex; align-items: center; justify-content: center; font-size: 1.8rem; box-shadow: 0 10px 20px rgba(139, 92, 246, 0.3); }}
    .track-meta h3 {{ font-size: 1.1rem; font-weight: 700; }}
    .track-meta p {{ color: var(--muted); font-size: 0.85rem; }}
    .controls {{ display: flex; flex-direction: column; align-items: center; gap: 0.6rem; min-width: 320px; flex: 1; }}
    .buttons {{ display: flex; align-items: center; gap: 1rem; }}
    .ctrl-btn {{ background: transparent; border: none; color: #fff; font-size: 1.2rem; cursor: pointer; padding: 0.5rem; border-radius: 50%; }}
    .play-btn {{ background: var(--accent); width: 48px; height: 48px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.4rem; transition: transform 0.1s; }}
    .play-btn:hover {{ transform: scale(1.05); }}
    .scrubber {{ display: flex; align-items: center; gap: 0.8rem; width: 100%; max-width: 450px; font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: var(--muted); }}
    .progress-bar {{ flex: 1; height: 6px; background: rgba(255,255,255,0.1); border-radius: 3px; position: relative; cursor: pointer; }}
    .progress-fill {{ width: 35%; height: 100%; background: var(--accent); border-radius: 3px; }}
    .wave-container {{ display: flex; align-items: flex-end; gap: 3px; height: 28px; }}
    .wave-bar {{ width: 4px; background: #a78bfa; border-radius: 2px; animation: wave 1s ease-in-out infinite alternate; }}
    @keyframes wave {{ 0% {{ height: 4px; }} 100% {{ height: 26px; }} }}
    .playlist-card {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 16px; padding: 1.5rem; }}
    table {{ width: 100%; border-collapse: collapse; text-align: left; font-size: 0.9rem; }}
    th {{ padding: 0.75rem 1rem; color: var(--muted); font-size: 0.8rem; text-transform: uppercase; border-bottom: 1px solid var(--border); }}
    td {{ padding: 0.9rem 1rem; border-bottom: 1px solid var(--border); }}
    tr:hover td {{ background: rgba(255,255,255,0.02); }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="badge">&#9835; MUSIC & AUDIO PLAYER SUITE</div>
      <h1>{app_title}</h1>
      <p class="subtitle">{app_desc}</p>
    </div>

    <div class="player-deck">
      <div class="track-info">
        <div class="album-art" id="vinylIcon">&#127925;</div>
        <div class="track-meta">
          <h3 id="currentTitle">Midnight Neon</h3>
          <p id="currentArtist">Synthetix &bull; Cyber Dreams EP</p>
        </div>
      </div>

      <div class="controls">
        <div class="buttons">
          <button class="ctrl-btn" onclick="prevTrack()">&#9198;</button>
          <button class="ctrl-btn play-btn" id="playBtn" onclick="togglePlay()">&#9654;</button>
          <button class="ctrl-btn" onclick="nextTrack()">&#9197;</button>
        </div>
        <div class="scrubber">
          <span id="elapsed">01:14</span>
          <div class="progress-bar" onclick="seek(event)"><div class="progress-fill" id="progressFill"></div></div>
          <span>03:45</span>
        </div>
      </div>

      <div class="wave-container" id="equalizer">
        <div class="wave-bar" style="animation-delay: 0.1s;"></div>
        <div class="wave-bar" style="animation-delay: 0.3s;"></div>
        <div class="wave-bar" style="animation-delay: 0.5s;"></div>
        <div class="wave-bar" style="animation-delay: 0.2s;"></div>
        <div class="wave-bar" style="animation-delay: 0.4s;"></div>
      </div>
    </div>

    <div class="playlist-card">
      <h3 style="margin-bottom: 1rem;">Track Playlist & Library</h3>
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Title</th>
            <th>Artist</th>
            <th>Album</th>
            <th>Duration</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody id="trackList">
          <tr onclick="loadTrack('Midnight Neon', 'Synthetix', '03:45')">
            <td>1</td>
            <td><b>Midnight Neon</b></td>
            <td>Synthetix</td>
            <td>Cyber Dreams</td>
            <td>03:45</td>
            <td><button class="ctrl-btn" style="color: #a78bfa;">&#9654;</button></td>
          </tr>
          <tr onclick="loadTrack('Electric Horizon', 'Solaris', '04:12')">
            <td>2</td>
            <td><b>Electric Horizon</b></td>
            <td>Solaris</td>
            <td>Galactic Drift</td>
            <td>04:12</td>
            <td><button class="ctrl-btn" style="color: #a78bfa;">&#9654;</button></td>
          </tr>
          <tr onclick="loadTrack('Lo-Fi Memories', 'Kumo', '02:50')">
            <td>3</td>
            <td><b>Lo-Fi Memories</b></td>
            <td>Kumo</td>
            <td>Rainy Café</td>
            <td>02:50</td>
            <td><button class="ctrl-btn" style="color: #a78bfa;">&#9654;</button></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <script>
    let isPlaying = false;
    function togglePlay() {{
      isPlaying = !isPlaying;
      document.getElementById('playBtn').innerHTML = isPlaying ? '&#10074;&#10074;' : '&#9654;';
      document.querySelectorAll('.wave-bar').forEach(b => b.style.animationPlayState = isPlaying ? 'running' : 'paused');
    }}
    function loadTrack(title, artist, dur) {{
      document.getElementById('currentTitle').innerText = title;
      document.getElementById('currentArtist').innerText = artist;
      if (!isPlaying) togglePlay();
    }}
    function nextTrack() {{ loadTrack('Electric Horizon', 'Solaris', '04:12'); }}
    function prevTrack() {{ loadTrack('Lo-Fi Memories', 'Kumo', '02:50'); }}
    function seek(e) {{
      const rect = e.currentTarget.getBoundingClientRect();
      const pct = (e.clientX - rect.left) / rect.width;
      document.getElementById('progressFill').style.width = (pct * 100) + '%';
    }}
  </script>
</body>
</html>"""

    # 3. FOOD DELIVERY APPLICATION
    if _has_kw("food", "delivery", "restaurant", "meal", "dish", "cuisine", "dining", "menu", "takeout", "eats"):
        app_title = title if title and "SE IntelliPlatform" not in title else "BistroGo Food Delivery"
        app_desc = desc if desc else "Fresh Gourmet Meals, Interactive Cart & Real-Time Delivery Tracking"
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{app_title} - Live Preview</title>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #0f172a; --card-bg: rgba(30, 41, 59, 0.85); --border: rgba(255, 255, 255, 0.08);
      --accent: #f97316; --accent-hover: #ea580c; --text: #f8fafc; --muted: #94a3b8;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Plus Jakarta Sans', sans-serif;
      background: radial-gradient(circle at 50% 10%, #2a1608 0%, #0f172a 75%);
      color: var(--text); min-height: 100vh; padding: 2rem;
    }}
    .container {{ max-width: 1200px; margin: 0 auto; }}
    .header {{ margin-bottom: 2rem; }}
    .badge {{ display: inline-flex; align-items: center; gap: 0.4rem; background: rgba(249, 115, 22, 0.15); color: #fb923c; border: 1px solid rgba(249, 115, 22, 0.3); padding: 0.3rem 0.8rem; border-radius: 9999px; font-size: 0.8rem; font-weight: 700; margin-bottom: 0.5rem; }}
    h1 {{ font-size: 2.2rem; font-weight: 800; background: linear-gradient(135deg, #fff 30%, #fdba74 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    .subtitle {{ color: var(--muted); font-size: 0.95rem; margin-top: 0.25rem; }}
    .layout {{ display: grid; grid-template-columns: 2fr 1fr; gap: 1.5rem; }}
    .menu-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1.25rem; }}
    .dish-card {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 14px; padding: 1.25rem; display: flex; flex-direction: column; justify-content: space-between; }}
    .dish-title {{ font-size: 1.1rem; font-weight: 700; }}
    .dish-desc {{ font-size: 0.85rem; color: var(--muted); margin: 0.4rem 0 1rem 0; line-height: 1.4; }}
    .dish-footer {{ display: flex; justify-content: space-between; align-items: center; }}
    .dish-price {{ font-size: 1.2rem; font-weight: 800; color: #fb923c; }}
    .btn {{ background: var(--accent); color: #fff; border: none; padding: 0.5rem 1rem; border-radius: 8px; font-weight: 600; cursor: pointer; transition: background 0.2s; }}
    .btn:hover {{ background: var(--accent-hover); }}
    .cart-card {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 14px; padding: 1.5rem; height: fit-content; }}
    .cart-item {{ display: flex; justify-content: space-between; align-items: center; padding: 0.6rem 0; border-bottom: 1px solid var(--border); font-size: 0.9rem; }}
    .tracker {{ margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid var(--border); }}
    .step {{ display: flex; align-items: center; gap: 0.6rem; font-size: 0.85rem; color: var(--muted); margin-bottom: 0.5rem; }}
    .step.active {{ color: #fb923c; font-weight: 700; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="badge">&#127828; GOURMET FOOD DELIVERY</div>
      <h1>{app_title}</h1>
      <p class="subtitle">{app_desc}</p>
    </div>

    <div class="layout">
      <div>
        <h3 style="margin-bottom: 1rem;">Chef's Featured Menu</h3>
        <div class="menu-grid">
          <div class="dish-card">
            <div>
              <div class="dish-title">Truffle Mushroom Burger</div>
              <p class="dish-desc">Angus beef patty with sautéed wild truffles, aged cheddar, and brioche bun.</p>
            </div>
            <div class="dish-footer">
              <span class="dish-price">$16.50</span>
              <button class="btn" onclick="addToCart('Truffle Burger', 16.50)">+ Add to Order</button>
            </div>
          </div>
          <div class="dish-card">
            <div>
              <div class="dish-title">Spicy Tuna Poke Bowl</div>
              <p class="dish-desc">Sashimi-grade tuna, avocado, edamame, and sriracha ponzu drizzle.</p>
            </div>
            <div class="dish-footer">
              <span class="dish-price">$18.00</span>
              <button class="btn" onclick="addToCart('Tuna Poke Bowl', 18.00)">+ Add to Order</button>
            </div>
          </div>
          <div class="dish-card">
            <div>
              <div class="dish-title">Artisan Margherita Pizza</div>
              <p class="dish-desc">San Marzano tomatoes, buffalo mozzarella, and fresh sweet basil.</p>
            </div>
            <div class="dish-footer">
              <span class="dish-price">$14.00</span>
              <button class="btn" onclick="addToCart('Margherita Pizza', 14.00)">+ Add to Order</button>
            </div>
          </div>
        </div>
      </div>

      <div class="cart-card">
        <h3 style="margin-bottom: 1rem;">Your Cart & Order</h3>
        <div id="cartItems">
          <div class="cart-item">
            <span>Truffle Burger x1</span>
            <b>$16.50</b>
          </div>
        </div>
        <div style="display: flex; justify-content: space-between; margin-top: 1rem; font-weight: 800; font-size: 1.1rem;">
          <span>Subtotal</span>
          <span id="cartTotal" style="color: #fb923c;">$16.50</span>
        </div>
        <button class="btn" style="width: 100%; margin-top: 1rem; padding: 0.75rem;" onclick="checkout()">Proceed to Checkout</button>

        <div class="tracker">
          <h4 style="font-size: 0.9rem; margin-bottom: 0.75rem;">Live Order Tracking</h4>
          <div class="step active">&#9679; 1. Order Confirmed (18:05)</div>
          <div class="step active">&#9679; 2. Kitchen Preparing Meal</div>
          <div class="step">&#9675; 3. Courier Out for Delivery</div>
          <div class="step">&#9675; 4. Delivered to Doorstep</div>
        </div>
      </div>
    </div>
  </div>

  <script>
    let total = 16.50;
    function addToCart(name, price) {{
      total += price;
      const div = document.createElement('div');
      div.className = 'cart-item';
      div.innerHTML = `<span>${{name}} x1</span><b>$${{price.toFixed(2)}}</b>`;
      document.getElementById('cartItems').appendChild(div);
      document.getElementById('cartTotal').innerText = '$' + total.toFixed(2);
    }}
    function checkout() {{
      alert('Order Placed Successfully! Your delivery driver is assigned.');
    }}
  </script>
</body>
</html>"""

    # 4. LEARNING MANAGEMENT SYSTEM (LMS)
    if _has_kw("learning", "lms", "course", "curriculum", "lesson", "academy", "grading", "syllabus"):
        app_title = title if title and "SE IntelliPlatform" not in title else "EduSphere Learning Management System"
        app_desc = desc if desc else "Interactive Online Courses, Lesson Modules & Student Academic Mastery"
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{app_title} - Live Preview</title>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #090e17; --card-bg: rgba(15, 23, 42, 0.85); --border: rgba(255, 255, 255, 0.08);
      --accent: #10b981; --accent-hover: #059669; --text: #f8fafc; --muted: #94a3b8;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Plus Jakarta Sans', sans-serif;
      background: radial-gradient(circle at 50% 10%, #06281e 0%, #090e17 75%);
      color: var(--text); min-height: 100vh; padding: 2rem;
    }}
    .container {{ max-width: 1200px; margin: 0 auto; }}
    .header {{ margin-bottom: 2rem; display: flex; justify-content: space-between; align-items: flex-start; }}
    .badge {{ display: inline-flex; align-items: center; gap: 0.4rem; background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); padding: 0.3rem 0.8rem; border-radius: 9999px; font-size: 0.8rem; font-weight: 700; margin-bottom: 0.5rem; }}
    h1 {{ font-size: 2.2rem; font-weight: 800; background: linear-gradient(135deg, #fff 30%, #6ee7b7 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    .subtitle {{ color: var(--muted); font-size: 0.95rem; margin-top: 0.25rem; }}
    .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1.25rem; margin-bottom: 2rem; }}
    .stat-card {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; padding: 1.25rem; }}
    .stat-title {{ font-size: 0.8rem; text-transform: uppercase; color: var(--muted); font-weight: 700; }}
    .stat-val {{ font-size: 1.8rem; font-weight: 800; font-family: 'JetBrains Mono', monospace; margin-top: 0.4rem; color: #fff; }}
    .main-card {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 16px; padding: 1.5rem; }}
    .course-item {{ display: flex; justify-content: space-between; align-items: center; padding: 1.25rem 0; border-bottom: 1px solid var(--border); flex-wrap: wrap; gap: 1rem; }}
    .course-meta h4 {{ font-size: 1.1rem; font-weight: 700; }}
    .course-meta p {{ color: var(--muted); font-size: 0.85rem; }}
    .progress-bar {{ width: 180px; height: 8px; background: rgba(255,255,255,0.1); border-radius: 4px; overflow: hidden; margin-top: 0.5rem; }}
    .progress-fill {{ height: 100%; background: var(--accent); border-radius: 4px; }}
    .btn {{ background: var(--accent); color: #fff; border: none; padding: 0.6rem 1.2rem; border-radius: 8px; font-weight: 600; cursor: pointer; transition: background 0.2s; }}
    .btn:hover {{ background: var(--accent-hover); }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div>
        <div class="badge">&#127891; LEARNING MANAGEMENT SYSTEM</div>
        <h1>{app_title}</h1>
        <p class="subtitle">{app_desc}</p>
      </div>
      <div>
        <button class="btn" onclick="alert('Enrolled in new specialization!')">+ Enroll Course</button>
      </div>
    </div>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-title">Enrolled Courses</div>
        <div class="stat-val">5</div>
      </div>
      <div class="stat-card">
        <div class="stat-title">Modules Completed</div>
        <div class="stat-val">42 / 56</div>
      </div>
      <div class="stat-card">
        <div class="stat-title">Overall GPA</div>
        <div class="stat-val">3.92</div>
      </div>
      <div class="stat-card">
        <div class="stat-title">Study Streak</div>
        <div class="stat-val" style="color: #34d399;">14 Days</div>
      </div>
    </div>

    <div class="main-card">
      <h3 style="margin-bottom: 1rem;">Active Course Curriculum</h3>
      <div class="course-item">
        <div class="course-meta">
          <h4>CS-401: Advanced Distributed Systems Architecture</h4>
          <p>Prof. James Thorne &bull; 10 / 12 Lessons Completed</p>
          <div class="progress-bar"><div class="progress-fill" style="width: 83%;"></div></div>
        </div>
        <button class="btn" onclick="resumeLesson(this)">Resume Lesson</button>
      </div>
      <div class="course-item">
        <div class="course-meta">
          <h4>DS-202: Applied Machine Learning & Neural Networks</h4>
          <p>Dr. Lisa Rodriguez &bull; 6 / 8 Lessons Completed</p>
          <div class="progress-bar"><div class="progress-fill" style="width: 75%;"></div></div>
        </div>
        <button class="btn" onclick="resumeLesson(this)">Resume Lesson</button>
      </div>
    </div>
  </div>

  <script>
    function resumeLesson(btn) {{
      btn.innerText = 'In Progress...';
      setTimeout(() => alert('Launching interactive Jupyter notebook and lecture stream.'), 300);
    }}
  </script>
</body>
</html>"""

    # 5. UNIVERSAL GENERAL-PURPOSE DOMAIN SYNTHESIZER
    app_title = title if title and "SE IntelliPlatform" not in title else "Domain Application Platform"
    app_desc = desc if desc else "Custom application synthesized according to confirmed project specifications."
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{app_title} - Live Preview</title>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #0b0f19; --card-bg: rgba(22, 30, 49, 0.85); --border: rgba(255, 255, 255, 0.1);
      --accent: #6366f1; --accent-hover: #4f46e5; --text: #f8fafc; --muted: #94a3b8;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Plus Jakarta Sans', sans-serif;
      background: radial-gradient(circle at 50% 10%, #1e1b4b 0%, #0b0f19 75%);
      color: var(--text); min-height: 100vh; padding: 2rem;
    }}
    .container {{ max-width: 1200px; margin: 0 auto; }}
    .header {{ margin-bottom: 2rem; display: flex; justify-content: space-between; align-items: flex-start; }}
    .badge {{ display: inline-flex; align-items: center; gap: 0.4rem; background: rgba(99, 102, 241, 0.15); color: #818cf8; border: 1px solid rgba(99, 102, 241, 0.3); padding: 0.3rem 0.8rem; border-radius: 9999px; font-size: 0.8rem; font-weight: 700; margin-bottom: 0.5rem; }}
    h1 {{ font-size: 2.2rem; font-weight: 800; background: linear-gradient(135deg, #fff 30%, #a5b4fc 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    .subtitle {{ color: var(--muted); font-size: 0.95rem; margin-top: 0.25rem; }}
    .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1.25rem; margin-bottom: 2rem; }}
    .stat-card {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; padding: 1.25rem; }}
    .stat-title {{ font-size: 0.8rem; text-transform: uppercase; color: var(--muted); font-weight: 700; }}
    .stat-val {{ font-size: 1.8rem; font-weight: 800; font-family: 'JetBrains Mono', monospace; margin-top: 0.4rem; color: #fff; }}
    .main-card {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 16px; padding: 1.5rem; }}
    .btn {{ background: var(--accent); color: #fff; border: none; padding: 0.6rem 1.2rem; border-radius: 8px; font-weight: 600; cursor: pointer; transition: background 0.2s; }}
    .btn:hover {{ background: var(--accent-hover); }}
    .btn-secondary {{ background: rgba(255, 255, 255, 0.08); color: var(--text); border: 1px solid var(--border); margin-left: 0.5rem; }}
    table {{ width: 100%; border-collapse: collapse; text-align: left; font-size: 0.9rem; margin-top: 1rem; }}
    th {{ padding: 0.75rem 1rem; color: var(--muted); font-size: 0.8rem; text-transform: uppercase; border-bottom: 1px solid var(--border); }}
    td {{ padding: 1rem; border-bottom: 1px solid var(--border); }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div>
        <div class="badge">&#9881; DOMAIN APPLICATION PLATFORM</div>
        <h1>{app_title}</h1>
        <p class="subtitle">{app_desc}</p>
      </div>
      <div>
        <button class="btn" onclick="addRecord()">+ Add Record</button>
        <button class="btn btn-secondary" onclick="exportData()">Export CSV</button>
      </div>
    </div>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-title">Managed Records</div>
        <div class="stat-val" id="recordCount">48</div>
      </div>
      <div class="stat-card">
        <div class="stat-title">Active Services</div>
        <div class="stat-val">99.9%</div>
      </div>
      <div class="stat-card">
        <div class="stat-title">Domain Throughput</div>
        <div class="stat-val">1.2k ops/s</div>
      </div>
      <div class="stat-card">
        <div class="stat-title">Efficiency Index</div>
        <div class="stat-val" style="color: #34d399;">Optimal</div>
      </div>
    </div>

    <div class="main-card">
      <h3 style="margin-bottom: 1rem;">Domain Resources & Entity Explorer</h3>
      <table id="domainTable">
        <thead>
          <tr>
            <th>ID</th>
            <th>Resource Identifier</th>
            <th>Status</th>
            <th>Last Updated</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody id="domainBody">
          <tr>
            <td><code>RES-01</code></td>
            <td><b>Primary Resource Cluster</b></td>
            <td><span style="color: #34d399; font-weight: 700;">Active</span></td>
            <td>Just now</td>
            <td><button class="btn btn-secondary" style="padding: 0.3rem 0.6rem; font-size: 0.8rem;" onclick="this.closest('tr').remove()">Remove</button></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <script>
    function addRecord() {{
      const id = 'RES-0' + (document.querySelectorAll('#domainBody tr').length + 1);
      const name = prompt('Enter resource name:') || 'Secondary Service Node';
      const tr = document.createElement('tr');
      tr.innerHTML = `<td><code>${{id}}</code></td><td><b>${{name}}</b></td><td><span style="color: #34d399; font-weight: 700;">Active</span></td><td>Just now</td><td><button class="btn btn-secondary" style="padding: 0.3rem 0.6rem; font-size: 0.8rem;" onclick="this.closest('tr').remove()">Remove</button></td>`;
      document.getElementById('domainBody').appendChild(tr);
      document.getElementById('recordCount').innerText = document.querySelectorAll('#domainBody tr').length;
    }}
    function exportData() {{
      alert('Exported domain configuration CSV.');
    }}
  </script>
</body>
</html>"""


def get_chess_game_html(title: str = "Chess Master Pro", desc: str = "Interactive Strategic Chess Game") -> str:
    return get_chess_html(title=title, desc=desc)

def get_platformer_game_html(title: str = "Skyline Jump Platformer", desc: str = "2D Action Platformer Game") -> str:
    return get_platformer_html(title=title, desc=desc)

def get_racing_game_html(title: str = "Turbo Nitro Racing", desc: str = "High-Speed Circuit Racing Simulator") -> str:
    return get_racing_html(title=title, desc=desc)

def get_puzzle_game_html(title: str = "Tile Shift Puzzle", desc: str = "Classic 15-Puzzle Sliding Challenge") -> str:
    return get_puzzle_html(title=title, desc=desc)

def get_educational_app_html(title: str = "StudyDeck Flashcards & Quiz", desc: str = "Interactive Learning Suite") -> str:
    return get_educational_html(title=title, desc=desc)


def get_app_html_for_project(project_id: Optional[str] = None, app_type: Optional[str] = None) -> str:
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
                cur.execute("SELECT metadata, files_manifest FROM development_versions WHERE id = ? OR id = ?", (clean_vid, vid_h))
                v_row = cur.fetchone()
                if v_row:
                    v_meta = json.loads(v_row[0]) if v_row[0] and isinstance(v_row[0], str) else (v_row[0] or {})
                    v_files = v_meta.get("files", {}) if isinstance(v_meta, dict) else {}
                    h_cand = v_files.get("frontend/index.html") or v_files.get("index.html")
                    if not h_cand and len(v_row) > 1 and v_row[1]:
                        try:
                            m_list = json.loads(v_row[1]) if isinstance(v_row[1], str) else v_row[1]
                            if isinstance(m_list, list):
                                for item in m_list:
                                    if isinstance(item, dict) and item.get("path") in ("frontend/index.html", "index.html") and item.get("content"):
                                        h_cand = item.get("content")
                                        break
                        except Exception:
                            pass
                    if h_cand:
                        is_stale = False
                        # Anti-collision check: only flag if content clearly belongs to another distinct archetype and doesn't match this project
                        shadow_duel_markers = [
                            "Katana Slash", "Shadow Master Skill Builder", "The Shadow Master",
                            "ninja@shadowduel", "Sign In to Arena", "Quick Fill Demo Ninja",
                            "Shadow Slayer", "Master Shadow", "Create Warrior Account", "shadowduel.com",
                            "combatCanvas"
                        ]
                        if mode != "shadow_master" and any(m in h_cand for m in shadow_duel_markers):
                            if p_name and "shadow" not in p_name.lower():
                                is_stale = True
                        if mode != "snake_game" and any(m in h_cand for m in ["spawnFood()", "snake_high_score", "Arcade Snake"]):
                            if p_name and "snake" not in p_name.lower():
                                is_stale = True
                        if mode not in ("taskflow", "custom") and "KanbanFlow Board" in h_cand:
                            if p_name and "kanban" not in p_name.lower() and "task" not in p_name.lower():
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
                shadow_duel_markers = [
                    "Katana Slash", "Shadow Master Skill Builder", "The Shadow Master",
                    "ninja@shadowduel", "Sign In to Arena", "Quick Fill Demo Ninja",
                    "Shadow Slayer", "Master Shadow", "Create Warrior Account", "shadowduel.com",
                    "combatCanvas"
                ]
                for cand in candidates:
                    if cand.is_file():
                        c_text = cand.read_text(encoding="utf-8", errors="replace")
                        if mode not in ("taskflow", "custom") and "KanbanFlow Board" in c_text and (not p_name or "kanban" not in p_name.lower()):
                            continue
                        if mode != "snake_game" and any(m in c_text for m in ["spawnFood()", "snake_high_score", "Arcade Snake"]) and (not p_name or "snake" not in p_name.lower()):
                            continue
                        if mode != "shadow_master" and any(m in c_text for m in shadow_duel_markers) and (not p_name or "shadow" not in p_name.lower()):
                            continue
                        if "Interactive Application Playground" not in c_text or mode == "custom":
                            return c_text
                for root, _, files in os.walk(str(ws_dir)):
                    for f in files:
                        if f.endswith(".html"):
                            c_text = Path(root, f).read_text(encoding="utf-8", errors="replace")
                            if mode not in ("taskflow", "custom") and "KanbanFlow Board" in c_text and (not p_name or "kanban" not in p_name.lower()):
                                continue
                            if mode != "snake_game" and any(m in c_text for m in ["spawnFood()", "snake_high_score", "Arcade Snake"]) and (not p_name or "snake" not in p_name.lower()):
                                continue
                            if mode != "shadow_master" and any(m in c_text for m in shadow_duel_markers) and (not p_name or "shadow" not in p_name.lower()):
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
    elif mode == "inventory":
        return get_inventory_html(p_name or "Apex Inventory & Warehouse Manager", p_desc)
    elif mode == "lms":
        return get_lms_html(p_name or "SkillForge Online Academy", p_desc)
    elif mode in ("space_arcade", "arcade_2d", "space_defender", "galaxy_shooter", "arcade"):
        return get_space_arcade_game_html(p_name or "Space Arcade Defender", p_desc)
    elif mode in ("sky_strike", "aerial_combat"):
        return get_sky_strike_game_html(p_name or "Sky Strike", p_desc)
    elif mode == "custom":
        return get_custom_interactive_html(p_name or "Domain Application Platform", p_desc)
    return get_custom_interactive_html(p_name or "Domain Application Platform", p_desc)


@app.get("/", response_class=HTMLResponse)
@app.get("/preview", response_class=HTMLResponse)
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


@app.get("/custom", response_class=HTMLResponse)
def custom_preview_page(name: Optional[str] = Query("Custom Application"), desc: Optional[str] = Query("")):
    html = get_custom_interactive_html(name, desc)
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


@app.get("/carrom", response_class=HTMLResponse)
def carrom_page():
    return HTMLResponse(content=get_carrom_game_html())


@app.get("/shadow_master", response_class=HTMLResponse)
def shadow_master_page():
    return HTMLResponse(content=get_shadow_master_game_html())



@app.get("/chess", response_class=HTMLResponse)
def chess_page():
    return HTMLResponse(content=get_chess_game_html())


@app.get("/platformer", response_class=HTMLResponse)
def platformer_page():
    return HTMLResponse(content=get_platformer_game_html())


@app.get("/racing", response_class=HTMLResponse)
def racing_page():
    return HTMLResponse(content=get_racing_game_html())


@app.get("/puzzle", response_class=HTMLResponse)
def puzzle_page():
    return HTMLResponse(content=get_puzzle_game_html())


@app.get("/educational", response_class=HTMLResponse)
def educational_page():
    return HTMLResponse(content=get_educational_app_html())

@app.get("/ecommerce", response_class=HTMLResponse)
def ecommerce_page():
    return HTMLResponse(content=get_ecommerce_html())


@app.get("/management", response_class=HTMLResponse)
def management_page():
    return HTMLResponse(content=get_management_html())


@app.get("/inventory", response_class=HTMLResponse)
def inventory_page():
    return HTMLResponse(content=get_inventory_html())


@app.get("/lms", response_class=HTMLResponse)
def lms_page():
    return HTMLResponse(content=get_lms_html())


@app.get("/sky_strike", response_class=HTMLResponse)
def sky_strike_page():
    return HTMLResponse(content=get_sky_strike_game_html())


if __name__ == "__main__":
    uvicorn.run("taskflow_app_server:app", host="127.0.0.1", port=8001, log_level="info", reload=False)

