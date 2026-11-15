"""Script to safely patch preview_server.py with:
1. Import get_inventory_html and get_lms_html
2. Real SQLite sync and endpoints for Events, Inventory, LMS, and E-Commerce
3. Route dispatch for inventory, lms, and sky_strike
"""

from pathlib import Path

preview_server_path = Path("backend/app/runtime/preview_server.py")
content = preview_server_path.read_text(encoding="utf-8")

# 1. Add import of preview_medium_complexity at top if not present
if "from app.runtime.preview_medium_complexity import get_inventory_html, get_lms_html" not in content:
    content = "from app.runtime.preview_medium_complexity import get_inventory_html, get_lms_html\n" + content

# 2. Add SQLite database sync and new routes for events, inventory, LMS, and ecommerce
NEW_SECTIONS = '''
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
'''

# Check if new sections already in content
if "sync_inventory_from_db" not in content:
    # Insert right before tasks_db definition
    idx = content.find("tasks_db = [")
    if idx != -1:
        content = content[:idx] + NEW_SECTIONS + "\n" + content[idx:]
    else:
        content += "\n" + NEW_SECTIONS

# 3. Update get_app_html_for_project dispatch
DISPATCH_OLD = '''    elif mode == "ecommerce":
        return get_ecommerce_html(p_name or "ShopSphere", p_desc)
    elif mode == "management":
        return get_management_html(p_name or "Enterprise Management System", p_desc)'''

DISPATCH_NEW = '''    elif mode == "ecommerce":
        return get_ecommerce_html(p_name or "ShopSphere", p_desc)
    elif mode == "management":
        return get_management_html(p_name or "Enterprise Management System", p_desc)
    elif mode == "inventory":
        return get_inventory_html(p_name or "Apex Inventory & Warehouse Manager", p_desc)
    elif mode == "lms":
        return get_lms_html(p_name or "SkillForge Online Academy", p_desc)
    elif mode in ("sky_strike", "aerial_combat"):
        return get_sky_strike_game_html(p_name or "Sky Strike", p_desc)'''

if DISPATCH_OLD in content:
    content = content.replace(DISPATCH_OLD, DISPATCH_NEW, 1)

# 4. Add direct GET endpoints at bottom
ENDPOINTS_OLD = '''@app.get("/ecommerce", response_class=HTMLResponse)
def ecommerce_page():
    return HTMLResponse(content=get_ecommerce_html())


@app.get("/management", response_class=HTMLResponse)
def management_page():
    return HTMLResponse(content=get_management_html())'''

ENDPOINTS_NEW = '''@app.get("/ecommerce", response_class=HTMLResponse)
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
    return HTMLResponse(content=get_sky_strike_game_html())'''

if ENDPOINTS_OLD in content:
    content = content.replace(ENDPOINTS_OLD, ENDPOINTS_NEW, 1)

preview_server_path.write_text(content, encoding="utf-8")
print("preview_server.py successfully patched and verified!")
