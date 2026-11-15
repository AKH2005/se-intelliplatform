"""Structured Internal Application Specification.

Translates natural language project intent and canonical requirements into a
complete, cohesive architectural blueprint with explicit dependencies, workflows,
data entities, backend operations, and UI/UX design systems.
"""

from typing import Any
from pydantic import BaseModel, ConfigDict, Field
from app.agents.code_generation.contracts import (
    ApplicationComplexityLevel,
    classify_application_complexity,
)


class FeatureSpecification(BaseModel):
    """Specification of an application feature with dependency tracking."""
    model_config = ConfigDict(extra="ignore")

    name: str = Field(..., description="Feature title")
    description: str = Field(..., description="Detailed functional capability")
    dependencies: list[str] = Field(default_factory=list, description="Names of prerequisite features")


class UserWorkflowSpecification(BaseModel):
    """End-to-end user workflow mapping dependent user steps and data flow."""
    model_config = ConfigDict(extra="ignore")

    workflow_name: str = Field(..., description="Name of user journey (e.g., 'Order Placement Flow')")
    steps: list[str] = Field(..., description="Ordered sequential user steps")
    data_flow: str = Field(default="", description="Description of data propagation across the steps")


class PageSpecification(BaseModel):
    """Page or view specification with route, title, and key UI components."""
    model_config = ConfigDict(extra="ignore")

    page_id: str
    title: str
    route: str
    icon: str = "Layout"
    components: list[str] = Field(default_factory=list)


class DataEntitySpecification(BaseModel):
    """Data entity schema, fields, relationships, and constraints."""
    model_config = ConfigDict(extra="ignore")

    entity_name: str
    fields: list[dict[str, str]] = Field(default_factory=list)  # {"name": "...", "type": "...", "constraint": "..."}
    relationships: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)


class BackendOperationSpecification(BaseModel):
    """REST API backend operation contract."""
    model_config = ConfigDict(extra="ignore")

    endpoint: str
    method: str
    description: str
    request_model: str | None = None
    response_model: str = "dict"
    validation_rules: list[str] = Field(default_factory=list)


class UIRequirementsSpecification(BaseModel):
    """UI/UX Design system specification tailored to the domain."""
    model_config = ConfigDict(extra="ignore")

    design_system: str
    primary_color: str
    secondary_color: str
    accent_color: str
    background_color: str
    surface_color: str
    font_family: str = "'Plus Jakarta Sans', system-ui, sans-serif"
    code_font_family: str = "'JetBrains Mono', monospace"
    border_radius: str = "12px"
    responsive_breakpoints: dict[str, str] = Field(
        default_factory=lambda: {
            "desktop": "min-width: 1024px",
            "tablet": "768px - 1023px",
            "mobile": "max-width: 767px",
        }
    )


class AuthRequirementsSpecification(BaseModel):
    """Authentication and session verification contract."""
    model_config = ConfigDict(extra="ignore")

    required: bool = False
    auth_type: str = "JWT"
    session_mechanism: str = "Bearer Token"
    roles: list[str] = Field(default_factory=lambda: ["user", "admin"])


class ApplicationSpecification(BaseModel):
    """Comprehensive structured internal specification for application generation."""
    model_config = ConfigDict(extra="ignore")

    purpose: str = Field(..., description="Core mission and objective of the application")
    target_users: list[str] = Field(default_factory=list, description="Intended personas and audiences")
    complexity_level: ApplicationComplexityLevel = Field(default=ApplicationComplexityLevel.MEDIUM)
    archetype: str = Field(default="custom")
    main_features: list[FeatureSpecification] = Field(default_factory=list)
    user_workflows: list[UserWorkflowSpecification] = Field(default_factory=list)
    pages_and_navigation: list[PageSpecification] = Field(default_factory=list)
    data_entities: list[DataEntitySpecification] = Field(default_factory=list)
    backend_operations: list[BackendOperationSpecification] = Field(default_factory=list)
    ui_requirements: UIRequirementsSpecification = Field(
        default_factory=lambda: UIRequirementsSpecification(
            design_system="Modern Enterprise",
            primary_color="#4f46e5",
            secondary_color="#6366f1",
            accent_color="#38bdf8",
            background_color="#0b0f19",
            surface_color="#111827",
        )
    )
    auth_requirements: AuthRequirementsSpecification = Field(default_factory=AuthRequirementsSpecification)
    business_rules: list[str] = Field(default_factory=list)
    validation_rules: list[str] = Field(default_factory=list)


def extract_application_specification(
    name: str = "",
    desc: str = "",
    requirements: list[Any] | None = None,
    archetype_hint: str | None = None,
) -> ApplicationSpecification:
    """Deterministically extracts a complete, structured application specification from project intent."""
    combined = f"{name} {desc}".lower()
    complexity = classify_application_complexity(name, desc, requirements)

    # 1. EVENT MANAGEMENT PLATFORM
    if any(k in combined for k in ["event", "conference", "summit", "meetup", "ticket", "eventhub", "booking"]):
        return ApplicationSpecification(
            purpose="Coordinate conference events, speaker schedules, ticket booking, and seat capacity management.",
            target_users=["Conference Organizers", "Event Attendees", "Keynote Speakers"],
            complexity_level=complexity,
            archetype="eventhub",
            main_features=[
                FeatureSpecification(name="Event Catalog", description="Browse upcoming summits, venues, and schedules", dependencies=[]),
                FeatureSpecification(name="Capacity Tracking", description="Live remaining seat countdown with sold-out gating", dependencies=["Event Catalog"]),
                FeatureSpecification(name="Attendee Registration", description="Register attendees with ticket types and contact validation", dependencies=["Capacity Tracking"]),
                FeatureSpecification(name="Registration Management", description="View confirmed tickets and cancel reservations", dependencies=["Attendee Registration"]),
            ],
            user_workflows=[
                UserWorkflowSpecification(
                    workflow_name="Conference Ticket Booking",
                    steps=["Browse Events Catalog", "Select Event & Check Capacity", "Fill Registration Form", "Receive Confirmation Ticket", "Manage/Cancel Booking"],
                    data_flow="Event selection -> Ticket form -> POST /api/events/{id}/register -> Registration Record created & seats decremented"
                )
            ],
            pages_and_navigation=[
                PageSpecification(page_id="catalog", title="Explore Events", route="/events", icon="Calendar", components=["EventGrid", "SearchBar", "CategoryFilters"]),
                PageSpecification(page_id="bookings", title="My Registrations", route="/registrations", icon="Ticket", components=["RegistrationList", "CancellationModal"]),
                PageSpecification(page_id="analytics", title="Organizer Telemetry", route="/stats", icon="BarChart3", components=["CapacityBar", "RevenueStats"]),
            ],
            data_entities=[
                DataEntitySpecification(
                    entity_name="Event",
                    fields=[
                        {"name": "id", "type": "INTEGER", "constraint": "PRIMARY KEY"},
                        {"name": "title", "type": "TEXT", "constraint": "NOT NULL"},
                        {"name": "date", "type": "TEXT", "constraint": "NOT NULL"},
                        {"name": "venue", "type": "TEXT", "constraint": "NOT NULL"},
                        {"name": "capacity", "type": "INTEGER", "constraint": "NOT NULL"},
                        {"name": "seats_available", "type": "INTEGER", "constraint": "NOT NULL"},
                        {"name": "price", "type": "REAL", "constraint": "DEFAULT 0.0"},
                    ],
                    relationships=["One Event has many Registrations"],
                    constraints=["seats_available >= 0", "seats_available <= capacity"]
                ),
                DataEntitySpecification(
                    entity_name="Registration",
                    fields=[
                        {"name": "id", "type": "INTEGER", "constraint": "PRIMARY KEY"},
                        {"name": "event_id", "type": "INTEGER", "constraint": "FOREIGN KEY (Event.id)"},
                        {"name": "attendee_name", "type": "TEXT", "constraint": "NOT NULL"},
                        {"name": "attendee_email", "type": "TEXT", "constraint": "NOT NULL"},
                        {"name": "ticket_type", "type": "TEXT", "constraint": "DEFAULT 'VIP'"},
                        {"name": "created_at", "type": "TEXT", "constraint": "NOT NULL"},
                    ],
                    relationships=["Belongs to one Event"],
                    constraints=["attendee_email contains '@'"]
                )
            ],
            backend_operations=[
                BackendOperationSpecification(endpoint="/api/events", method="GET", description="List events with search, category, and capacity"),
                BackendOperationSpecification(endpoint="/api/events/{event_id}", method="GET", description="Get single event details"),
                BackendOperationSpecification(endpoint="/api/events/{event_id}/register", method="POST", description="Register attendee and decrement capacity"),
                BackendOperationSpecification(endpoint="/api/registrations", method="GET", description="List confirmed registrations"),
                BackendOperationSpecification(endpoint="/api/events/{event_id}/registration", method="DELETE", description="Cancel attendee registration and release seat"),
            ],
            ui_requirements=UIRequirementsSpecification(
                design_system="EventHub Modern Conference",
                primary_color="#7c3aed",
                secondary_color="#9333ea",
                accent_color="#ec4899",
                background_color="#0a0518",
                surface_color="#140e2b",
            ),
            business_rules=[
                "Cannot register when seats_available == 0 (sold out).",
                "Cancelling a registration immediately increments seats_available.",
                "Duplicate registrations for the same email and event are rejected.",
            ],
            validation_rules=[
                "Attendee name must be at least 2 characters.",
                "Attendee email must be a valid email format.",
            ]
        )

    # 2. INVENTORY MANAGEMENT SYSTEM
    if any(k in combined for k in ["inventory", "warehouse", "stock", "supplier", "sku", "supply chain", "stockflow"]):
        return ApplicationSpecification(
            purpose="Real-time warehouse inventory management, SKU stock tracking, supplier management, and stock adjustment auditing.",
            target_users=["Warehouse Managers", "Procurement Officers", "Inventory Clerks"],
            complexity_level=complexity,
            archetype="inventory",
            main_features=[
                FeatureSpecification(name="SKU Directory", description="Catalog of warehouse products with barcode, category, and stock levels", dependencies=[]),
                FeatureSpecification(name="Stock Level Monitoring", description="Visual stock indicators (In Stock, Low Stock Alert, Out of Stock)", dependencies=["SKU Directory"]),
                FeatureSpecification(name="Stock Adjustments", description="Add or deduct stock with timestamped reason auditing", dependencies=["SKU Directory", "Stock Level Monitoring"]),
                FeatureSpecification(name="Supplier Management", description="Link products to primary suppliers with lead time and restock info", dependencies=["SKU Directory"]),
            ],
            user_workflows=[
                UserWorkflowSpecification(
                    workflow_name="Stock Adjustment & Restock Flow",
                    steps=["Locate SKU via Live Filter", "Inspect Current Stock & Minimum Threshold", "Open Stock Adjustment Dialog", "Enter Quantity (+/-) & Reason", "Verify Updated Stock & Audit Log"],
                    data_flow="Product table -> Select Item -> POST /api/inventory/adjustments -> Stock recalculated, audit row inserted, state persisted"
                )
            ],
            pages_and_navigation=[
                PageSpecification(page_id="stock", title="Inventory Catalog", route="/inventory", icon="Boxes", components=["StockTable", "SearchBar", "CategoryTabs", "KpiBar"]),
                PageSpecification(page_id="adjustments", title="Adjustment Audit Log", route="/adjustments", icon="History", components=["AdjustmentHistoryTable"]),
                PageSpecification(page_id="suppliers", title="Suppliers Directory", route="/suppliers", icon="Truck", components=["SupplierCardGrid"]),
            ],
            data_entities=[
                DataEntitySpecification(
                    entity_name="InventoryProduct",
                    fields=[
                        {"name": "id", "type": "INTEGER", "constraint": "PRIMARY KEY"},
                        {"name": "sku", "type": "TEXT", "constraint": "UNIQUE NOT NULL"},
                        {"name": "name", "type": "TEXT", "constraint": "NOT NULL"},
                        {"name": "category", "type": "TEXT", "constraint": "NOT NULL"},
                        {"name": "current_stock", "type": "INTEGER", "constraint": "NOT NULL DEFAULT 0"},
                        {"name": "min_threshold", "type": "INTEGER", "constraint": "NOT NULL DEFAULT 5"},
                        {"name": "unit_cost", "type": "REAL", "constraint": "NOT NULL"},
                        {"name": "supplier_name", "type": "TEXT", "constraint": "NOT NULL"},
                    ],
                    relationships=["One Product has many StockAdjustments"],
                    constraints=["current_stock >= 0"]
                ),
                DataEntitySpecification(
                    entity_name="StockAdjustment",
                    fields=[
                        {"name": "id", "type": "INTEGER", "constraint": "PRIMARY KEY"},
                        {"name": "product_id", "type": "INTEGER", "constraint": "FOREIGN KEY (InventoryProduct.id)"},
                        {"name": "delta", "type": "INTEGER", "constraint": "NOT NULL"},
                        {"name": "previous_stock", "type": "INTEGER", "constraint": "NOT NULL"},
                        {"name": "new_stock", "type": "INTEGER", "constraint": "NOT NULL"},
                        {"name": "reason", "type": "TEXT", "constraint": "NOT NULL"},
                        {"name": "timestamp", "type": "TEXT", "constraint": "NOT NULL"},
                    ],
                    relationships=["Belongs to InventoryProduct"],
                    constraints=["new_stock == previous_stock + delta"]
                )
            ],
            backend_operations=[
                BackendOperationSpecification(endpoint="/api/inventory/products", method="GET", description="Get product catalog with live stock and filters"),
                BackendOperationSpecification(endpoint="/api/inventory/products/{product_id}", method="GET", description="Get product detail and history"),
                BackendOperationSpecification(endpoint="/api/inventory/adjustments", method="POST", description="Record stock adjustment and update product stock"),
                BackendOperationSpecification(endpoint="/api/inventory/adjustments", method="GET", description="Get chronological adjustment audit log"),
                BackendOperationSpecification(endpoint="/api/inventory/stats", method="GET", description="Get total SKUs, total valuation, and low stock count"),
            ],
            ui_requirements=UIRequirementsSpecification(
                design_system="StockFlow Enterprise Warehouse",
                primary_color="#0d9488",
                secondary_color="#14b8a6",
                accent_color="#f59e0b",
                background_color="#071317",
                surface_color="#0f2329",
            ),
            business_rules=[
                "Stock reduction cannot result in negative stock.",
                "Products below min_threshold are flagged with 'LOW STOCK' badge.",
                "Every stock modification must have an auditable reason recorded.",
            ],
            validation_rules=[
                "Adjustment delta must not be 0.",
                "Reason must be provided (minimum 3 characters).",
            ]
        )

    # 3. LEARNING MANAGEMENT SYSTEM (LMS)
    if any(k in combined for k in ["lms", "course", "lesson", "student", "learn", "academy", "quiz", "education", "edusphere"]):
        return ApplicationSpecification(
            purpose="Comprehensive online learning academy with course curriculum, multimedia lessons, interactive quizzes, and student progress certificates.",
            target_users=["Students", "Instructors", "Corporate Trainees"],
            complexity_level=complexity,
            archetype="lms",
            main_features=[
                FeatureSpecification(name="Course Catalog", description="Explore courses with difficulty tags, instructor profiles, and ratings", dependencies=[]),
                FeatureSpecification(name="Lesson Player", description="Interactive curriculum viewer with syllabus progression and lesson completion", dependencies=["Course Catalog"]),
                FeatureSpecification(name="Interactive Quizzes", description="Multi-question knowledge evaluations with instant scoring and explanations", dependencies=["Lesson Player"]),
                FeatureSpecification(name="Student Progress Tracker", description="Real-time completion percentage, certificate eligibility, and enrollment log", dependencies=["Interactive Quizzes"]),
            ],
            user_workflows=[
                UserWorkflowSpecification(
                    workflow_name="Course Enrollment & Certification Journey",
                    steps=["Browse Academy Course Catalog", "Enroll in Target Course", "Complete Sequential Lessons", "Pass Knowledge Assessment Quiz", "Earn Verified Certificate"],
                    data_flow="Catalog -> Enroll (POST /api/lms/enrollments) -> Lesson study -> Quiz submit (POST /api/lms/quizzes/submit) -> Score tallied & progress updated"
                )
            ],
            pages_and_navigation=[
                PageSpecification(page_id="courses", title="Course Catalog", route="/courses", icon="GraduationCap", components=["CourseGrid", "SearchFilter", "LevelTabs"]),
                PageSpecification(page_id="player", title="Curriculum & Lessons", route="/learn", icon="BookOpen", components=["LessonAccordion", "ContentPane", "CompleteBtn"]),
                PageSpecification(page_id="quiz", title="Interactive Assessment", route="/quiz", icon="HelpCircle", components=["QuizRunner", "ScoreBadge", "ResultModal"]),
                PageSpecification(page_id="progress", title="My Learning Dashboard", route="/dashboard", icon="Award", components=["ProgressRing", "EnrolledCards", "Certificate"]),
            ],
            data_entities=[
                DataEntitySpecification(
                    entity_name="Course",
                    fields=[
                        {"name": "id", "type": "INTEGER", "constraint": "PRIMARY KEY"},
                        {"name": "title", "type": "TEXT", "constraint": "NOT NULL"},
                        {"name": "instructor", "type": "TEXT", "constraint": "NOT NULL"},
                        {"name": "level", "type": "TEXT", "constraint": "DEFAULT 'Intermediate'"},
                        {"name": "duration", "type": "TEXT", "constraint": "NOT NULL"},
                        {"name": "total_lessons", "type": "INTEGER", "constraint": "NOT NULL"},
                    ],
                    relationships=["One Course has many Lessons and Enrollments"],
                    constraints=["total_lessons > 0"]
                ),
                DataEntitySpecification(
                    entity_name="Enrollment",
                    fields=[
                        {"name": "id", "type": "INTEGER", "constraint": "PRIMARY KEY"},
                        {"name": "course_id", "type": "INTEGER", "constraint": "FOREIGN KEY (Course.id)"},
                        {"name": "student_name", "type": "TEXT", "constraint": "NOT NULL"},
                        {"name": "progress_percent", "type": "INTEGER", "constraint": "DEFAULT 0"},
                        {"name": "quiz_score", "type": "INTEGER", "constraint": "DEFAULT 0"},
                        {"name": "is_certified", "type": "BOOLEAN", "constraint": "DEFAULT 0"},
                    ],
                    relationships=["Belongs to Course"],
                    constraints=["progress_percent >= 0 AND progress_percent <= 100"]
                )
            ],
            backend_operations=[
                BackendOperationSpecification(endpoint="/api/lms/courses", method="GET", description="Get academy courses with lessons count and details"),
                BackendOperationSpecification(endpoint="/api/lms/courses/{course_id}", method="GET", description="Get single course syllabus and lessons"),
                BackendOperationSpecification(endpoint="/api/lms/courses/{course_id}/enroll", method="POST", description="Enroll student into course"),
                BackendOperationSpecification(endpoint="/api/lms/quizzes/submit", method="POST", description="Submit quiz answers and compute score"),
                BackendOperationSpecification(endpoint="/api/lms/progress", method="GET", description="Get student enrollment and certificate records"),
            ],
            ui_requirements=UIRequirementsSpecification(
                design_system="EduSphere Modern Academy",
                primary_color="#6366f1",
                secondary_color="#818cf8",
                accent_color="#10b981",
                background_color="#090d16",
                surface_color="#131b2e",
            ),
            business_rules=[
                "Passing score of 70% or higher is required for course certification.",
                "Progress is recalculated upon every completed lesson.",
            ],
            validation_rules=[
                "Student name must be at least 2 characters.",
                "Quiz submission must include responses for all questions.",
            ]
        )

    # 4. E-COMMERCE APPLICATION
    if any(k in combined for k in ["ecommerce", "e-commerce", "shop", "store", "product", "cart", "checkout", "merchandise"]):
        return ApplicationSpecification(
            purpose="Full-stack online shopping destination with categorized product catalog, interactive cart drawer, secure checkout, and order history tracking.",
            target_users=["Shoppers", "Store Admins", "Merchandisers"],
            complexity_level=complexity,
            archetype="ecommerce",
            main_features=[
                FeatureSpecification(name="Product Catalog", description="Categorized product grid with price, rating, stock status, and filters", dependencies=[]),
                FeatureSpecification(name="Product Quick View", description="Detailed modal view with specifications, high-res images, and reviews", dependencies=["Product Catalog"]),
                FeatureSpecification(name="Slide-Out Cart", description="Cart drawer with quantity modifiers, line item subtotals, and checkout button", dependencies=["Product Catalog"]),
                FeatureSpecification(name="Checkout Workflow", description="Multi-step checkout form collecting shipping, calculating tax, and placing orders", dependencies=["Slide-Out Cart"]),
                FeatureSpecification(name="Order History", description="Live order history with tracking status, item breakdowns, and receipt totals", dependencies=["Checkout Workflow"]),
            ],
            user_workflows=[
                UserWorkflowSpecification(
                    workflow_name="E-Commerce Purchase Flow",
                    steps=["Browse Catalog & Filter by Category", "Inspect Product Details", "Add Items to Cart", "Open Cart Drawer & Adjust Quantities", "Complete Checkout Form", "View Order Confirmation & History"],
                    data_flow="Catalog -> Add to Cart -> Cart Drawer -> POST /api/ecommerce/checkout -> Order created in DB, stock deducted, receipt rendered"
                )
            ],
            pages_and_navigation=[
                PageSpecification(page_id="shop", title="Storefront Catalog", route="/products", icon="ShoppingBag", components=["ProductGrid", "CategoryPills", "SortSelector", "CartBadge"]),
                PageSpecification(page_id="orders", title="Order History", route="/orders", icon="Package", components=["OrderHistoryList", "OrderStatusBadge"]),
                PageSpecification(page_id="admin", title="Store Telemetry", route="/admin", icon="TrendingUp", components=["RevenueKpi", "LowStockAlerts"]),
            ],
            data_entities=[
                DataEntitySpecification(
                    entity_name="Product",
                    fields=[
                        {"name": "id", "type": "INTEGER", "constraint": "PRIMARY KEY"},
                        {"name": "name", "type": "TEXT", "constraint": "NOT NULL"},
                        {"name": "category", "type": "TEXT", "constraint": "NOT NULL"},
                        {"name": "price", "type": "REAL", "constraint": "NOT NULL"},
                        {"name": "stock", "type": "INTEGER", "constraint": "NOT NULL DEFAULT 0"},
                        {"name": "description", "type": "TEXT", "constraint": "NOT NULL"},
                    ],
                    relationships=["One Product belongs to many OrderItems"],
                    constraints=["price >= 0.0", "stock >= 0"]
                ),
                DataEntitySpecification(
                    entity_name="Order",
                    fields=[
                        {"name": "id", "type": "INTEGER", "constraint": "PRIMARY KEY"},
                        {"name": "order_number", "type": "TEXT", "constraint": "UNIQUE NOT NULL"},
                        {"name": "customer_name", "type": "TEXT", "constraint": "NOT NULL"},
                        {"name": "email", "type": "TEXT", "constraint": "NOT NULL"},
                        {"name": "total", "type": "REAL", "constraint": "NOT NULL"},
                        {"name": "status", "type": "TEXT", "constraint": "DEFAULT 'PENDING'"},
                        {"name": "created_at", "type": "TEXT", "constraint": "NOT NULL"},
                    ],
                    relationships=["One Order has many OrderItems"],
                    constraints=["total >= 0.0"]
                )
            ],
            backend_operations=[
                BackendOperationSpecification(endpoint="/api/ecommerce/products", method="GET", description="Browse catalog with category, search, and sorting"),
                BackendOperationSpecification(endpoint="/api/ecommerce/products/{product_id}", method="GET", description="Get detailed product record"),
                BackendOperationSpecification(endpoint="/api/ecommerce/checkout", method="POST", description="Submit customer order, deduct stock, persist order record"),
                BackendOperationSpecification(endpoint="/api/ecommerce/orders", method="GET", description="Get chronological order history"),
                BackendOperationSpecification(endpoint="/api/ecommerce/admin/stats", method="GET", description="Get revenue total, order count, and low stock count"),
            ],
            ui_requirements=UIRequirementsSpecification(
                design_system="ShopSphere Modern Retail",
                primary_color="#4f46e5",
                secondary_color="#6366f1",
                accent_color="#10b981",
                background_color="#070a12",
                surface_color="#0e1526",
            ),
            business_rules=[
                "Checkout is blocked if cart is empty.",
                "Purchasing items deducts available stock in real time.",
                "Orders with subtotal over $100 receive free shipping.",
            ],
            validation_rules=[
                "Customer name and valid shipping address are mandatory.",
                "Customer email must be well-formed.",
            ]
        )

    # 5. INTERACTIVE 2D GAME / SIMULATOR
    if any(k in combined for k in ["game", "arcade", "combat", "strike", "simulator", "dogfight", "space", "defender", "battle", "canvas"]):
        return ApplicationSpecification(
            purpose="High-performance 60 FPS HTML5 Canvas arcade action simulator with real-time physics, controls, weapons, HUD telemetry, and persistent high scores.",
            target_users=["Gamers", "Arcade Enthusiasts", "Simulation Players"],
            complexity_level=complexity,
            archetype="custom",
            main_features=[
                FeatureSpecification(name="60 FPS Canvas Game Loop", description="Smooth requestAnimationFrame physics loop with smooth input handling", dependencies=[]),
                FeatureSpecification(name="Tactical Avionics & Weapons", description="Primary rapid-fire cannons, secondary homing missiles, and defensive shields", dependencies=["60 FPS Canvas Game Loop"]),
                FeatureSpecification(name="Enemy Bogeys & AI", description="Enemy ships with behavioral patrol, tracking, and combat evasion", dependencies=["60 FPS Canvas Game Loop"]),
                FeatureSpecification(name="Dynamic Environments", description="Weather and atmospheric modifiers (Clear, Thunderstorm, Night Sortie)", dependencies=["60 FPS Canvas Game Loop"]),
                FeatureSpecification(name="Leaderboard Persistence", description="Persisted score records and rank tracking via backend scores API", dependencies=["60 FPS Canvas Game Loop"]),
            ],
            user_workflows=[
                UserWorkflowSpecification(
                    workflow_name="Interactive Sortie Gameplay Loop",
                    steps=["Review Pilot HUD Telemetry", "Engage Controls (Throttle, Steering, Fire)", "Eliminate Enemy Bogeys & Evade Counterfire", "Upgrade Aircraft in Hangar", "Submit High Score to Leaderboard"],
                    data_flow="Canvas loop -> Keyboard/mouse events -> Collision detection -> Score tally -> POST /api/scores -> Leaderboard persisted"
                )
            ],
            pages_and_navigation=[
                PageSpecification(page_id="arena", title="Combat Simulator Arena", route="/game", icon="Crosshair", components=["SkyStrikeCanvas", "TacticalHud", "HangarUpgradePanel"]),
                PageSpecification(page_id="scores", title="Sortie Leaderboard", route="/scores", icon="Trophy", components=["ScoreLeaderboardTable", "PilotStats"]),
            ],
            data_entities=[
                DataEntitySpecification(
                    entity_name="GameScore",
                    fields=[
                        {"name": "id", "type": "INTEGER", "constraint": "PRIMARY KEY"},
                        {"name": "player_name", "type": "TEXT", "constraint": "NOT NULL"},
                        {"name": "score", "type": "INTEGER", "constraint": "NOT NULL"},
                        {"name": "bogeys_down", "type": "INTEGER", "constraint": "NOT NULL DEFAULT 0"},
                        {"name": "sortie_time", "type": "TEXT", "constraint": "NOT NULL"},
                    ],
                    relationships=[],
                    constraints=["score >= 0"]
                )
            ],
            backend_operations=[
                BackendOperationSpecification(endpoint="/api/scores", method="GET", description="Get high score leaderboard"),
                BackendOperationSpecification(endpoint="/api/scores", method="POST", description="Submit verified pilot score and stats"),
            ],
            ui_requirements=UIRequirementsSpecification(
                design_system="SkyStrike Tactical Cockpit",
                primary_color="#06b6d4",
                secondary_color="#0284c7",
                accent_color="#f59e0b",
                background_color="#050811",
                surface_color="#0a101f",
            ),
            business_rules=[
                "Player health reaching 0 triggers Game Over with final score tally.",
                "Restart button immediately reinitializes the flight arena.",
                "Afterburner boost consumes energy that recharges when not in use.",
            ],
            validation_rules=[
                "Score must be a positive integer.",
                "Player callsight must be between 2 and 20 characters.",
            ]
        )

    # 6. GENERAL / CUSTOM APPLICATION
    return ApplicationSpecification(
        purpose=f"{name} — professional domain application for business data management and workflow productivity.",
        target_users=["Business Professionals", "Operations Teams"],
        complexity_level=complexity,
        archetype="custom",
        main_features=[
            FeatureSpecification(name="Domain Explorer", description="Live searchable data table with filters and CRUD operations", dependencies=[]),
            FeatureSpecification(name="KPI Summary Cards", description="Key performance indicators reflecting real-time business health", dependencies=["Domain Explorer"]),
            FeatureSpecification(name="Item Management Dialog", description="Modal interface to create, validate, and edit domain records", dependencies=["Domain Explorer"]),
        ],
        user_workflows=[
            UserWorkflowSpecification(
                workflow_name="Record Lifecycle",
                steps=["Browse Records", "Filter by Category/Status", "Create or Update Record", "Verify Persistence across Refreshes"],
                data_flow="UI Table -> Modal Action -> REST API -> Database Persistence"
            )
        ],
        pages_and_navigation=[
            PageSpecification(page_id="dashboard", title="Dashboard", route="/dashboard", icon="LayoutDashboard", components=["KpiGrid", "RecordTable", "ActionModal"])
        ],
        data_entities=[
            DataEntitySpecification(
                entity_name="DomainRecord",
                fields=[
                    {"name": "id", "type": "INTEGER", "constraint": "PRIMARY KEY"},
                    {"name": "title", "type": "TEXT", "constraint": "NOT NULL"},
                    {"name": "category", "type": "TEXT", "constraint": "NOT NULL"},
                    {"name": "status", "type": "TEXT", "constraint": "NOT NULL DEFAULT 'ACTIVE'"},
                    {"name": "created_at", "type": "TEXT", "constraint": "NOT NULL"},
                ],
                relationships=[],
                constraints=[]
            )
        ],
        backend_operations=[
            BackendOperationSpecification(endpoint="/api/records", method="GET", description="List records with search and filter"),
            BackendOperationSpecification(endpoint="/api/records", method="POST", description="Create record with validation"),
        ],
        ui_requirements=UIRequirementsSpecification(
            design_system="Modern Enterprise",
            primary_color="#4f46e5",
            secondary_color="#6366f1",
            accent_color="#38bdf8",
            background_color="#0b0f19",
            surface_color="#111827",
        ),
        business_rules=["Records must have non-empty titles."],
        validation_rules=["Title must be at least 2 characters."]
    )
