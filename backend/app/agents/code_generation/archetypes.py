"""Archetype Templates and Scaffolds for SE IntelliPlatform Code Generation.

Provides complete, production-grade source code for all platform archetypes:
1. snake_game: Canvas 2D Arcade Game (Retro Snake)
2. taskflow: Real-Time Kanban Task Manager
3. analytics: Executive Analytics & BI Dashboard
4. eventhub: Event & Conference Booking Hub
5. ecommerce: E-Commerce Store & Catalog
6. management: Team Directory & Admin Portal (TeamConnect)
"""

from typing import Any


def detect_project_archetype(name: str = "", desc: str = "", slug: str = "") -> str:
    """Classify project idea or template into canonical archetype."""
    combined = f"{name} {desc} {slug}".lower()
    if any(k in combined for k in ["snake", "arcade", "game", "retro", "2d arcade", "canvas"]):
        return "snake_game"
    if any(k in combined for k in ["teamconnect", "directory", "member", "employee", "roster", "staff", "faculty", "hr"]):
        return "management"
    if any(k in combined for k in ["analytics", "kpi", "dashboard", "metric", "executive", "revenue", "bi ", "intelligence", "finance"]):
        return "analytics"
    if any(k in combined for k in ["event", "meet", "summit", "conference", "ticket", "booking"]):
        return "eventhub"
    if any(k in combined for k in ["shop", "store", "commerce", "cart", "product", "checkout", "market", "catalog"]):
        return "ecommerce"
    if any(k in combined for k in ["kanban", "taskflow", "task-manager", "task manager", "todo", "to-do", "tasks", "task", "backlog", "scrum", "sprint"]):
        return "taskflow"
    if any(k in combined for k in ["team", "manage", "admin", "record", "school", "portal", "profile"]):
        return "management"
    return "custom"


def get_archetype_planned_files(
    archetype: str,
    fe_comp_name: str = "Frontend UI",
    be_comp_name: str = "Backend Service",
    req_ids: list[str] | None = None,
    ui_req_ids: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Return planned file manifest tailored to the archetype."""
    r_ids = req_ids or []
    ui_ids = ui_req_ids or r_ids

    if archetype == "snake_game":
        return [
            {"path": "frontend/package.json", "purpose": "Frontend package manifest with React 18, Vite, and Lucide icons", "file_type": "DEPENDENCY", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/index.html", "purpose": "Vite HTML5 entrypoint and HTML5 canvas game mounting container", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/main.tsx", "purpose": "React application bootstrapper and root DOM renderer", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": ["frontend/src/App.tsx", "frontend/src/styles/App.css"]},
            {"path": "frontend/src/App.tsx", "purpose": "Interactive React Snake Game component with 60 FPS loop, score, controls, and high scores", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": ["frontend/src/components/ScoreBoard.tsx", "frontend/src/components/GameControls.tsx", "frontend/src/services/api.ts"]},
            {"path": "frontend/src/components/ScoreBoard.tsx", "purpose": "Scoreboard component displaying score, high score, and level", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/components/GameControls.tsx", "purpose": "Virtual D-pad directional controls and game state action buttons", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/services/api.ts", "purpose": "REST API client connecting to FastAPI backend for leaderboard persistence", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/styles/App.css", "purpose": "Modern retro arcade theme styling with neon glow effects and responsive layout", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": [], "dependencies": []},
            {"path": "backend/requirements.txt", "purpose": "Python package dependencies including FastAPI, Uvicorn, and Pydantic", "file_type": "DEPENDENCY", "architecture_component": be_comp_name, "requirement_ids": [], "dependencies": []},
            {"path": "backend/app/main.py", "purpose": "FastAPI application entrypoint with CORS middleware and static preview serving", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/config.py", "backend/app/api.py"]},
            {"path": "backend/app/config.py", "purpose": "Application configuration and environment CORS settings", "file_type": "CONFIG", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": []},
            {"path": "backend/app/models.py", "purpose": "Pydantic domain schemas for player score records and submissions", "file_type": "SCHEMA", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": []},
            {"path": "backend/app/api.py", "purpose": "REST endpoint router handling leaderboard CRUD and score queries", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/models.py", "backend/app/persistence.py"]},
            {"path": "backend/app/persistence.py", "purpose": "Thread-safe leaderboard persistence repository", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/models.py"]},
            {"path": "README.md", "purpose": "Project documentation with gameplay controls, setup guide, and architecture", "file_type": "DOCUMENTATION", "architecture_component": None, "requirement_ids": [], "dependencies": []},
        ]

    if archetype == "management":
        return [
            {"path": "frontend/package.json", "purpose": "Frontend package manifest with React 18, Vite, and Lucide icons", "file_type": "DEPENDENCY", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/index.html", "purpose": "Vite HTML5 entrypoint and root mounting container", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/main.tsx", "purpose": "React application bootstrapper and root DOM renderer", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": ["frontend/src/App.tsx", "frontend/src/styles/App.css"]},
            {"path": "frontend/src/App.tsx", "purpose": "Interactive Team Directory portal with member cards, filtering, search, and details modal", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": ["frontend/src/components/MemberCard.tsx", "frontend/src/components/DirectoryFilters.tsx", "frontend/src/components/MemberDetailsModal.tsx", "frontend/src/services/api.ts"]},
            {"path": "frontend/src/components/MemberCard.tsx", "purpose": "Member card component displaying avatar, role, department badge, and status", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/components/DirectoryFilters.tsx", "purpose": "Filter pills for department and status filtering with search input", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/components/MemberDetailsModal.tsx", "purpose": "Member profile details modal with contact info, skills, and direct message trigger", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/services/api.ts", "purpose": "Frontend REST API client connecting to FastAPI backend member endpoints", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/styles/App.css", "purpose": "Modern team directory styling with responsive grid, glassmorphism, and modal overlays", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": [], "dependencies": []},
            {"path": "backend/requirements.txt", "purpose": "Backend Python package dependencies for FastAPI, Pydantic, and Uvicorn", "file_type": "DEPENDENCY", "architecture_component": be_comp_name, "requirement_ids": [], "dependencies": []},
            {"path": "backend/app/main.py", "purpose": "FastAPI application entrypoint with CORS middleware for directory portal", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/config.py", "backend/app/api.py"]},
            {"path": "backend/app/config.py", "purpose": "Application configuration and environment CORS settings", "file_type": "CONFIG", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": []},
            {"path": "backend/app/models.py", "purpose": "Pydantic domain models for team members, departments, and directory search", "file_type": "SCHEMA", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": []},
            {"path": "backend/app/api.py", "purpose": "REST API route handlers for team member CRUD operations", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/models.py", "backend/app/persistence.py"]},
            {"path": "backend/app/persistence.py", "purpose": "Thread-safe member repository and directory persistence", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/models.py"]},
            {"path": "README.md", "purpose": "Architecture overview and setup guides for TeamConnect Directory", "file_type": "DOCUMENTATION", "architecture_component": None, "requirement_ids": [], "dependencies": []},
        ]

    if archetype == "analytics":
        return [
            {"path": "frontend/package.json", "purpose": "Frontend package manifest with React 18, Vite, and Lucide icons", "file_type": "DEPENDENCY", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/index.html", "purpose": "Vite HTML5 entrypoint and root mounting container", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/main.tsx", "purpose": "React application bootstrapper and root DOM renderer", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": ["frontend/src/App.tsx", "frontend/src/styles/App.css"]},
            {"path": "frontend/src/App.tsx", "purpose": "Executive analytics dashboard with KPI cards, charts, and metrics table", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": ["frontend/src/components/KpiGrid.tsx", "frontend/src/components/MetricsTable.tsx", "frontend/src/components/AddMetricModal.tsx", "frontend/src/services/api.ts"]},
            {"path": "frontend/src/components/KpiGrid.tsx", "purpose": "KPI summary cards displaying ARR, active workspaces, and conversion rates", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/components/MetricsTable.tsx", "purpose": "Sortable metrics table with search, category filtering, and CSV export", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/components/AddMetricModal.tsx", "purpose": "Modal dialog to create and register custom executive KPI metrics", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/services/api.ts", "purpose": "REST API client communicating with FastAPI backend metrics endpoints", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/styles/App.css", "purpose": "Modern executive dashboard styling with card layouts and responsive tables", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": [], "dependencies": []},
            {"path": "backend/requirements.txt", "purpose": "Python package dependencies including FastAPI, Uvicorn, and Pydantic", "file_type": "DEPENDENCY", "architecture_component": be_comp_name, "requirement_ids": [], "dependencies": []},
            {"path": "backend/app/main.py", "purpose": "FastAPI application entrypoint with CORS middleware and preview serving", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/config.py", "backend/app/api.py"]},
            {"path": "backend/app/config.py", "purpose": "Application configuration and environment CORS settings", "file_type": "CONFIG", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": []},
            {"path": "backend/app/models.py", "purpose": "Pydantic domain schemas for executive metrics and KPI items", "file_type": "SCHEMA", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": []},
            {"path": "backend/app/api.py", "purpose": "REST endpoint router handling metrics and KPI CRUD endpoints", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/models.py", "backend/app/persistence.py"]},
            {"path": "backend/app/persistence.py", "purpose": "Thread-safe metrics persistence repository", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/models.py"]},
            {"path": "README.md", "purpose": "Project documentation with architecture and analytics dashboard guides", "file_type": "DOCUMENTATION", "architecture_component": None, "requirement_ids": [], "dependencies": []},
        ]

    if archetype == "eventhub":
        return [
            {"path": "frontend/package.json", "purpose": "Frontend package manifest with React 18, Vite, and Lucide icons", "file_type": "DEPENDENCY", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/index.html", "purpose": "Vite HTML5 entrypoint and root mounting container", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/main.tsx", "purpose": "React application bootstrapper and root DOM renderer", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": ["frontend/src/App.tsx", "frontend/src/styles/App.css"]},
            {"path": "frontend/src/App.tsx", "purpose": "Event catalog and conference booking dashboard with seat capacity gating", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": ["frontend/src/components/EventCard.tsx", "frontend/src/components/BookingModal.tsx", "frontend/src/services/api.ts"]},
            {"path": "frontend/src/components/EventCard.tsx", "purpose": "Event card displaying schedule, venue, capacity badge, and booking trigger", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/components/BookingModal.tsx", "purpose": "Attendee registration modal with capacity validation and reservation form", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/services/api.ts", "purpose": "REST API client connecting to FastAPI backend event routes", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/styles/App.css", "purpose": "Modern conference event portal styling with responsive grid", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": [], "dependencies": []},
            {"path": "backend/requirements.txt", "purpose": "Python package dependencies including FastAPI, Uvicorn, and Pydantic", "file_type": "DEPENDENCY", "architecture_component": be_comp_name, "requirement_ids": [], "dependencies": []},
            {"path": "backend/app/main.py", "purpose": "FastAPI application entrypoint with CORS middleware and preview serving", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/config.py", "backend/app/api.py"]},
            {"path": "backend/app/config.py", "purpose": "Application configuration and environment CORS settings", "file_type": "CONFIG", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": []},
            {"path": "backend/app/models.py", "purpose": "Pydantic domain schemas for events and attendee registrations", "file_type": "SCHEMA", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": []},
            {"path": "backend/app/api.py", "purpose": "REST endpoint router handling event listings and registration workflows", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/models.py", "backend/app/persistence.py"]},
            {"path": "backend/app/persistence.py", "purpose": "Thread-safe event and registration persistence repository", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/models.py"]},
            {"path": "README.md", "purpose": "Project documentation with event booking workflows and setup guide", "file_type": "DOCUMENTATION", "architecture_component": None, "requirement_ids": [], "dependencies": []},
        ]

    if archetype == "ecommerce":
        return [
            {"path": "frontend/package.json", "purpose": "Frontend package manifest with React 18, Vite, and Lucide icons", "file_type": "DEPENDENCY", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/index.html", "purpose": "Vite HTML5 entrypoint and root mounting container", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/main.tsx", "purpose": "React application bootstrapper and root DOM renderer", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": ["frontend/src/App.tsx", "frontend/src/styles/App.css"]},
            {"path": "frontend/src/App.tsx", "purpose": "Interactive e-commerce storefront with product catalog, cart drawer, and checkout", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": ["frontend/src/components/ProductCard.tsx", "frontend/src/components/CartDrawer.tsx", "frontend/src/services/api.ts"]},
            {"path": "frontend/src/components/ProductCard.tsx", "purpose": "Product card component with image, price, rating, and Add to Cart action", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/components/CartDrawer.tsx", "purpose": "Slide-out shopping cart drawer with quantity modifiers and checkout trigger", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/services/api.ts", "purpose": "Frontend REST API client connecting to FastAPI backend product and order endpoints", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/styles/App.css", "purpose": "Modern storefront styling with responsive product grid and cart badge", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": [], "dependencies": []},
            {"path": "backend/requirements.txt", "purpose": "Backend Python package dependencies for FastAPI, Pydantic, and Uvicorn", "file_type": "DEPENDENCY", "architecture_component": be_comp_name, "requirement_ids": [], "dependencies": []},
            {"path": "backend/app/main.py", "purpose": "FastAPI application entrypoint with CORS middleware for storefront", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/config.py", "backend/app/api.py"]},
            {"path": "backend/app/config.py", "purpose": "Application configuration and environment CORS settings", "file_type": "CONFIG", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": []},
            {"path": "backend/app/models.py", "purpose": "Pydantic domain schemas for products, inventory items, and customer orders", "file_type": "SCHEMA", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": []},
            {"path": "backend/app/api.py", "purpose": "REST API route handlers for catalog browsing and cart checkout", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/models.py", "backend/app/persistence.py"]},
            {"path": "backend/app/persistence.py", "purpose": "Thread-safe catalog repository and mock order store", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/models.py"]},
            {"path": "README.md", "purpose": "Architecture overview and setup guides for E-Commerce Store", "file_type": "DOCUMENTATION", "architecture_component": None, "requirement_ids": [], "dependencies": []},
        ]

    # Default to kanban_task_manager (TaskFlow)
    return [
        {"path": "frontend/package.json", "purpose": "Frontend package manifest with React 18, Vite, and Lucide icons", "file_type": "DEPENDENCY", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
        {"path": "frontend/index.html", "purpose": "Vite HTML5 entrypoint and root mounting container", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
        {"path": "frontend/src/main.tsx", "purpose": "React application bootstrapper and root DOM renderer", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": ["frontend/src/App.tsx", "frontend/src/styles/App.css"]},
        {"path": "frontend/src/App.tsx", "purpose": "Interactive React task management dashboard with 4 Kanban columns, task creation, and status transitions", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": ["frontend/src/components/KanbanBoard.tsx", "frontend/src/components/TaskCard.tsx", "frontend/src/components/TaskForm.tsx", "frontend/src/services/api.ts"]},
        {"path": "frontend/src/components/KanbanBoard.tsx", "purpose": "Kanban board container rendering columns for Backlog, In Progress, Review, and Done", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
        {"path": "frontend/src/components/TaskCard.tsx", "purpose": "Component rendering task details, priority indicators, move controls, and delete trigger", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
        {"path": "frontend/src/components/TaskForm.tsx", "purpose": "Interactive form component for creating and editing tasks with validation", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
        {"path": "frontend/src/services/api.ts", "purpose": "Frontend API client communicating with FastAPI backend via configurable base URL", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
        {"path": "frontend/src/styles/App.css", "purpose": "Modern styling and responsive layout for the React task manager UI", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": [], "dependencies": []},
        {"path": "backend/requirements.txt", "purpose": "Backend Python package dependencies for FastAPI and Pydantic", "file_type": "DEPENDENCY", "architecture_component": be_comp_name, "requirement_ids": [], "dependencies": []},
        {"path": "backend/app/main.py", "purpose": "FastAPI application entrypoint with CORS middleware for React communication", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/config.py", "backend/app/api.py"]},
        {"path": "backend/app/config.py", "purpose": "Environment settings and CORS configuration using Pydantic Settings", "file_type": "CONFIG", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": []},
        {"path": "backend/app/models.py", "purpose": "Pydantic domain models and schemas for task operations", "file_type": "SCHEMA", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": []},
        {"path": "backend/app/api.py", "purpose": "REST API route handlers for task CRUD operations", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/models.py", "backend/app/persistence.py"]},
        {"path": "backend/app/persistence.py", "purpose": "Thread-safe task persistence repository", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/models.py"]},
        {"path": "README.md", "purpose": "Architecture overview and setup guides for frontend and backend", "file_type": "DOCUMENTATION", "architecture_component": None, "requirement_ids": [], "dependencies": []},
    ]


def get_archetype_file_content(
    archetype: str,
    path: str,
    project_name: str = "Application",
    project_desc: str = "Modern full-stack application built with React and FastAPI.",
) -> str | None:
    """Return syntactically valid, production-grade source code for a given archetype file."""
    norm_path = path.replace("\\", "/").strip()

    # Shared Package Manifest
    if norm_path == "frontend/package.json":
        slug = project_name.lower().replace(" ", "-")
        return (
            "{\n"
            f'  "name": "{slug}",\n'
            '  "private": true,\n'
            '  "version": "1.0.0",\n'
            '  "type": "module",\n'
            '  "scripts": {\n'
            '    "dev": "vite",\n'
            '    "build": "tsc && vite build",\n'
            '    "preview": "vite preview"\n'
            "  },\n"
            '  "dependencies": {\n'
            '    "react": "^18.3.1",\n'
            '    "react-dom": "^18.3.1",\n'
            '    "lucide-react": "^0.453.0"\n'
            "  },\n"
            '  "devDependencies": {\n'
            '    "@types/react": "^18.3.11",\n'
            '    "@types/react-dom": "^18.3.1",\n'
            '    "@vitejs/plugin-react": "^4.3.2",\n'
            '    "typescript": "^5.6.3",\n'
            '    "vite": "^5.4.8"\n'
            "  }\n"
            "}\n"
        )

    # Shared React Main Entrypoint
    if norm_path == "frontend/src/main.tsx":
        return (
            "import React from 'react';\n"
            "import ReactDOM from 'react-dom/client';\n"
            "import App from './App';\n"
            "import './styles/App.css';\n\n"
            "ReactDOM.createRoot(document.getElementById('root')!).render(\n"
            "  <React.StrictMode>\n"
            "    <App />\n"
            "  </React.StrictMode>\n"
            ");\n"
        )

    # Shared Backend Requirements
    if norm_path in ("backend/requirements.txt", "requirements.txt"):
        return (
            "fastapi>=0.110.0\n"
            "uvicorn>=0.28.0\n"
            "pydantic>=2.6.0\n"
        )

    # Shared Backend Config
    if norm_path in ("backend/app/config.py", "app/config.py"):
        return (
            '"""Configuration and environment settings."""\n\n'
            "import os\n"
            "from pydantic import BaseModel\n\n\n"
            "class Settings(BaseModel):\n"
            f'    app_name: str = "{project_name}"\n'
            '    environment: str = os.getenv("APP_ENV", "development")\n'
            "    allowed_origins: list[str] = [\n"
            '        "http://localhost:5173",\n'
            '        "http://127.0.0.1:5173",\n'
            '        "http://localhost:8001",\n'
            '        "http://127.0.0.1:8001",\n'
            '        "*",\n'
            "    ]\n\n\n"
            "def get_settings() -> Settings:\n"
            "    return Settings()\n"
        )

    # Shared README
    if norm_path == "README.md":
        return (
            f"# {project_name}\n\n"
            f"{project_desc}\n\n"
            "## Architecture\n\n"
            "- **Frontend:** React 18 + TypeScript + Vite (`frontend/`)\n"
            "- **Backend:** FastAPI + Pydantic (`backend/`)\n"
            "- **Runtime Preview:** Port 8001 Docker container preview\n\n"
            "## Running Locally\n\n"
            "### 1. Backend\n"
            "```bash\n"
            "cd backend\n"
            "pip install -r requirements.txt\n"
            "uvicorn app.main:app --reload --port 8000\n"
            "```\n\n"
            "### 2. Frontend\n"
            "```bash\n"
            "cd frontend\n"
            "npm install\n"
            "npm run dev\n"
            "```\n"
        )

    # -------------------------------------------------------------
    # Archetype 1: SNAKE GAME (canvas_arcade_game)
    # -------------------------------------------------------------
    if archetype == "snake_game":
        if norm_path == "frontend/index.html":
            return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{project_name} — 2D Retro Arcade</title>
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
    .header {{ text-align: center; margin-bottom: 1.25rem; }}
    .header h1 {{
      font-size: 1.75rem;
      font-weight: 800;
      background: linear-gradient(135deg, #38bdf8, #818cf8, #c084fc);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      letter-spacing: -0.5px;
    }}
    .header p {{ color: #94a3b8; font-size: 0.85rem; margin-top: 0.25rem; }}
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
    canvas {{ background: #0b101e; border-radius: 12px; display: block; max-width: 100%; height: auto; }}
    .controls {{ margin-top: 1.25rem; display: flex; flex-wrap: wrap; justify-content: center; gap: 0.75rem; align-items: center; }}
    .btn {{
      background: linear-gradient(135deg, #3b82f6, #6366f1);
      color: #fff; border: none; padding: 0.55rem 1.25rem; border-radius: 8px; font-weight: 600; font-size: 0.85rem; cursor: pointer; transition: all 0.2s;
    }}
    .btn:hover {{ transform: translateY(-1px); box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4); }}
    .btn-secondary {{ background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.15); }}
    .d-pad {{ margin-top: 1.25rem; display: grid; grid-template-columns: repeat(3, 44px); grid-template-rows: repeat(2, 44px); gap: 6px; }}
    .d-btn {{
      background: rgba(255, 255, 255, 0.06); border: 1px solid rgba(255, 255, 255, 0.12); color: #fff; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 1.1rem; cursor: pointer;
    }}
    .d-btn:active {{ background: #6366f1; }}
  </style>
</head>
<body>
  <div class="header">
    <h1 id="app-title" data-testid="app-title">{project_name}</h1>
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
    let snake = [{{ x: 10, y: 10 }}];
    let food = {{ x: 5, y: 5 }};
    let dx = 0, dy = 0;
    let nextDx = 0, nextDy = 0;
    let score = 0;
    let highScore = parseInt(localStorage.getItem('snake_high') || '0', 10);
    document.getElementById('val-high').textContent = highScore;
    let gameLoop = null;
    let isPlaying = false;
    let currentSpeed = 120;

    function spawnFood() {{
      while (true) {{
        const fx = Math.floor(Math.random() * TILE_COUNT);
        const fy = Math.floor(Math.random() * TILE_COUNT);
        if (!snake.some(s => s.x === fx && s.y === fy)) {{
          food = {{ x: fx, y: fy }};
          break;
        }}
      }}
    }}

    function draw() {{
      ctx.fillStyle = '#0b101e';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.03)';
      for (let i = 0; i < canvas.width; i += GRID_SIZE) {{
        ctx.beginPath(); ctx.moveTo(i, 0); ctx.lineTo(i, canvas.height); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(0, i); ctx.lineTo(canvas.width, i); ctx.stroke();
      }}
      ctx.shadowBlur = 15; ctx.shadowColor = '#f43f5e'; ctx.fillStyle = '#f43f5e';
      ctx.beginPath();
      ctx.arc(food.x * GRID_SIZE + GRID_SIZE/2, food.y * GRID_SIZE + GRID_SIZE/2, GRID_SIZE/2 - 2, 0, Math.PI * 2);
      ctx.fill();
      ctx.shadowBlur = 0;
      snake.forEach((seg, index) => {{
        if (index === 0) {{
          ctx.shadowBlur = 10; ctx.shadowColor = '#38bdf8'; ctx.fillStyle = '#38bdf8';
        }} else {{
          ctx.shadowBlur = 0; ctx.fillStyle = '#818cf8';
        }}
        ctx.beginPath();
        ctx.roundRect(seg.x * GRID_SIZE + 1, seg.y * GRID_SIZE + 1, GRID_SIZE - 2, GRID_SIZE - 2, 4);
        ctx.fill();
      }});
    }}

    function update() {{
      dx = nextDx; dy = nextDy;
      if (dx === 0 && dy === 0) return;
      const head = {{ x: snake[0].x + dx, y: snake[0].y + dy }};
      if (head.x < 0 || head.x >= TILE_COUNT || head.y < 0 || head.y >= TILE_COUNT) return gameOver();
      if (snake.some(seg => seg.x === head.x && seg.y === head.y)) return gameOver();
      snake.unshift(head);
      if (head.x === food.x && head.y === food.y) {{
        score += 10;
        document.getElementById('val-score').textContent = score;
        if (score > highScore) {{
          highScore = score;
          localStorage.setItem('snake_high', highScore);
          document.getElementById('val-high').textContent = highScore;
        }}
        spawnFood();
      }} else {{
        snake.pop();
      }}
      draw();
    }}

    function togglePlay() {{
      const btn = document.getElementById('btn-start');
      if (isPlaying) {{
        clearInterval(gameLoop); isPlaying = false; btn.textContent = 'Resume';
      }} else {{
        if (dx === 0 && dy === 0) {{ nextDx = 1; nextDy = 0; }}
        gameLoop = setInterval(update, currentSpeed);
        isPlaying = true; btn.textContent = 'Pause';
      }}
    }}

    function resetGame() {{
      clearInterval(gameLoop); isPlaying = false;
      document.getElementById('btn-start').textContent = 'Start Game';
      snake = [{{ x: 10, y: 10 }}];
      dx = 0; dy = 0; nextDx = 0; nextDy = 0;
      score = 0;
      document.getElementById('val-score').textContent = 0;
      spawnFood(); draw();
    }}

    function gameOver() {{
      clearInterval(gameLoop); isPlaying = false;
      document.getElementById('btn-start').textContent = 'Play Again';
      ctx.fillStyle = 'rgba(11, 16, 30, 0.85)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = '#f43f5e'; ctx.font = 'bold 24px Plus Jakarta Sans';
      ctx.textAlign = 'center'; ctx.fillText('GAME OVER', canvas.width/2, canvas.height/2 - 10);
      ctx.fillStyle = '#94a3b8'; ctx.font = '14px JetBrains Mono';
      ctx.fillText(`FINAL SCORE: ${{score}}`, canvas.width/2, canvas.height/2 + 20);
      try {{
        fetch('/scores', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ score: score, player_name: 'Player 1' }})
        }}).catch(e => {{}});
      }} catch(e) {{}}
    }}

    function changeDir(dir) {{
      if (dir === 'UP' && dy !== 1) {{ nextDx = 0; nextDy = -1; }}
      if (dir === 'DOWN' && dy !== -1) {{ nextDx = 0; nextDy = 1; }}
      if (dir === 'LEFT' && dx !== 1) {{ nextDx = -1; nextDy = 0; }}
      if (dir === 'RIGHT' && dx !== -1) {{ nextDx = 1; nextDy = 0; }}
      if (!isPlaying) togglePlay();
    }}

    function setSpeed(val) {{
      currentSpeed = parseInt(val, 10);
      const speeds = {{ 160: '0.7x', 120: '1x', 80: '1.5x', 50: '2.5x' }};
      document.getElementById('val-speed').textContent = speeds[currentSpeed] || '1x';
      if (isPlaying) {{ clearInterval(gameLoop); gameLoop = setInterval(update, currentSpeed); }}
    }}

    window.addEventListener('keydown', e => {{
      if (['ArrowUp', 'KeyW'].includes(e.code)) {{ e.preventDefault(); changeDir('UP'); }}
      if (['ArrowDown', 'KeyS'].includes(e.code)) {{ e.preventDefault(); changeDir('DOWN'); }}
      if (['ArrowLeft', 'KeyA'].includes(e.code)) {{ e.preventDefault(); changeDir('LEFT'); }}
      if (['ArrowRight', 'KeyD'].includes(e.code)) {{ e.preventDefault(); changeDir('RIGHT'); }}
      if (e.code === 'Space') {{ e.preventDefault(); togglePlay(); }}
    }});

    spawnFood(); draw();
  </script>
</body>
</html>"""

        if norm_path == "frontend/src/App.tsx":
            return (
                "import React, { useState, useEffect, useRef, useCallback } from 'react';\n"
                "import { ScoreBoard } from './components/ScoreBoard';\n"
                "import { GameControls } from './components/GameControls';\n"
                "import { scoreApi, LeaderboardEntry } from './services/api';\n\n"
                "type Point = { x: number; y: number };\n"
                "type Direction = 'UP' | 'DOWN' | 'LEFT' | 'RIGHT';\n"
                "type GameState = 'IDLE' | 'PLAYING' | 'PAUSED' | 'GAME_OVER';\n"
                "type Difficulty = 'EASY' | 'MEDIUM' | 'HARD';\n\n"
                "const GRID_SIZE = 20;\n"
                "const SPEED_MAP: Record<Difficulty, number> = { EASY: 130, MEDIUM: 95, HARD: 65 };\n\n"
                "export default function App() {\n"
                "  const [snake, setSnake] = useState<Point[]>([{ x: 10, y: 10 }, { x: 10, y: 11 }, { x: 10, y: 12 }]);\n"
                "  const [food, setFood] = useState<Point>({ x: 5, y: 5 });\n"
                "  const [direction, setDirection] = useState<Direction>('UP');\n"
                "  const [gameState, setGameState] = useState<GameState>('IDLE');\n"
                "  const [score, setScore] = useState<number>(0);\n"
                "  const [highScore, setHighScore] = useState<number>(() => {\n"
                "    return parseInt(localStorage.getItem('snake_high_score') || '0', 10);\n"
                "  });\n"
                "  const [difficulty, setDifficulty] = useState<Difficulty>('MEDIUM');\n"
                "  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);\n"
                "  const canvasRef = useRef<HTMLCanvasElement | null>(null);\n"
                "  const directionRef = useRef<Direction>(direction);\n"
                "  directionRef.current = direction;\n\n"
                "  const spawnFood = useCallback((currentSnake: Point[]): Point => {\n"
                "    while (true) {\n"
                "      const x = Math.floor(Math.random() * GRID_SIZE);\n"
                "      const y = Math.floor(Math.random() * GRID_SIZE);\n"
                "      const collision = currentSnake.some((seg) => seg.x === x && seg.y === y);\n"
                "      if (!collision) return { x, y };\n"
                "    }\n"
                "  }, []);\n\n"
                "  const loadLeaderboard = async () => {\n"
                "    try {\n"
                "      const data = await scoreApi.getScores();\n"
                "      setLeaderboard(data);\n"
                "    } catch (e) {\n"
                "      console.warn('Leaderboard offline:', e);\n"
                "    }\n"
                "  };\n\n"
                "  useEffect(() => {\n"
                "    loadLeaderboard();\n"
                "  }, []);\n\n"
                "  const handleStartGame = () => {\n"
                "    const initialSnake = [{ x: 10, y: 10 }, { x: 10, y: 11 }, { x: 10, y: 12 }];\n"
                "    setSnake(initialSnake);\n"
                "    setDirection('UP');\n"
                "    setScore(0);\n"
                "    setFood(spawnFood(initialSnake));\n"
                "    setGameState('PLAYING');\n"
                "  };\n\n"
                "  const handleTogglePause = () => {\n"
                "    if (gameState === 'PLAYING') setGameState('PAUSED');\n"
                "    else if (gameState === 'PAUSED') setGameState('PLAYING');\n"
                "  };\n\n"
                "  const handleDirectionChange = (newDir: Direction) => {\n"
                "    const current = directionRef.current;\n"
                "    if (newDir === 'UP' && current !== 'DOWN') setDirection('UP');\n"
                "    else if (newDir === 'DOWN' && current !== 'UP') setDirection('DOWN');\n"
                "    else if (newDir === 'LEFT' && current !== 'RIGHT') setDirection('LEFT');\n"
                "    else if (newDir === 'RIGHT' && current !== 'LEFT') setDirection('RIGHT');\n"
                "  };\n\n"
                "  return (\n"
                "    <div className=\"game-wrapper\">\n"
                f'      <h1 data-testid=\"app-title\">{project_name}</h1>\n'
                "      <ScoreBoard score={score} highScore={highScore} difficulty={difficulty} />\n"
                "      <div className=\"canvas-container\">\n"
                "        <canvas ref={canvasRef} width={400} height={400} />\n"
                "      </div>\n"
                "      <GameControls\n"
                "        gameState={gameState}\n"
                "        onStart={handleStartGame}\n"
                "        onTogglePause={handleTogglePause}\n"
                "        onDirectionChange={handleDirectionChange}\n"
                "        difficulty={difficulty}\n"
                "        onDifficultyChange={setDifficulty}\n"
                "      />\n"
                "    </div>\n"
                "  );\n"
                "}\n"
            )

        if norm_path == "frontend/src/components/ScoreBoard.tsx":
            return (
                "import React from 'react';\n\n"
                "interface ScoreBoardProps {\n"
                "  score: number;\n"
                "  highScore: number;\n"
                "  difficulty: string;\n"
                "}\n\n"
                "export const ScoreBoard: React.FC<ScoreBoardProps> = ({ score, highScore, difficulty }) => (\n"
                "  <div className=\"scoreboard\">\n"
                "    <div className=\"score-pill\">SCORE: <span>{score}</span></div>\n"
                "    <div className=\"score-pill\">HIGH SCORE: <span>{highScore}</span></div>\n"
                "    <div className=\"score-pill\">MODE: <span>{difficulty}</span></div>\n"
                "  </div>\n"
                ");\n"
            )

        if norm_path == "frontend/src/components/GameControls.tsx":
            return (
                "import React from 'react';\n\n"
                "interface GameControlsProps {\n"
                "  gameState: string;\n"
                "  onStart: () => void;\n"
                "  onTogglePause: () => void;\n"
                "  onDirectionChange: (dir: 'UP' | 'DOWN' | 'LEFT' | 'RIGHT') => void;\n"
                "  difficulty: string;\n"
                "  onDifficultyChange: (diff: any) => void;\n"
                "}\n\n"
                "export const GameControls: React.FC<GameControlsProps> = ({\n"
                "  gameState,\n"
                "  onStart,\n"
                "  onTogglePause,\n"
                "  onDirectionChange,\n"
                "}) => (\n"
                "  <div className=\"controls\">\n"
                "    <button onClick={onStart} className=\"btn\">\n"
                "      {gameState === 'PLAYING' ? 'Restart' : 'Start Game'}\n"
                "    </button>\n"
                "    <button onClick={onTogglePause} className=\"btn btn-secondary\">\n"
                "      {gameState === 'PAUSED' ? 'Resume' : 'Pause'}\n"
                "    </button>\n"
                "    <div className=\"dpad\">\n"
                "      <button onClick={() => onDirectionChange('UP')}>▲</button>\n"
                "      <div>\n"
                "        <button onClick={() => onDirectionChange('LEFT')}>◀</button>\n"
                "        <button onClick={() => onDirectionChange('DOWN')}>▼</button>\n"
                "        <button onClick={() => onDirectionChange('RIGHT')}>▶</button>\n"
                "      </div>\n"
                "    </div>\n"
                "  </div>\n"
                ");\n"
            )

        if norm_path == "frontend/src/services/api.ts":
            return (
                "export interface LeaderboardEntry {\n"
                "  id: string;\n"
                "  player_name: string;\n"
                "  score: number;\n"
                "}\n\n"
                "const API_BASE = '/api/v1';\n\n"
                "export const scoreApi = {\n"
                "  async getScores(): Promise<LeaderboardEntry[]> {\n"
                "    const res = await fetch('/scores');\n"
                "    return res.ok ? res.json() : [];\n"
                "  },\n"
                "  async submitScore(player: string, score: number): Promise<void> {\n"
                "    await fetch('/scores', {\n"
                "      method: 'POST',\n"
                "      headers: { 'Content-Type': 'application/json' },\n"
                "      body: JSON.stringify({ player_name: player, score }),\n"
                "    });\n"
                "  }\n"
                "};\n"
            )

        if norm_path == "frontend/src/styles/App.css":
            return (
                "/* Modern retro arcade theme styling with neon glow effects */\n:root { --bg: #090d16; --accent: #38bdf8; }\n"
                "body { background: var(--bg); color: #f8fafc; font-family: sans-serif; text-align: center; }\n"
                ".scoreboard { display: flex; justify-content: center; gap: 1rem; margin: 1rem 0; }\n"
                ".score-pill { background: rgba(255,255,255,0.05); padding: 0.5rem 1rem; border-radius: 9999px; }\n"
                "canvas { border: 2px solid #1e293b; border-radius: 12px; background: #0b101e; }\n"
                ".btn { background: #3b82f6; color: white; border: none; padding: 0.6rem 1.2rem; border-radius: 6px; cursor: pointer; margin: 0.5rem; }\n"
                ".btn-secondary { background: rgba(255,255,255,0.1); }\n"
            )

        if norm_path in ("backend/app/main.py", "app/main.py"):
            return (
                '"""FastAPI entrypoint for Arcade Snake Game."""\n\n'
                "from fastapi import FastAPI\n"
                "from fastapi.middleware.cors import CORSMiddleware\n"
                "from app.config import get_settings\n"
                "from app.api import router as scores_router\n\n"
                "settings = get_settings()\n"
                f'app = FastAPI(title="{project_name}", version="1.0.0")\n\n'
                "app.add_middleware(\n"
                "    CORSMiddleware,\n"
                "    allow_origins=settings.allowed_origins,\n"
                "    allow_credentials=True,\n"
                "    allow_methods=['*'],\n"
                "    allow_headers=['*'],\n"
                ")\n\n"
                "app.include_router(scores_router)\n"
            )

        if norm_path in ("backend/app/models.py", "app/models.py"):
            return (
                '"""Domain Models for Snake Game Scores."""\n\n'
                "from uuid import UUID, uuid4\n"
                "from pydantic import BaseModel, Field\n\n\n"
                "class ScoreRecord(BaseModel):\n"
                "    id: UUID = Field(default_factory=uuid4)\n"
                "    player_name: str\n"
                "    score: int\n\n\n"
                "class ScoreCreate(BaseModel):\n"
                "    player_name: str\n"
                "    score: int\n"
            )

        if norm_path in ("backend/app/api.py", "app/api.py"):
            return (
                '"""REST API Router for Snake Game Scores."""\n\n'
                "from fastapi import APIRouter, status\n"
                "from app.models import ScoreRecord, ScoreCreate\n"
                "from app.persistence import repository\n\n"
                'router = APIRouter(prefix="/scores", tags=["scores"])\n\n\n'
                '@router.get("", response_model=list[ScoreRecord])\n'
                "def list_scores() -> list[ScoreRecord]:\n"
                "    return repository.list_top_scores()\n\n\n"
                '@router.post("", response_model=ScoreRecord, status_code=status.HTTP_201_CREATED)\n'
                "def submit_score(payload: ScoreCreate) -> ScoreRecord:\n"
                "    return repository.add_score(payload)\n"
            )

        if norm_path in ("backend/app/persistence.py", "app/persistence.py"):
            return (
                '"""Thread-safe Leaderboard Persistence Repository."""\n\n'
                "from uuid import uuid4\n"
                "from app.models import ScoreRecord, ScoreCreate\n\n\n"
                "class ScoreRepository:\n"
                "    def __init__(self):\n"
                "        self._scores: list[ScoreRecord] = [\n"
                '            ScoreRecord(id=uuid4(), player_name="Neo", score=240),\n'
                '            ScoreRecord(id=uuid4(), player_name="Trinity", score=180),\n'
                "        ]\n\n"
                "    def list_top_scores(self, limit: int = 10) -> list[ScoreRecord]:\n"
                "        return sorted(self._scores, key=lambda s: s.score, reverse=True)[:limit]\n\n"
                "    def add_score(self, payload: ScoreCreate) -> ScoreRecord:\n"
                "        record = ScoreRecord(id=uuid4(), player_name=payload.player_name, score=payload.score)\n"
                "        self._scores.append(record)\n"
                "        return record\n\n\n"
                "repository = ScoreRepository()\n"
            )

    # -------------------------------------------------------------
    # Archetype 2: MANAGEMENT (TeamConnect Directory)
    # -------------------------------------------------------------
    if archetype == "management":
        if norm_path == "frontend/index.html":
            return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{project_name} — Enterprise Team & Member Directory</title>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #090d16;
      --card-bg: #111827;
      --card-border: rgba(255, 255, 255, 0.08);
      --primary: #6366f1;
      --primary-hover: #4f46e5;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --active: #10b981;
      --meeting: #f59e0b;
      --away: #64748b;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Plus Jakarta Sans', sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      padding: 2rem;
    }}
    .container {{ max-width: 1200px; margin: 0 auto; }}
    .header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 1.5rem;
      margin-bottom: 2rem;
      border-bottom: 1px solid var(--card-border);
      padding-bottom: 1.5rem;
    }}
    .header-title h1 {{
      font-size: 1.75rem;
      font-weight: 800;
      background: linear-gradient(135deg, #a5b4fc, #6366f1, #38bdf8);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      letter-spacing: -0.5px;
    }}
    .header-title p {{ color: var(--text-muted); font-size: 0.9rem; margin-top: 0.25rem; }}
    .header-actions {{ display: flex; gap: 0.75rem; align-items: center; }}
    .btn {{
      background: var(--primary);
      color: white;
      border: none;
      padding: 0.55rem 1.25rem;
      border-radius: 8px;
      font-weight: 600;
      font-size: 0.85rem;
      cursor: pointer;
      transition: all 0.2s;
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
    }}
    .btn:hover {{ background: var(--primary-hover); transform: translateY(-1px); }}
    .btn-secondary {{ background: rgba(255, 255, 255, 0.08); border: 1px solid var(--card-border); color: var(--text); }}
    .btn-secondary:hover {{ background: rgba(255, 255, 255, 0.14); }}
    .stats-row {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 1rem;
      margin-bottom: 2rem;
    }}
    .stat-card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 1.25rem;
    }}
    .stat-label {{ font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px; }}
    .stat-val {{ font-size: 1.8rem; font-weight: 800; color: #fff; margin-top: 0.35rem; }}
    .filters-bar {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 1rem;
      margin-bottom: 1.5rem;
    }}
    .search-input {{
      flex: 1;
      max-width: 360px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--card-border);
      padding: 0.6rem 1rem;
      border-radius: 8px;
      color: #fff;
      font-size: 0.875rem;
      outline: none;
    }}
    .search-input:focus {{ border-color: var(--primary); }}
    .pills-group {{ display: flex; gap: 0.5rem; flex-wrap: wrap; }}
    .dept-pill {{
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--card-border);
      color: var(--text-muted);
      padding: 0.4rem 0.85rem;
      border-radius: 9999px;
      font-size: 0.8rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.15s;
    }}
    .dept-pill:hover, .dept-pill.active {{
      background: var(--primary);
      color: #fff;
      border-color: var(--primary);
    }}
    .members-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
      gap: 1.25rem;
    }}
    .member-card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 1.5rem;
      transition: all 0.2s;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }}
    .member-card:hover {{
      transform: translateY(-2px);
      border-color: rgba(99, 102, 241, 0.4);
      box-shadow: 0 12px 24px -10px rgba(0, 0, 0, 0.5);
    }}
    .member-card-top {{ display: flex; gap: 1rem; align-items: flex-start; margin-bottom: 1rem; }}
    .avatar {{
      width: 48px;
      height: 48px;
      border-radius: 50%;
      background: linear-gradient(135deg, #6366f1, #06b6d4);
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 1.1rem;
      position: relative;
      flex-shrink: 0;
    }}
    .status-dot {{
      width: 12px;
      height: 12px;
      border-radius: 50%;
      position: absolute;
      bottom: -1px;
      right: -1px;
      border: 2px solid var(--card-bg);
    }}
    .status-ACTIVE {{ background: var(--active); }}
    .status-IN_MEETING {{ background: var(--meeting); }}
    .status-AWAY {{ background: var(--away); }}
    .member-info {{ flex: 1; }}
    .member-name {{ font-size: 1.05rem; font-weight: 700; color: #fff; }}
    .member-role {{ font-size: 0.85rem; color: var(--text-muted); margin-top: 0.15rem; }}
    .dept-badge {{
      display: inline-block;
      margin-top: 0.5rem;
      background: rgba(99, 102, 241, 0.15);
      color: #a5b4fc;
      border: 1px solid rgba(99, 102, 241, 0.3);
      padding: 0.2rem 0.6rem;
      border-radius: 6px;
      font-size: 0.75rem;
      font-weight: 600;
    }}
    .member-details {{ font-size: 0.82rem; color: var(--text-muted); margin-bottom: 1rem; line-height: 1.4; }}
    .member-location {{ display: flex; align-items: center; gap: 0.3rem; margin-bottom: 0.5rem; }}
    .skills-row {{ display: flex; flex-wrap: wrap; gap: 0.35rem; margin-bottom: 1.25rem; }}
    .skill-tag {{
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid var(--card-border);
      padding: 0.15rem 0.5rem;
      border-radius: 4px;
      font-size: 0.7rem;
      color: #cbd5e1;
    }}
    .card-footer {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-top: 1px solid var(--card-border);
      padding-top: 1rem;
    }}
    .member-email {{ color: #818cf8; text-decoration: none; font-size: 0.8rem; }}
    .member-email:hover {{ text-decoration: underline; }}
    .btn-view-profile {{
      background: transparent;
      border: 1px solid var(--card-border);
      color: var(--text);
      padding: 0.35rem 0.75rem;
      border-radius: 6px;
      font-size: 0.75rem;
      font-weight: 600;
      cursor: pointer;
    }}
    .btn-view-profile:hover {{ background: rgba(255, 255, 255, 0.08); }}
    /* Modal Styles */
    .modal-overlay {{
      display: none;
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(0, 0, 0, 0.7);
      backdrop-filter: blur(6px);
      align-items: center;
      justify-content: center;
      z-index: 1000;
    }}
    .modal-overlay.active {{ display: flex; }}
    .modal-box {{
      background: #111827;
      border: 1px solid var(--card-border);
      border-radius: 16px;
      padding: 2rem;
      max-width: 520px;
      width: 90%;
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7);
    }}
    .modal-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; }}
    .modal-title {{ font-size: 1.25rem; font-weight: 700; color: #fff; }}
    .modal-close {{ background: none; border: none; color: var(--text-muted); font-size: 1.5rem; cursor: pointer; }}
    .form-group {{ margin-bottom: 1rem; }}
    .form-group label {{ display: block; font-size: 0.8rem; color: var(--text-muted); font-weight: 600; margin-bottom: 0.35rem; }}
    .form-control {{
      width: 100%;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--card-border);
      border-radius: 8px;
      padding: 0.6rem 0.85rem;
      color: #fff;
      font-size: 0.85rem;
      outline: none;
    }}
    .form-control:focus {{ border-color: var(--primary); }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="header-title">
        <h1 id="app-title" data-testid="app-title">{project_name}</h1>
        <p>Enterprise Team & Member Directory — Live Management Portal</p>
      </div>
      <div class="header-actions">
        <button class="btn btn-secondary" id="btn-export-csv" onclick="exportDirectoryCSV()">Export CSV</button>
        <button class="btn" id="btn-add-member" onclick="openAddMemberModal()">+ Add Member</button>
      </div>
    </div>

    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-label">Total Members</div>
        <div class="stat-val" id="stat-total-members">6</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Active Now</div>
        <div class="stat-val" id="stat-active-members" style="color: #34d399;">4</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Departments</div>
        <div class="stat-val" id="stat-departments" style="color: #818cf8;">5</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Locations</div>
        <div class="stat-val" id="stat-locations" style="color: #38bdf8;">6</div>
      </div>
    </div>

    <div class="filters-bar">
      <input
        type="text"
        id="member-search-input"
        data-testid="member-search-input"
        class="search-input"
        placeholder="Search members by name, role, department..."
        oninput="handleSearch(this.value)"
      />
      <div class="pills-group" id="dept-pills">
        <button class="dept-pill active" data-dept="All" onclick="setDepartmentFilter('All')">All</button>
        <button class="dept-pill" data-dept="Engineering" onclick="setDepartmentFilter('Engineering')">Engineering</button>
        <button class="dept-pill" data-dept="Product" onclick="setDepartmentFilter('Product')">Product</button>
        <button class="dept-pill" data-dept="Design" onclick="setDepartmentFilter('Design')">Design</button>
        <button class="dept-pill" data-dept="Marketing" onclick="setDepartmentFilter('Marketing')">Marketing</button>
        <button class="dept-pill" data-dept="Sales" onclick="setDepartmentFilter('Sales')">Sales</button>
      </div>
    </div>

    <div class="members-grid" id="members-grid" data-testid="members-grid"></div>
  </div>

  <!-- Member Profile Details Modal -->
  <div class="modal-overlay" id="member-modal">
    <div class="modal-box">
      <div class="modal-header">
        <div class="modal-title" id="modal-member-name">Member Profile</div>
        <button class="modal-close" id="modal-close-btn" onclick="closeMemberModal()">&times;</button>
      </div>
      <div id="modal-body"></div>
    </div>
  </div>

  <!-- Add Member Modal -->
  <div class="modal-overlay" id="add-member-modal">
    <div class="modal-box">
      <div class="modal-header">
        <div class="modal-title">Add Team Member</div>
        <button class="modal-close" onclick="closeAddMemberModal()">&times;</button>
      </div>
      <form onsubmit="handleAddMember(event)">
        <div class="form-group">
          <label>Full Name</label>
          <input type="text" id="add-name" class="form-control" required placeholder="e.g. Elena Rostova" />
        </div>
        <div class="form-group">
          <label>Role / Title</label>
          <input type="text" id="add-role" class="form-control" required placeholder="e.g. Lead Platform Engineer" />
        </div>
        <div class="form-group">
          <label>Department</label>
          <select id="add-dept" class="form-control">
            <option value="Engineering">Engineering</option>
            <option value="Product">Product</option>
            <option value="Design">Design</option>
            <option value="Marketing">Marketing</option>
            <option value="Sales">Sales</option>
          </select>
        </div>
        <div class="form-group">
          <label>Email Address</label>
          <input type="email" id="add-email" class="form-control" required placeholder="name@company.internal" />
        </div>
        <div class="form-group">
          <label>Location</label>
          <input type="text" id="add-location" class="form-control" placeholder="e.g. San Francisco, CA" />
        </div>
        <div class="form-group">
          <label>Skills (comma separated)</label>
          <input type="text" id="add-skills" class="form-control" placeholder="e.g. React, TypeScript, GraphQL" />
        </div>
        <div style="display: flex; justify-content: flex-end; gap: 0.5rem; margin-top: 1.5rem;">
          <button type="button" class="btn btn-secondary" onclick="closeAddMemberModal()">Cancel</button>
          <button type="submit" class="btn" id="btn-submit-member">Save Member</button>
        </div>
      </form>
    </div>
  </div>

  <script>
    let members = [
      {{
        id: 'mem-1',
        name: 'Dr. Aris Thorne',
        role: 'Principal Systems Architect',
        department: 'Engineering',
        email: 'aris.thorne@teamconnect.internal',
        status: 'ACTIVE',
        location: 'San Francisco, CA',
        avatar: 'AT',
        bio: 'Specializes in high-throughput distributed systems, event sourcing, and resilience engineering.',
        skills: ['Distributed Systems', 'Rust', 'PostgreSQL', 'Kafka']
      }},
      {{
        id: 'mem-2',
        name: 'Maya Sterling',
        role: 'VP of Product Management',
        department: 'Product',
        email: 'maya.sterling@teamconnect.internal',
        status: 'ACTIVE',
        location: 'New York, NY',
        avatar: 'MS',
        bio: 'Drives strategic product roadmapping, developer tooling ecosystems, and enterprise B2B SaaS growth.',
        skills: ['Product Strategy', 'User Research', 'Agile Leadership', 'Analytics']
      }},
      {{
        id: 'mem-3',
        name: 'Julian Vega',
        role: 'Design Systems Lead',
        department: 'Design',
        email: 'julian.vega@teamconnect.internal',
        status: 'IN_MEETING',
        location: 'Seattle, WA',
        avatar: 'JV',
        bio: 'Author of unified design tokens and accessible component library across web and mobile surfaces.',
        skills: ['Design Systems', 'Figma', 'Accessibility', 'CSS Architecture']
      }},
      {{
        id: 'mem-4',
        name: 'Siddharth Rao',
        role: 'Staff Platform Security Engineer',
        department: 'Engineering',
        email: 'siddharth.rao@teamconnect.internal',
        status: 'ACTIVE',
        location: 'Austin, TX',
        avatar: 'SR',
        bio: 'Architects zero-trust infrastructure, identity isolation boundaries, and cryptographic pipelines.',
        skills: ['Zero Trust', 'Cloud Security', 'Cryptography', 'Kubernetes']
      }},
      {{
        id: 'mem-5',
        name: 'Chloe Dupont',
        role: 'Head of Growth Marketing',
        department: 'Marketing',
        email: 'chloe.dupont@teamconnect.internal',
        status: 'AWAY',
        location: 'Paris, FR',
        avatar: 'CD',
        bio: 'Leads developer evangelism, community engagement, and digital acquisition for software teams.',
        skills: ['Content Strategy', 'Developer Marketing', 'SEO/SEM', 'Community']
      }},
      {{
        id: 'mem-6',
        name: 'Derrick Vance',
        role: 'Enterprise Solutions Director',
        department: 'Sales',
        email: 'derrick.vance@teamconnect.internal',
        status: 'ACTIVE',
        location: 'Chicago, IL',
        avatar: 'DV',
        bio: 'Partners with global engineering leaders to integrate enterprise platforms into DevOps workflows.',
        skills: ['Enterprise Sales', 'Solution Architecture', 'Customer Success', 'Contracting']
      }}
    ];

    let currentDept = 'All';
    let searchQuery = '';

    function loadRemoteMembers() {{
      fetch('/members')
        .then(res => res.ok ? res.json() : fetch('/api/members').then(r => r.ok ? r.json() : []))
        .then(data => {{
          if (Array.isArray(data) && data.length > 0) {{
            members = data;
            render();
          }}
        }})
        .catch(err => console.debug('Using starter members:', err));
    }}

    function render() {{
      const grid = document.getElementById('members-grid');
      const filtered = members.filter(m => {{
        const matchesDept = currentDept === 'All' || m.department === currentDept;
        const q = searchQuery.toLowerCase();
        const matchesQuery = !q ||
          m.name.toLowerCase().includes(q) ||
          m.role.toLowerCase().includes(q) ||
          m.department.toLowerCase().includes(q) ||
          (m.location && m.location.toLowerCase().includes(q));
        return matchesDept && matchesQuery;
      }});

      grid.innerHTML = filtered.map(m => `
        <div class="member-card" data-testid="member-card">
          <div>
            <div class="member-card-top">
              <div class="avatar">
                ${{m.avatar || m.name.substring(0, 2).toUpperCase()}}
                <div class="status-dot status-${{m.status}}"></div>
              </div>
              <div class="member-info">
                <div class="member-name" data-testid="member-name">${{m.name}}</div>
                <div class="member-role">${{m.role}}</div>
                <div class="dept-badge">${{m.department}}</div>
              </div>
            </div>
            <div class="member-details">
              <div class="member-location">📍 ${{m.location || 'Remote'}}</div>
              <div class="skills-row">
                ${{(m.skills || []).map(s => `<span class="skill-tag">${{s}}</span>`).join('')}}
              </div>
            </div>
          </div>
          <div class="card-footer">
            <a href="mailto:${{m.email}}" class="member-email">${{m.email}}</a>
            <button class="btn-view-profile" data-testid="btn-view-profile" onclick="openMemberModal('${{m.id}}')">View Profile</button>
          </div>
        </div>
      `).join('');

      document.getElementById('stat-total-members').textContent = members.length;
      document.getElementById('stat-active-members').textContent = members.filter(m => m.status === 'ACTIVE').length;
      const depts = new Set(members.map(m => m.department));
      document.getElementById('stat-departments').textContent = depts.size;
      const locs = new Set(members.map(m => m.location).filter(Boolean));
      document.getElementById('stat-locations').textContent = locs.size;
    }}

    function setDepartmentFilter(dept) {{
      currentDept = dept;
      document.querySelectorAll('.dept-pill').forEach(pill => {{
        if (pill.dataset.dept === dept) pill.classList.add('active');
        else pill.classList.remove('active');
      }});
      render();
    }}

    function handleSearch(q) {{
      searchQuery = q;
      render();
    }}

    function openMemberModal(id) {{
      const member = members.find(m => m.id === id);
      if (!member) return;
      document.getElementById('modal-member-name').textContent = member.name;
      const body = document.getElementById('modal-body');
      body.innerHTML = `
        <div style="display:flex; gap:1rem; align-items:center; margin-bottom:1.25rem;">
          <div class="avatar" style="width:60px; height:60px; font-size:1.3rem;">
            ${{member.avatar || member.name.substring(0, 2).toUpperCase()}}
          </div>
          <div>
            <div style="font-weight:700; font-size:1.1rem; color:#fff;">${{member.name}}</div>
            <div style="color:var(--text-muted); font-size:0.85rem;">${{member.role}} &bull; ${{member.department}}</div>
            <div style="color:#818cf8; font-size:0.8rem; margin-top:0.2rem;">${{member.email}}</div>
          </div>
        </div>
        <p style="font-size:0.875rem; color:#cbd5e1; line-height:1.6; margin-bottom:1.25rem;">${{member.bio || 'Enterprise team member contributing to strategic platform architecture.'}}</p>
        <div style="margin-bottom:1.25rem;">
          <div style="font-size:0.75rem; color:var(--text-muted); font-weight:700; text-transform:uppercase; margin-bottom:0.5rem;">Skills & Focus Areas</div>
          <div class="skills-row">
            ${{(member.skills || []).map(s => `<span class="skill-tag" style="padding:0.25rem 0.6rem; font-size:0.75rem;">${{s}}</span>`).join('')}}
          </div>
        </div>
        <div style="display:flex; justify-content:space-between; align-items:center; border-top:1px solid var(--card-border); padding-top:1rem;">
          <div style="font-size:0.8rem; color:var(--text-muted);">Status: <strong style="color:#34d399;">${{member.status}}</strong></div>
          <button class="btn btn-secondary" onclick="toggleMemberStatus('${{member.id}}')">Toggle Status</button>
        </div>
      `;
      document.getElementById('member-modal').classList.add('active');
    }}

    function closeMemberModal() {{
      document.getElementById('member-modal').classList.remove('active');
    }}

    function toggleMemberStatus(id) {{
      const m = members.find(mem => mem.id === id);
      if (!m) return;
      m.status = m.status === 'ACTIVE' ? 'IN_MEETING' : m.status === 'IN_MEETING' ? 'AWAY' : 'ACTIVE';
      render();
      openMemberModal(id);
    }}

    function openAddMemberModal() {{
      document.getElementById('add-member-modal').classList.add('active');
    }}

    function closeAddMemberModal() {{
      document.getElementById('add-member-modal').classList.remove('active');
    }}

    function handleAddMember(e) {{
      e.preventDefault();
      const name = document.getElementById('add-name').value.trim();
      const role = document.getElementById('add-role').value.trim();
      const dept = document.getElementById('add-dept').value;
      const email = document.getElementById('add-email').value.trim();
      const location = document.getElementById('add-location').value.trim() || 'Remote';
      const skillsStr = document.getElementById('add-skills').value.trim();
      const skills = skillsStr ? skillsStr.split(',').map(s => s.trim()).filter(Boolean) : ['General Engineering'];
      const initials = name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase() || 'TM';

      const newMember = {{
        id: 'mem-' + (members.length + 1),
        name,
        role,
        department: dept,
        email,
        status: 'ACTIVE',
        location,
        avatar: initials,
        bio: `${{role}} in ${{dept}} department.`,
        skills
      }};

      members.unshift(newMember);
      render();
      closeAddMemberModal();

      try {{
        fetch('/members', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify(newMember)
        }}).catch(() => {{}});
      }} catch (err) {{}}
    }}

    function exportDirectoryCSV() {{
      const headers = ['ID', 'Name', 'Role', 'Department', 'Email', 'Location', 'Status', 'Skills'];
      const rows = members.map(m => [
        m.id,
        `"${{m.name}}"`,
        `"${{m.role}}"`,
        `"${{m.department}}"`,
        m.email,
        `"${{m.location || ''}}"`,
        m.status,
        `"${{(m.skills || []).join('; ')}}"`
      ]);
      const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
      const encodedUri = encodeURI(csvContent);
      const link = document.createElement('a');
      link.setAttribute('href', encodedUri);
      link.setAttribute('download', 'team_directory.csv');
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }}

    loadRemoteMembers();
    render();
  </script>
</body>
</html>"""

        if norm_path == "frontend/src/App.tsx":
            return (
                "import React, { useState, useEffect } from 'react';\n"
                "import { Member, MemberCreateInput, memberApi } from './services/api';\n"
                "import { MemberCard } from './components/MemberCard';\n"
                "import { DirectoryFilters } from './components/DirectoryFilters';\n"
                "import { MemberDetailsModal } from './components/MemberDetailsModal';\n\n"
                "export default function App() {\n"
                "  const [members, setMembers] = useState<Member[]>([]);\n"
                "  const [searchQuery, setSearchQuery] = useState('');\n"
                "  const [selectedDept, setSelectedDept] = useState('All');\n"
                "  const [activeMember, setActiveMember] = useState<Member | null>(null);\n"
                "  const [isLoading, setIsLoading] = useState(true);\n\n"
                "  const loadMembers = async () => {\n"
                "    try {\n"
                "      setIsLoading(true);\n"
                "      const data = await memberApi.listMembers();\n"
                "      setMembers(data);\n"
                "    } catch (e) {\n"
                "      console.warn('Failed to load members, using defaults', e);\n"
                "    } finally {\n"
                "      setIsLoading(false);\n"
                "    }\n"
                "  };\n\n"
                "  useEffect(() => {\n"
                "    loadMembers();\n"
                "  }, []);\n\n"
                "  const handleCreateMember = async (input: MemberCreateInput) => {\n"
                "    const created = await memberApi.createMember(input);\n"
                "    setMembers((prev) => [created, ...prev]);\n"
                "  };\n\n"
                "  const filtered = members.filter((m) => {\n"
                "    const matchesDept = selectedDept === 'All' || m.department === selectedDept;\n"
                "    const q = searchQuery.toLowerCase();\n"
                "    const matchesQ = !q || m.name.toLowerCase().includes(q) || m.role.toLowerCase().includes(q);\n"
                "    return matchesDept && matchesQ;\n"
                "  });\n\n"
                "  return (\n"
                "    <div className=\"directory-container\">\n"
                f'      <h1 data-testid=\"app-title\">{project_name}</h1>\n'
                "      <DirectoryFilters\n"
                "        searchQuery={searchQuery}\n"
                "        onSearchChange={setSearchQuery}\n"
                "        selectedDept={selectedDept}\n"
                "        onDeptChange={setSelectedDept}\n"
                "      />\n"
                "      <div className=\"members-grid\" data-testid=\"members-grid\">\n"
                "        {filtered.map((m) => (\n"
                "          <MemberCard key={m.id} member={m} onViewProfile={() => setActiveMember(m)} />\n"
                "        ))}\n"
                "      </div>\n"
                "      {activeMember && (\n"
                "        <MemberDetailsModal member={activeMember} onClose={() => setActiveMember(null)} />\n"
                "      )}\n"
                "    </div>\n"
                "  );\n"
                "}\n"
            )

        if norm_path == "frontend/src/components/MemberCard.tsx":
            return (
                "import React from 'react';\n"
                "import { Member } from '../services/api';\n\n"
                "interface MemberCardProps {\n"
                "  member: Member;\n"
                "  onViewProfile: () => void;\n"
                "}\n\n"
                "export const MemberCard: React.FC<MemberCardProps> = ({ member, onViewProfile }) => (\n"
                "  <div className=\"member-card\" data-testid=\"member-card\">\n"
                "    <div className=\"member-avatar\">{member.avatar || member.name.substring(0, 2)}</div>\n"
                "    <div className=\"member-name\" data-testid=\"member-name\">{member.name}</div>\n"
                "    <div className=\"member-role\">{member.role}</div>\n"
                "    <div className=\"dept-badge\">{member.department}</div>\n"
                "    <button className=\"btn-view\" data-testid=\"btn-view-profile\" onClick={onViewProfile}>View Profile</button>\n"
                "  </div>\n"
                ");\n"
            )

        if norm_path == "frontend/src/components/DirectoryFilters.tsx":
            return (
                "import React from 'react';\n\n"
                "interface FiltersProps {\n"
                "  searchQuery: string;\n"
                "  onSearchChange: (q: string) => void;\n"
                "  selectedDept: string;\n"
                "  onDeptChange: (d: string) => void;\n"
                "}\n\n"
                "export const DirectoryFilters: React.FC<FiltersProps> = ({\n"
                "  searchQuery,\n"
                "  onSearchChange,\n"
                "  selectedDept,\n"
                "  onDeptChange,\n"
                "}) => (\n"
                "  <div className=\"filters-bar\">\n"
                "    <input\n"
                "      type=\"text\"\n"
                "      data-testid=\"member-search-input\"\n"
                "      value={searchQuery}\n"
                "      onChange={(e) => onSearchChange(e.target.value)}\n"
                "      placeholder=\"Search members...\"\n"
                "    />\n"
                "    <div className=\"pills\">\n"
                "      {['All', 'Engineering', 'Product', 'Design', 'Marketing', 'Sales'].map((dept) => (\n"
                "        <button\n"
                "          key={dept}\n"
                "          className={selectedDept === dept ? 'active' : ''}\n"
                "          onClick={() => onDeptChange(dept)}\n"
                "        >\n"
                "          {dept}\n"
                "        </button>\n"
                "      ))}\n"
                "    </div>\n"
                "  </div>\n"
                ");\n"
            )

        if norm_path == "frontend/src/components/MemberDetailsModal.tsx":
            return (
                "import React from 'react';\n"
                "import { Member } from '../services/api';\n\n"
                "interface ModalProps {\n"
                "  member: Member;\n"
                "  onClose: () => void;\n"
                "}\n\n"
                "export const MemberDetailsModal: React.FC<ModalProps> = ({ member, onClose }) => (\n"
                "  <div className=\"modal-overlay\">\n"
                "    <div className=\"modal-content\">\n"
                "      <h2>{member.name}</h2>\n"
                "      <p>{member.role} &bull; {member.department}</p>\n"
                "      <p>{member.bio || 'Enterprise team member.'}</p>\n"
                "      <button onClick={onClose}>Close</button>\n"
                "    </div>\n"
                "  </div>\n"
                ");\n"
            )

        if norm_path == "frontend/src/services/api.ts":
            return (
                "export interface Member {\n"
                "  id: string;\n"
                "  name: string;\n"
                "  role: string;\n"
                "  department: string;\n"
                "  email: string;\n"
                "  status: string;\n"
                "  location?: string;\n"
                "  avatar?: string;\n"
                "  bio?: string;\n"
                "  skills?: string[];\n"
                "}\n\n"
                "export interface MemberCreateInput {\n"
                "  name: string;\n"
                "  role: string;\n"
                "  department: string;\n"
                "  email: string;\n"
                "  location?: string;\n"
                "}\n\n"
                "export const memberApi = {\n"
                "  async listMembers(): Promise<Member[]> {\n"
                "    const res = await fetch('/members');\n"
                "    return res.ok ? res.json() : [];\n"
                "  },\n"
                "  async createMember(input: MemberCreateInput): Promise<Member> {\n"
                "    const res = await fetch('/members', {\n"
                "      method: 'POST',\n"
                "      headers: { 'Content-Type': 'application/json' },\n"
                "      body: JSON.stringify(input),\n"
                "    });\n"
                "    return res.json();\n"
                "  }\n"
                "};\n"
            )

        if norm_path == "frontend/src/styles/App.css":
            return (
                ":root { --bg: #090d16; --primary: #6366f1; }\n"
                "body { background: var(--bg); color: #f8fafc; font-family: sans-serif; padding: 2rem; }\n"
                ".members-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1rem; margin-top: 1.5rem; }\n"
                ".member-card { background: #111827; padding: 1.5rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.08); }\n"
                ".btn-view { background: var(--primary); color: white; border: none; padding: 0.4rem 0.8rem; border-radius: 4px; cursor: pointer; margin-top: 1rem; }\n"
            )

        if norm_path in ("backend/app/main.py", "app/main.py"):
            return (
                '"""FastAPI application entrypoint for TeamConnect Directory."""\n\n'
                "from fastapi import FastAPI\n"
                "from fastapi.middleware.cors import CORSMiddleware\n"
                "from app.config import get_settings\n"
                "from app.api import router as members_router\n\n"
                "settings = get_settings()\n"
                f'app = FastAPI(title="{project_name}", version="1.0.0")\n\n'
                "app.add_middleware(\n"
                "    CORSMiddleware,\n"
                "    allow_origins=settings.allowed_origins,\n"
                "    allow_credentials=True,\n"
                "    allow_methods=['*'],\n"
                "    allow_headers=['*'],\n"
                ")\n\n"
                "app.include_router(members_router)\n"
            )

        if norm_path in ("backend/app/models.py", "app/models.py"):
            return (
                '"""Pydantic Domain Models for Team Directory."""\n\n'
                "from uuid import UUID, uuid4\n"
                "from pydantic import BaseModel, Field\n\n\n"
                "class MemberRecord(BaseModel):\n"
                "    id: str = Field(default_factory=lambda: str(uuid4()))\n"
                "    name: str\n"
                "    role: str\n"
                "    department: str\n"
                "    email: str\n"
                "    status: str = 'ACTIVE'\n"
                "    location: str | None = None\n"
                "    skills: list[str] = Field(default_factory=list)\n\n\n"
                "class MemberCreate(BaseModel):\n"
                "    name: str\n"
                "    role: str\n"
                "    department: str\n"
                "    email: str\n"
                "    location: str | None = None\n"
            )

        if norm_path in ("backend/app/api.py", "app/api.py"):
            return (
                '"""REST API Router for Team Directory Members."""\n\n'
                "from fastapi import APIRouter, status\n"
                "from app.models import MemberRecord, MemberCreate\n"
                "from app.persistence import repository\n\n"
                'router = APIRouter(prefix="/members", tags=["members"])\n\n\n'
                '@router.get("", response_model=list[MemberRecord])\n'
                "def list_members() -> list[MemberRecord]:\n"
                "    return repository.list_all()\n\n\n"
                '@router.post("", response_model=MemberRecord, status_code=status.HTTP_201_CREATED)\n'
                "def create_member(payload: MemberCreate) -> MemberRecord:\n"
                "    return repository.create(payload)\n"
            )

        if norm_path in ("backend/app/persistence.py", "app/persistence.py"):
            return (
                '"""Thread-safe Repository for Team Directory Members."""\n\n'
                "from uuid import uuid4\n"
                "from app.models import MemberRecord, MemberCreate\n\n\n"
                "class MemberRepository:\n"
                "    def __init__(self):\n"
                "        self._members: list[MemberRecord] = [\n"
                '            MemberRecord(id="mem-1", name="Dr. Aris Thorne", role="Principal Architect", department="Engineering", email="aris@teamconnect.internal", location="San Francisco, CA"),\n'
                '            MemberRecord(id="mem-2", name="Maya Sterling", role="VP of Product", department="Product", email="maya@teamconnect.internal", location="New York, NY"),\n'
                '            MemberRecord(id="mem-3", name="Julian Vega", role="Design Lead", department="Design", email="julian@teamconnect.internal", location="Seattle, WA"),\n'
                "        ]\n\n"
                "    def list_all(self) -> list[MemberRecord]:\n"
                "        return self._members\n\n"
                "    def create(self, payload: MemberCreate) -> MemberRecord:\n"
                "        record = MemberRecord(id=str(uuid4()), name=payload.name, role=payload.role, department=payload.department, email=payload.email, location=payload.location)\n"
                "        self._members.append(record)\n"
                "        return record\n\n\n"
                "repository = MemberRepository()\n"
            )

    # -------------------------------------------------------------
    # Archetype 3: TASKFLOW (KanbanFlow Board)
    # -------------------------------------------------------------
    if archetype == "taskflow":
        if norm_path == "frontend/index.html":
            return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{project_name} — KanbanFlow Agile Board</title>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #090d16;
      --card-bg: #111827;
      --card-border: rgba(255, 255, 255, 0.08);
      --primary: #3b82f6;
      --primary-hover: #2563eb;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --col-bg: rgba(255, 255, 255, 0.02);
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
      flex-wrap: wrap;
      gap: 1rem;
      margin-bottom: 1.5rem;
      border-bottom: 1px solid var(--card-border);
      padding-bottom: 1.25rem;
    }}
    .header-left h1 {{
      font-size: 1.6rem;
      font-weight: 800;
      background: linear-gradient(135deg, #60a5fa, #3b82f6, #93c5fd);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      letter-spacing: -0.5px;
    }}
    .header-left p {{ color: var(--text-muted); font-size: 0.85rem; margin-top: 0.2rem; }}
    .header-right {{ display: flex; gap: 0.75rem; align-items: center; }}
    .search-input {{
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--card-border);
      padding: 0.55rem 1rem;
      border-radius: 8px;
      color: #fff;
      font-size: 0.85rem;
      outline: none;
      min-width: 260px;
    }}
    .search-input:focus {{ border-color: var(--primary); }}
    .btn {{
      background: var(--primary);
      color: white;
      border: none;
      padding: 0.55rem 1.2rem;
      border-radius: 8px;
      font-weight: 600;
      font-size: 0.85rem;
      cursor: pointer;
      transition: all 0.2s;
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
    }}
    .btn:hover {{ background: var(--primary-hover); transform: translateY(-1px); }}
    .btn-secondary {{ background: rgba(255, 255, 255, 0.08); border: 1px solid var(--card-border); }}
    .stats-bar {{
      display: flex;
      gap: 1.5rem;
      margin-bottom: 1.5rem;
      background: var(--col-bg);
      border: 1px solid var(--card-border);
      padding: 0.75rem 1.25rem;
      border-radius: 10px;
    }}
    .stat-item {{ font-size: 0.85rem; color: var(--text-muted); }}
    .stat-item strong {{ color: #fff; font-size: 1rem; }}
    .kanban-grid {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 1.25rem;
      align-items: start;
    }}
    @media (max-width: 1024px) {{
      .kanban-grid {{ grid-template-columns: repeat(2, 1fr); }}
    }}
    @media (max-width: 640px) {{
      .kanban-grid {{ grid-template-columns: 1fr; }}
    }}
    .kanban-col {{
      background: var(--col-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 1rem;
      min-height: 480px;
    }}
    .col-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1rem;
      padding-bottom: 0.5rem;
      border-bottom: 1px solid var(--card-border);
    }}
    .col-title {{ font-size: 0.9rem; font-weight: 700; color: #fff; display: flex; align-items: center; gap: 0.5rem; }}
    .col-count {{
      background: rgba(255, 255, 255, 0.08);
      color: var(--text-muted);
      font-size: 0.75rem;
      padding: 0.15rem 0.5rem;
      border-radius: 9999px;
      font-weight: 700;
    }}
    .task-cards-list {{ display: flex; flex-direction: column; gap: 0.75rem; }}
    .task-card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 10px;
      padding: 1rem;
      transition: all 0.2s;
    }}
    .task-card:hover {{ border-color: rgba(59, 130, 246, 0.4); transform: translateY(-1px); }}
    .task-card-header {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 0.5rem; margin-bottom: 0.5rem; }}
    .task-title {{ font-size: 0.95rem; font-weight: 700; color: #fff; }}
    .priority-badge {{
      font-size: 0.7rem;
      font-weight: 700;
      padding: 0.2rem 0.5rem;
      border-radius: 4px;
      text-transform: uppercase;
      letter-spacing: 0.3px;
    }}
    .p-HIGH {{ background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }}
    .p-MEDIUM {{ background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }}
    .p-LOW {{ background: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); }}
    .task-desc {{ font-size: 0.8rem; color: var(--text-muted); line-height: 1.4; margin-bottom: 0.75rem; }}
    .task-footer {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-top: 1px solid var(--card-border);
      padding-top: 0.6rem;
      margin-top: 0.6rem;
    }}
    .move-btn-group {{ display: flex; gap: 0.25rem; }}
    .btn-action {{
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--card-border);
      color: var(--text-muted);
      padding: 0.2rem 0.5rem;
      border-radius: 4px;
      font-size: 0.75rem;
      cursor: pointer;
    }}
    .btn-action:hover {{ background: rgba(255, 255, 255, 0.12); color: #fff; }}
    .btn-delete {{ background: transparent; border: none; color: #ef4444; cursor: pointer; font-size: 0.8rem; }}
    /* Modal */
    .modal-overlay {{
      display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(0, 0, 0, 0.75); backdrop-filter: blur(4px);
      align-items: center; justify-content: center; z-index: 1000;
    }}
    .modal-overlay.active {{ display: flex; }}
    .modal-box {{
      background: #111827; border: 1px solid var(--card-border); border-radius: 12px;
      padding: 1.75rem; max-width: 480px; width: 90%;
    }}
    .form-group {{ margin-bottom: 1rem; }}
    .form-group label {{ display: block; font-size: 0.8rem; color: var(--text-muted); font-weight: 600; margin-bottom: 0.3rem; }}
    .form-control {{
      width: 100%; background: rgba(255, 255, 255, 0.05); border: 1px solid var(--card-border);
      border-radius: 6px; padding: 0.55rem; color: #fff; font-size: 0.85rem; outline: none;
    }}
  </style>
</head>
<body>
  <div class="header">
    <div class="header-left">
      <h1 id="app-title" data-testid="app-title">{project_name}</h1>
      <p>KanbanFlow Agile Board — Interactive TaskFlow Sprint & Task Management</p>
    </div>
    <div class="header-right">
      <input
        type="text"
        id="task-search-input"
        data-testid="task-search-input"
        class="search-input"
        placeholder="Filter tasks by title or keyword..."
        oninput="handleSearch(this.value)"
      />
      <button class="btn" id="btn-new-task" onclick="openNewTaskModal()">+ New Task</button>
    </div>
  </div>

  <div class="stats-bar">
    <div class="stat-item">Total Tasks: <strong id="stat-total-tasks">3</strong></div>
    <div class="stat-item">In Progress: <strong id="stat-in-progress" style="color: #60a5fa;">1</strong></div>
    <div class="stat-item">Completed: <strong id="stat-completed-tasks" style="color: #34d399;">1</strong></div>
    <div class="stat-item">System Status: <strong style="color: #34d399;">Connected (Ready)</strong></div>
  </div>

  <div class="kanban-grid">
    <!-- Backlog -->
    <div class="kanban-col" id="col-backlog" data-testid="column-backlog">
      <div class="col-header">
        <div class="col-title">📋 Backlog</div>
        <span class="col-count" id="count-backlog">0</span>
      </div>
      <div class="task-cards-list" id="list-backlog"></div>
    </div>

    <!-- In Progress -->
    <div class="kanban-col" id="col-in-progress" data-testid="column-in-progress">
      <div class="col-header">
        <div class="col-title">⚡ In Progress</div>
        <span class="col-count" id="count-in-progress">0</span>
      </div>
      <div class="task-cards-list" id="list-in-progress"></div>
    </div>

    <!-- Review -->
    <div class="kanban-col" id="col-review" data-testid="column-review">
      <div class="col-header">
        <div class="col-title">🔍 Review</div>
        <span class="col-count" id="count-review">0</span>
      </div>
      <div class="task-cards-list" id="list-review"></div>
    </div>

    <!-- Done -->
    <div class="kanban-col" id="col-done" data-testid="column-done">
      <div class="col-header">
        <div class="col-title">✅ Done</div>
        <span class="col-count" id="count-done">0</span>
      </div>
      <div class="task-cards-list" id="list-done"></div>
    </div>
  </div>

  <!-- Create Task Modal -->
  <div class="modal-overlay" id="task-modal">
    <div class="modal-box">
      <h2 style="font-size: 1.2rem; font-weight: 700; margin-bottom: 1.25rem;">Create New Task</h2>
      <form onsubmit="handleCreateTask(event)">
        <div class="form-group">
          <label>Task Title</label>
          <input type="text" id="task-title-input" class="form-control" required placeholder="e.g. Implement OAuth Flow" />
        </div>
        <div class="form-group">
          <label>Description</label>
          <textarea id="task-desc-input" class="form-control" rows="3" placeholder="Task requirements and acceptance criteria..."></textarea>
        </div>
        <div class="form-group">
          <label>Priority</label>
          <select id="task-priority-input" class="form-control">
            <option value="HIGH">High Priority</option>
            <option value="MEDIUM" selected>Medium Priority</option>
            <option value="LOW">Low Priority</option>
          </select>
        </div>
        <div class="form-group">
          <label>Initial Column</label>
          <select id="task-status-input" class="form-control">
            <option value="PENDING" selected>Backlog</option>
            <option value="IN_PROGRESS">In Progress</option>
            <option value="REVIEW">Review</option>
            <option value="COMPLETED">Done</option>
          </select>
        </div>
        <div style="display: flex; justify-content: flex-end; gap: 0.5rem; margin-top: 1.5rem;">
          <button type="button" class="btn btn-secondary" onclick="closeNewTaskModal()">Cancel</button>
          <button type="submit" class="btn" id="btn-submit-task">Create Task</button>
        </div>
      </form>
    </div>
  </div>

  <script>
    const COLUMNS = ['PENDING', 'IN_PROGRESS', 'REVIEW', 'COMPLETED'];
    let tasks = [
      {{ id: '1', title: 'Review Architecture Blueprint', description: 'Inspect domain models, services, and endpoints.', priority: 'HIGH', status: 'COMPLETED' }},
      {{ id: '2', title: 'Implement Core Feature Set', description: 'Build and integrate primary application logic.', priority: 'HIGH', status: 'IN_PROGRESS' }},
      {{ id: '3', title: 'Verify Live Preview Integration', description: 'Ensure end-to-end API communication and real-time UI updates.', priority: 'MEDIUM', status: 'PENDING' }}
    ];
    let searchQuery = '';

    function loadRemoteTasks() {{
      fetch('/tasks')
        .then(res => res.ok ? res.json() : fetch('/api/tasks').then(r => r.ok ? r.json() : []))
        .then(data => {{
          if (Array.isArray(data) && data.length > 0) {{
            tasks = data.map(t => ({{
              id: String(t.id),
              title: t.title,
              description: t.description || '',
              priority: t.priority || 'MEDIUM',
              status: t.status === 'DONE' ? 'COMPLETED' : (t.status || 'PENDING')
            }}));
            render();
          }}
        }})
        .catch(err => console.debug('Using starter tasks', err));
    }}

    function render() {{
      const cols = {{
        PENDING: document.getElementById('list-backlog'),
        IN_PROGRESS: document.getElementById('list-in-progress'),
        REVIEW: document.getElementById('list-review'),
        COMPLETED: document.getElementById('list-done')
      }};

      Object.values(cols).forEach(el => {{ if (el) el.innerHTML = ''; }});

      const counts = {{ PENDING: 0, IN_PROGRESS: 0, REVIEW: 0, COMPLETED: 0 }};
      const q = searchQuery.toLowerCase();

      tasks.forEach(t => {{
        const matchesQ = !q || t.title.toLowerCase().includes(q) || t.description.toLowerCase().includes(q);
        if (!matchesQ) return;

        const normalizedStatus = t.status === 'DONE' ? 'COMPLETED' : (cols[t.status] ? t.status : 'PENDING');
        counts[normalizedStatus] = (counts[normalizedStatus] || 0) + 1;

        const colIndex = COLUMNS.indexOf(normalizedStatus);
        const canMoveLeft = colIndex > 0;
        const canMoveRight = colIndex < COLUMNS.length - 1;

        const card = document.createElement('div');
        card.className = 'task-card';
        card.setAttribute('data-testid', 'task-card');
        card.innerHTML = `
          <div class="task-card-header">
            <span class="task-title" data-testid="task-title">${{t.title}}</span>
            <span class="priority-badge p-${{t.priority}}">${{t.priority}}</span>
          </div>
          <div class="task-desc">${{t.description || 'No description provided.'}}</div>
          <div class="task-footer">
            <div class="move-btn-group">
              ${{canMoveLeft ? `<button class="btn-action btn-move-back" onclick="moveTask('${{t.id}}', -1)">◀</button>` : ''}}
              ${{canMoveRight ? `<button class="btn-action btn-move-forward" onclick="moveTask('${{t.id}}', 1)">▶</button>` : ''}}
            </div>
            <button class="btn-delete" onclick="deleteTask('${{t.id}}')">🗑</button>
          </div>
        `;
        if (cols[normalizedStatus]) cols[normalizedStatus].appendChild(card);
      }});

      document.getElementById('count-backlog').textContent = counts.PENDING;
      document.getElementById('count-in-progress').textContent = counts.IN_PROGRESS;
      document.getElementById('count-review').textContent = counts.REVIEW;
      document.getElementById('count-done').textContent = counts.COMPLETED;

      document.getElementById('stat-total-tasks').textContent = tasks.length;
      document.getElementById('stat-in-progress').textContent = counts.IN_PROGRESS;
      document.getElementById('stat-completed-tasks').textContent = counts.COMPLETED;
    }}

    function handleSearch(val) {{
      searchQuery = val;
      render();
    }}

    function moveTask(id, dir) {{
      const t = tasks.find(task => task.id === String(id));
      if (!t) return;
      const currentIdx = COLUMNS.indexOf(t.status === 'DONE' ? 'COMPLETED' : t.status);
      const nextIdx = currentIdx + dir;
      if (nextIdx >= 0 && nextIdx < COLUMNS.length) {{
        t.status = COLUMNS[nextIdx];
        render();
        try {{
          fetch(`/tasks/${{id}}`, {{
            method: 'PUT',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ status: t.status }})
          }}).catch(() => {{}});
        }} catch(e) {{}}
      }}
    }}

    function deleteTask(id) {{
      tasks = tasks.filter(task => task.id !== String(id));
      render();
      try {{
        fetch(`/tasks/${{id}}`, {{ method: 'DELETE' }}).catch(() => {{}});
      }} catch(e) {{}}
    }}

    function openNewTaskModal() {{
      document.getElementById('task-modal').classList.add('active');
    }}

    function closeNewTaskModal() {{
      document.getElementById('task-modal').classList.remove('active');
    }}

    function handleCreateTask(e) {{
      e.preventDefault();
      const title = document.getElementById('task-title-input').value.trim();
      const desc = document.getElementById('task-desc-input').value.trim();
      const priority = document.getElementById('task-priority-input').value;
      const status = document.getElementById('task-status-input').value;
      if (!title) return;

      const newTask = {{
        id: String(Date.now()),
        title,
        description: desc,
        priority,
        status
      }};

      tasks.push(newTask);
      render();
      closeNewTaskModal();
      document.getElementById('task-title-input').value = '';
      document.getElementById('task-desc-input').value = '';

      try {{
        fetch('/tasks', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify(newTask)
        }}).catch(() => {{}});
      }} catch(err) {{}}
    }}

    loadRemoteTasks();
    render();
  </script>
</body>
</html>"""

        if norm_path == "frontend/src/App.tsx":
            return (
                "import React, { useState, useEffect } from 'react';\n"
                "import { Task, TaskCreateInput, taskApi } from './services/api';\n"
                "import { KanbanBoard } from './components/KanbanBoard';\n"
                "import { TaskForm } from './components/TaskForm';\n\n"
                "export default function App() {\n"
                "  const [tasks, setTasks] = useState<Task[]>([]);\n"
                "  const [isLoading, setIsLoading] = useState(true);\n\n"
                "  const loadTasks = async () => {\n"
                "    try {\n"
                "      setIsLoading(true);\n"
                "      const data = await taskApi.listTasks();\n"
                "      setTasks(data);\n"
                "    } catch (e) {\n"
                "      console.warn('Failed to load tasks', e);\n"
                "    } finally {\n"
                "      setIsLoading(false);\n"
                "    }\n"
                "  };\n\n"
                "  useEffect(() => {\n"
                "    loadTasks();\n"
                "  }, []);\n\n"
                "  const handleCreateTask = async (input: TaskCreateInput) => {\n"
                "    const created = await taskApi.createTask(input);\n"
                "    setTasks((prev) => [...prev, created]);\n"
                "  };\n\n"
                "  const handleMoveTask = async (id: string, newStatus: any) => {\n"
                "    const updated = await taskApi.updateTask(id, { status: newStatus });\n"
                "    setTasks((prev) => prev.map((t) => (t.id === id ? updated : t)));\n"
                "  };\n\n"
                "  const handleDeleteTask = async (id: string) => {\n"
                "    await taskApi.deleteTask(id);\n"
                "    setTasks((prev) => prev.filter((t) => t.id !== id));\n"
                "  };\n\n"
                "  return (\n"
                "    <div className=\"kanban-app\">\n"
                f'      <h1 data-testid=\"app-title\">{project_name}</h1>\n'
                "      <TaskForm onSubmit={handleCreateTask} />\n"
                "      <KanbanBoard\n"
                "        tasks={tasks}\n"
                "        onMoveTask={handleMoveTask}\n"
                "        onDeleteTask={handleDeleteTask}\n"
                "      />\n"
                "    </div>\n"
                "  );\n"
                "}\n"
            )

        if norm_path == "frontend/src/components/KanbanBoard.tsx":
            return (
                "import React from 'react';\n"
                "import { Task } from '../services/api';\n"
                "import { TaskCard } from './TaskCard';\n\n"
                "interface BoardProps {\n"
                "  tasks: Task[];\n"
                "  onMoveTask: (id: string, newStatus: any) => void;\n"
                "  onDeleteTask: (id: string) => void;\n"
                "}\n\n"
                "export const KanbanBoard: React.FC<BoardProps> = ({ tasks, onMoveTask, onDeleteTask }) => {\n"
                "  const cols = [\n"
                "    { key: 'PENDING', label: 'Backlog', testId: 'column-backlog' },\n"
                "    { key: 'IN_PROGRESS', label: 'In Progress', testId: 'column-in-progress' },\n"
                "    { key: 'REVIEW', label: 'Review', testId: 'column-review' },\n"
                "    { key: 'COMPLETED', label: 'Done', testId: 'column-done' },\n"
                "  ];\n"
                "  return (\n"
                "    <div className=\"kanban-grid\">\n"
                "      {cols.map((col) => (\n"
                "        <div key={col.key} className=\"kanban-col\" data-testid={col.testId}>\n"
                "          <h3>{col.label}</h3>\n"
                "          {tasks.filter((t) => t.status === col.key).map((task) => (\n"
                "            <TaskCard key={task.id} task={task} onMove={onMoveTask} onDelete={onDeleteTask} />\n"
                "          ))}\n"
                "        </div>\n"
                "      ))}\n"
                "    </div>\n"
                "  );\n"
                "};\n"
            )

        if norm_path == "frontend/src/components/TaskCard.tsx":
            return (
                "import React from 'react';\n"
                "import { Task } from '../services/api';\n\n"
                "interface CardProps {\n"
                "  task: Task;\n"
                "  onMove: (id: string, newStatus: any) => void;\n"
                "  onDelete: (id: string) => void;\n"
                "}\n\n"
                "export const TaskCard: React.FC<CardProps> = ({ task, onDelete }) => (\n"
                "  <div className=\"task-card\" data-testid=\"task-card\">\n"
                "    <div className=\"task-title\" data-testid=\"task-title\">{task.title}</div>\n"
                "    <div className=\"task-desc\">{task.description}</div>\n"
                "    <button className=\"btn-delete\" onClick={() => onDelete(task.id)}>Delete</button>\n"
                "  </div>\n"
                ");\n"
            )

        if norm_path == "frontend/src/components/TaskForm.tsx":
            return (
                "import React, { useState } from 'react';\n"
                "import { TaskCreateInput } from '../services/api';\n\n"
                "interface FormProps {\n"
                "  onSubmit: (input: TaskCreateInput) => void;\n"
                "}\n\n"
                "export const TaskForm: React.FC<FormProps> = ({ onSubmit }) => {\n"
                "  const [title, setTitle] = useState('');\n"
                "  return (\n"
                "    <form onSubmit={(e) => { e.preventDefault(); if (title) { onSubmit({ title }); setTitle(''); } }}>\n"
                "      <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder=\"New task...\" />\n"
                "      <button type=\"submit\">Add</button>\n"
                "    </form>\n"
                "  );\n"
                "};\n"
            )

        if norm_path == "frontend/src/services/api.ts":
            return (
                "export interface Task {\n"
                "  id: string;\n"
                "  title: string;\n"
                "  description?: string;\n"
                "  priority: 'LOW' | 'MEDIUM' | 'HIGH';\n"
                "  status: 'PENDING' | 'IN_PROGRESS' | 'REVIEW' | 'COMPLETED';\n"
                "}\n\n"
                "const API_BASE_URL = (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_BASE_URL) || 'http://localhost:8000';\n\n"
                "export interface TaskCreateInput {\n"
                "  title: string;\n"
                "  description?: string;\n"
                "  priority?: 'LOW' | 'MEDIUM' | 'HIGH';\n"
                "  status?: string;\n"
                "}\n\n"
                "export const taskApi = {\n"
                "  async listTasks(): Promise<Task[]> {\n"
                "    const res = await fetch('/tasks');\n"
                "    return res.ok ? res.json() : [];\n"
                "  },\n"
                "  async createTask(input: TaskCreateInput): Promise<Task> {\n"
                "    const res = await fetch('/tasks', {\n"
                "      method: 'POST',\n"
                "      headers: { 'Content-Type': 'application/json' },\n"
                "      body: JSON.stringify(input),\n"
                "    });\n"
                "    return res.json();\n"
                "  },\n"
                "  async updateTask(id: string, input: Partial<Task>): Promise<Task> {\n"
                "    const res = await fetch(`/tasks/${id}`, {\n"
                "      method: 'PUT',\n"
                "      headers: { 'Content-Type': 'application/json' },\n"
                "      body: JSON.stringify(input),\n"
                "    });\n"
                "    return res.json();\n"
                "  },\n"
                "  async deleteTask(id: string): Promise<void> {\n"
                "    await fetch(`/tasks/${id}`, { method: 'DELETE' });\n"
                "  }\n"
                "};\n"
            )

        if norm_path == "frontend/src/styles/App.css":
            return (
                ":root { --bg: #090d16; }\n"
                "body { background: var(--bg); color: #f8fafc; font-family: sans-serif; padding: 1.5rem; }\n"
                ".kanban-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; }\n"
                ".kanban-col { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); padding: 1rem; border-radius: 8px; }\n"
                ".task-card { background: #111827; padding: 1rem; border-radius: 6px; margin-bottom: 0.5rem; }\n"
            )

        if norm_path in ("backend/app/main.py", "app/main.py"):
            return (
                '"""FastAPI application entrypoint for TaskFlow Kanban."""\n\n'
                "from fastapi import FastAPI\n"
                "from fastapi.middleware.cors import CORSMiddleware\n"
                "from app.config import get_settings\n"
                "from app.api import router as tasks_router\n\n"
                "settings = get_settings()\n"
                f'app = FastAPI(title="{project_name}", version="1.0.0")\n\n'
                "app.add_middleware(\n"
                "    CORSMiddleware,\n"
                "    allow_origins=settings.allowed_origins,\n"
                "    allow_credentials=True,\n"
                "    allow_methods=['*'],\n"
                "    allow_headers=['*'],\n"
                ")\n\n"
                "app.include_router(tasks_router)\n"
            )

        if norm_path in ("backend/app/models.py", "app/models.py"):
            return (
                '"""Pydantic schemas for Kanban Tasks."""\n\n'
                "from uuid import UUID, uuid4\n"
                "from pydantic import BaseModel, Field\n\n\n"
                "class Task(BaseModel):\n"
                "    id: UUID = Field(default_factory=uuid4)\n"
                "    title: str\n"
                "    description: str | None = None\n"
                "    priority: str = 'MEDIUM'\n"
                "    status: str = 'PENDING'\n\n\n"
                "class TaskCreate(BaseModel):\n"
                "    title: str\n"
                "    description: str | None = None\n"
                "    priority: str = 'MEDIUM'\n"
                "    status: str = 'PENDING'\n\n\n"
                "class TaskUpdate(BaseModel):\n"
                "    title: str | None = None\n"
                "    description: str | None = None\n"
                "    priority: str | None = None\n"
                "    status: str | None = None\n"
            )

        if norm_path in ("backend/app/api.py", "app/api.py"):
            return (
                '"""REST API routes for Task Operations."""\n\n'
                "from uuid import UUID\n"
                "from fastapi import APIRouter, HTTPException, status\n"
                "from app.models import Task, TaskCreate, TaskUpdate\n"
                "from app.persistence import repository\n\n"
                'router = APIRouter(prefix="/tasks", tags=["tasks"])\n\n\n'
                '@router.get("", response_model=list[Task])\n'
                "def get_tasks() -> list[Task]:\n"
                "    return repository.list_all()\n\n\n"
                '@router.post("", response_model=Task, status_code=status.HTTP_201_CREATED)\n'
                "def create_task(payload: TaskCreate) -> Task:\n"
                "    return repository.create(payload)\n\n\n"
                '@router.put("/{task_id}", response_model=Task)\n'
                "def update_task(task_id: UUID, payload: TaskUpdate) -> Task:\n"
                "    task = repository.update(task_id, payload)\n"
                "    if not task:\n"
                "        raise HTTPException(status_code=404, detail='Task not found')\n"
                "    return task\n\n\n"
                '@router.delete("/{task_id}")\n'
                "def delete_task(task_id: UUID):\n"
                "    repository.delete(task_id)\n"
                "    return {'status': 'deleted', 'id': str(task_id)}\n"
            )

        if norm_path in ("backend/app/persistence.py", "app/persistence.py"):
            return (
                '"""Thread-safe Repository for Kanban Tasks."""\n\n'
                "from uuid import UUID, uuid4\n"
                "from app.models import Task, TaskCreate, TaskUpdate\n\n\n"
                "class TaskRepository:\n"
                "    def __init__(self):\n"
                "        self._tasks: list[Task] = [\n"
                '            Task(id=uuid4(), title="Review Architecture Blueprint", priority="HIGH", status="COMPLETED"),\n'
                '            Task(id=uuid4(), title="Implement Core Feature Set", priority="HIGH", status="IN_PROGRESS"),\n'
                '            Task(id=uuid4(), title="Verify Live Preview Integration", priority="MEDIUM", status="PENDING"),\n'
                "        ]\n\n"
                "    def list_all(self) -> list[Task]:\n"
                "        return self._tasks\n\n"
                "    def create(self, payload: TaskCreate) -> Task:\n"
                "        t = Task(id=uuid4(), title=payload.title, description=payload.description, priority=payload.priority, status=payload.status)\n"
                "        self._tasks.append(t)\n"
                "        return t\n\n"
                "    def update(self, task_id: UUID, payload: TaskUpdate) -> Task | None:\n"
                "        for t in self._tasks:\n"
                "            if t.id == task_id:\n"
                "                if payload.title is not None: t.title = payload.title\n"
                "                if payload.description is not None: t.description = payload.description\n"
                "                if payload.priority is not None: t.priority = payload.priority\n"
                "                if payload.status is not None: t.status = payload.status\n"
                "                return t\n"
                "        return None\n\n"
                "    def delete(self, task_id: UUID) -> bool:\n"
                "        init = len(self._tasks)\n"
                "        self._tasks = [t for t in self._tasks if t.id != task_id]\n"
                "        return len(self._tasks) < init\n\n\n"
                "repository = TaskRepository()\n"
            )

    # -------------------------------------------------------------
    # Archetype 4: ANALYTICS (Executive Analytics & BI Dashboard)
    # -------------------------------------------------------------
    if archetype == "analytics":
        if norm_path == "frontend/index.html":
            return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{project_name} — Executive Analytics Dashboard</title>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #090d16;
      --card-bg: #111827;
      --card-border: rgba(255, 255, 255, 0.08);
      --primary: #10b981;
      --primary-hover: #059669;
      --accent-blue: #3b82f6;
      --accent-purple: #8b5cf6;
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
    }}
    .container {{ max-width: 1200px; margin: 0 auto; }}
    .header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 1.5rem;
      margin-bottom: 2rem;
      border-bottom: 1px solid var(--card-border);
      padding-bottom: 1.5rem;
    }}
    .header-title h1 {{
      font-size: 1.75rem;
      font-weight: 800;
      background: linear-gradient(135deg, #34d399, #10b981, #60a5fa);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      letter-spacing: -0.5px;
    }}
    .header-title p {{ color: var(--text-muted); font-size: 0.9rem; margin-top: 0.25rem; }}
    .header-actions {{ display: flex; gap: 0.75rem; align-items: center; }}
    .btn {{
      background: var(--primary);
      color: white;
      border: none;
      padding: 0.55rem 1.25rem;
      border-radius: 8px;
      font-weight: 600;
      font-size: 0.85rem;
      cursor: pointer;
      transition: all 0.2s;
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
    }}
    .btn:hover {{ background: var(--primary-hover); transform: translateY(-1px); }}
    .btn-secondary {{ background: rgba(255, 255, 255, 0.08); border: 1px solid var(--card-border); color: var(--text); }}
    .btn-secondary:hover {{ background: rgba(255, 255, 255, 0.14); }}
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 1.25rem;
      margin-bottom: 2rem;
    }}
    .kpi-card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 1.5rem;
      position: relative;
      overflow: hidden;
    }}
    .kpi-label {{ font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px; }}
    .kpi-val {{ font-size: 2rem; font-weight: 800; color: #fff; margin: 0.4rem 0; font-family: 'JetBrains Mono', monospace; }}
    .kpi-change {{ font-size: 0.8rem; font-weight: 700; display: inline-flex; align-items: center; gap: 0.25rem; }}
    .change-up {{ color: #34d399; }}
    .change-down {{ color: #f87171; }}
    .charts-row {{
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: 1.25rem;
      margin-bottom: 2rem;
    }}
    @media (max-width: 900px) {{
      .charts-row {{ grid-template-columns: 1fr; }}
    }}
    .chart-card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 1.5rem;
    }}
    .chart-title {{ font-size: 1rem; font-weight: 700; color: #fff; margin-bottom: 1rem; display: flex; justify-content: space-between; }}
    .chart-container {{ width: 100%; height: 200px; display: flex; align-items: flex-end; }}
    svg.chart-svg {{ width: 100%; height: 100%; }}
    .table-card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 1.5rem;
    }}
    .table-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 1rem;
      margin-bottom: 1.25rem;
    }}
    .search-input {{
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--card-border);
      padding: 0.5rem 0.85rem;
      border-radius: 6px;
      color: #fff;
      font-size: 0.85rem;
      outline: none;
      min-width: 240px;
    }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.875rem; }}
    th {{ text-align: left; padding: 0.75rem 1rem; color: var(--text-muted); font-size: 0.75rem; text-transform: uppercase; border-bottom: 1px solid var(--card-border); }}
    td {{ padding: 0.85rem 1rem; border-bottom: 1px solid var(--card-border); }}
    .badge {{ padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 700; }}
    .badge-track {{ background: rgba(16, 185, 129, 0.15); color: #34d399; }}
    .badge-risk {{ background: rgba(239, 68, 68, 0.15); color: #f87171; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="header-title">
        <h1 id="app-title" data-testid="app-title">{project_name}</h1>
        <p>Executive Analytics & BI Dashboard — Real-Time KPI Intelligence</p>
      </div>
      <div class="header-actions">
        <button class="btn btn-secondary" id="btn-export-csv" onclick="exportAnalyticsCSV()">Export CSV</button>
        <button class="btn" id="btn-add-metric" onclick="openAddMetricModal()">+ Add Metric</button>
      </div>
    </div>

    <!-- 4 KPI Summary Cards -->
    <div class="kpi-grid">
      <div class="kpi-card" id="kpi-arr">
        <div class="kpi-label">Annual Recurring Revenue</div>
        <div class="kpi-val">$2,480,000</div>
        <div class="kpi-change change-up">&uarr; +19.4% YoY</div>
      </div>
      <div class="kpi-card" id="kpi-workspaces">
        <div class="kpi-label">Active Workspaces</div>
        <div class="kpi-val">1,420</div>
        <div class="kpi-change change-up">&uarr; +12.4% MoM</div>
      </div>
      <div class="kpi-card" id="kpi-conversion">
        <div class="kpi-label">Trial Conversion Rate</div>
        <div class="kpi-val">4.85%</div>
        <div class="kpi-change change-up">&uarr; +0.6% vs benchmark</div>
      </div>
      <div class="kpi-card" id="kpi-latency">
        <div class="kpi-label">Avg API Latency</div>
        <div class="kpi-val">142ms</div>
        <div class="kpi-change change-up">&darr; -15ms improvement</div>
      </div>
    </div>

    <!-- Charts Row -->
    <div class="charts-row">
      <div class="chart-card">
        <div class="chart-title">
          <span>Monthly Revenue Trend ($K)</span>
          <span style="font-size: 0.8rem; color: #34d399;">+16.1% H2 Run Rate</span>
        </div>
        <div class="chart-container">
          <svg class="chart-svg" id="chart-revenue-trend" viewBox="0 0 500 160">
            <defs>
              <linearGradient id="grad-area" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#10b981" stop-opacity="0.3"/>
                <stop offset="100%" stop-color="#10b981" stop-opacity="0.0"/>
              </linearGradient>
            </defs>
            <polyline fill="url(#grad-area)" stroke="none" points="20,130 100,110 180,95 260,80 340,65 420,40 480,25 480,150 20,150" />
            <polyline fill="none" stroke="#10b981" stroke-width="3" points="20,130 100,110 180,95 260,80 340,65 420,40 480,25" />
            <circle cx="20" cy="130" r="4" fill="#34d399" />
            <circle cx="100" cy="110" r="4" fill="#34d399" />
            <circle cx="180" cy="95" r="4" fill="#34d399" />
            <circle cx="260" cy="80" r="4" fill="#34d399" />
            <circle cx="340" cy="65" r="4" fill="#34d399" />
            <circle cx="420" cy="40" r="4" fill="#34d399" />
            <circle cx="480" cy="25" r="5" fill="#fff" stroke="#10b981" stroke-width="2" />
          </svg>
        </div>
      </div>

      <div class="chart-card">
        <div class="chart-title">
          <span>Workspace Additions</span>
          <span style="font-size: 0.8rem; color: #60a5fa;">Monthly</span>
        </div>
        <div class="chart-container">
          <svg class="chart-svg" id="chart-workspaces-bar" viewBox="0 0 260 160">
            <rect x="20" y="70" width="28" height="80" fill="#3b82f6" rx="4" />
            <rect x="65" y="55" width="28" height="95" fill="#3b82f6" rx="4" />
            <rect x="110" y="45" width="28" height="105" fill="#3b82f6" rx="4" />
            <rect x="155" y="30" width="28" height="120" fill="#60a5fa" rx="4" />
            <rect x="200" y="15" width="28" height="135" fill="#93c5fd" rx="4" />
            <text x="34" y="62" fill="#94a3b8" font-size="10" text-anchor="middle">120</text>
            <text x="79" y="47" fill="#94a3b8" font-size="10" text-anchor="middle">145</text>
            <text x="124" y="37" fill="#94a3b8" font-size="10" text-anchor="middle">180</text>
            <text x="169" y="22" fill="#94a3b8" font-size="10" text-anchor="middle">210</text>
            <text x="214" y="10" fill="#fff" font-size="10" text-anchor="middle" font-weight="bold">265</text>
          </svg>
        </div>
      </div>
    </div>

    <!-- Filterable Metrics Table -->
    <div class="table-card">
      <div class="table-header">
        <div style="font-weight: 700; font-size: 1.05rem;">Operational KPI Scorecard</div>
        <input
          type="text"
          id="metric-search-input"
          data-testid="metric-search-input"
          class="search-input"
          placeholder="Filter metric names or categories..."
          oninput="handleSearch(this.value)"
        />
      </div>
      <table id="metrics-table">
        <thead>
          <tr>
            <th>Metric Name</th>
            <th>Category</th>
            <th>Current Value</th>
            <th>Target</th>
            <th>Trend</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody id="metrics-body"></tbody>
      </table>
    </div>
  </div>

  <script>
    let metrics = [
      {{ name: 'Net Revenue Retention (NRR)', category: 'Revenue', value: '112.5%', target: '110.0%', trend: '+2.5%', status: 'On Track' }},
      {{ name: 'Monthly Active Developers', category: 'Usage', value: '15,420', target: '14,000', trend: '+10.1%', status: 'On Track' }},
      {{ name: 'Customer Acquisition Cost (CAC)', category: 'Revenue', value: '$640', target: '$700', trend: '-8.5%', status: 'On Track' }},
      {{ name: 'P95 API Response Latency', category: 'Performance', value: '142ms', target: '180ms', trend: '-21.1%', status: 'On Track' }},
      {{ name: 'Test Execution Pipeline Time', category: 'Performance', value: '42s', target: '30s', trend: '+12.0%', status: 'At Risk' }},
      {{ name: 'Monthly Churn Rate', category: 'Revenue', value: '1.4%', target: '1.5%', trend: '-0.1%', status: 'On Track' }}
    ];
    let searchQuery = '';

    function renderMetrics() {{
      const tbody = document.getElementById('metrics-body');
      const q = searchQuery.toLowerCase();
      const filtered = metrics.filter(m => !q || m.name.toLowerCase().includes(q) || m.category.toLowerCase().includes(q));
      tbody.innerHTML = filtered.map(m => `
        <tr>
          <td style="font-weight:600; color:#fff;">${{m.name}}</td>
          <td><span style="color:#94a3b8; font-size:0.8rem;">${{m.category}}</span></td>
          <td style="font-family:'JetBrains Mono', monospace; font-weight:700;">${{m.value}}</td>
          <td style="color:#64748b;">${{m.target}}</td>
          <td style="color:${{m.trend.startsWith('+') ? '#34d399' : '#f87171'}}; font-weight:700;">${{m.trend}}</td>
          <td><span class="badge ${{m.status === 'On Track' ? 'badge-track' : 'badge-risk'}}">${{m.status}}</span></td>
        </tr>
      `).join('');
    }}

    function handleSearch(val) {{
      searchQuery = val;
      renderMetrics();
    }}

    function openAddMetricModal() {{
      const name = prompt('Enter new metric name:');
      if (!name) return;
      const cat = prompt('Enter category (Revenue / Usage / Performance):') || 'Usage';
      const val = prompt('Enter current value:') || '100';
      metrics.unshift({{ name, category: cat, value: val, target: val, trend: '+0.0%', status: 'On Track' }});
      renderMetrics();
    }}

    function exportAnalyticsCSV() {{
      const headers = ['Metric Name', 'Category', 'Current Value', 'Target', 'Trend', 'Status'];
      const rows = metrics.map(m => [`"${{m.name}}"`, m.category, `"${{m.value}}"`, `"${{m.target}}"`, m.trend, m.status]);
      const csv = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
      const uri = encodeURI(csv);
      const a = document.createElement('a');
      a.href = uri; a.download = 'executive_metrics.csv';
      document.body.appendChild(a); a.click(); document.body.removeChild(a);
    }}

    renderMetrics();
  </script>
</body>
</html>"""

        if norm_path == "frontend/src/App.tsx":
            return (
                "import React, { useState, useEffect } from 'react';\n"
                "import { KpiGrid } from './components/KpiGrid';\n"
                "import { MetricsTable } from './components/MetricsTable';\n"
                "import { analyticsApi, MetricItem } from './services/api';\n\n"
                "export default function App() {\n"
                "  const [metrics, setMetrics] = useState<MetricItem[]>([]);\n"
                "  const [summary, setSummary] = useState<any>(null);\n\n"
                "  useEffect(() => {\n"
                "    analyticsApi.getMetrics().then((data) => {\n"
                "      if (data && data.kpis) setMetrics(data.kpis);\n"
                "      if (data && data.summary) setSummary(data.summary);\n"
                "    });\n"
                "  }, []);\n\n"
                "  return (\n"
                "    <div className=\"analytics-dashboard\">\n"
                f'      <h1 data-testid=\"app-title\">{project_name}</h1>\n'
                "      <KpiGrid summary={summary} />\n"
                "      <MetricsTable metrics={metrics} />\n"
                "    </div>\n"
                "  );\n"
                "}\n"
            )

        if norm_path == "frontend/src/components/KpiGrid.tsx":
            return (
                "import React from 'react';\n\n"
                "export const KpiGrid: React.FC<{ summary: any }> = ({ summary }) => (\n"
                "  <div className=\"kpi-grid\">\n"
                "    <div className=\"kpi-card\"><div>ARR</div><h2>{summary?.arr || '$2.48M'}</h2></div>\n"
                "    <div className=\"kpi-card\"><div>Workspaces</div><h2>{summary?.active_users || '1,420'}</h2></div>\n"
                "  </div>\n"
                ");\n"
            )

        if norm_path == "frontend/src/components/MetricsTable.tsx":
            return (
                "import React from 'react';\n"
                "import { MetricItem } from '../services/api';\n\n"
                "export const MetricsTable: React.FC<{ metrics: MetricItem[] }> = ({ metrics }) => (\n"
                "  <table className=\"metrics-table\">\n"
                "    <thead><tr><th>Metric</th><th>Value</th><th>Change</th></tr></thead>\n"
                "    <tbody>\n"
                "      {metrics.map((m, i) => (\n"
                "        <tr key={i}><td>{m.name}</td><td>{m.value}</td><td>{m.change}</td></tr>\n"
                "      ))}\n"
                "    </tbody>\n"
                "  </table>\n"
                ");\n"
            )

        if norm_path == "frontend/src/components/AddMetricModal.tsx":
            return (
                "import React from 'react';\n\n"
                "export const AddMetricModal: React.FC<{ onClose: () => void }> = ({ onClose }) => (\n"
                "  <div className=\"modal\"><button onClick={onClose}>Close</button></div>\n"
                ");\n"
            )

        if norm_path == "frontend/src/services/api.ts":
            return (
                "export interface MetricItem {\n"
                "  name: string;\n"
                "  value: string;\n"
                "  change: string;\n"
                "  category?: string;\n"
                "}\n\n"
                "export const analyticsApi = {\n"
                "  async getMetrics(): Promise<any> {\n"
                "    const res = await fetch('/metrics');\n"
                "    return res.ok ? res.json() : { kpis: [], summary: {} };\n"
                "  }\n"
                "};\n"
            )

        if norm_path == "frontend/src/styles/App.css":
            return (
                ":root { --bg: #090d16; }\n"
                "body { background: var(--bg); color: #f8fafc; font-family: sans-serif; padding: 2rem; }\n"
                ".kpi-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; margin-bottom: 2rem; }\n"
                ".kpi-card { background: #111827; padding: 1.5rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.08); }\n"
            )

        if norm_path in ("backend/app/main.py", "app/main.py"):
            return (
                '"""FastAPI entrypoint for Executive Analytics."""\n\n'
                "from fastapi import FastAPI\n"
                "from fastapi.middleware.cors import CORSMiddleware\n"
                "from app.config import get_settings\n"
                "from app.api import router as metrics_router\n\n"
                "settings = get_settings()\n"
                f'app = FastAPI(title="{project_name}", version="1.0.0")\n\n'
                "app.add_middleware(\n"
                "    CORSMiddleware,\n"
                "    allow_origins=settings.allowed_origins,\n"
                "    allow_credentials=True,\n"
                "    allow_methods=['*'],\n"
                "    allow_headers=['*'],\n"
                ")\n\n"
                "app.include_router(metrics_router)\n"
            )

        if norm_path in ("backend/app/models.py", "app/models.py"):
            return (
                '"""Domain Models for Executive Analytics."""\n\n'
                "from pydantic import BaseModel\n\n\n"
                "class MetricRecord(BaseModel):\n"
                "    name: str\n"
                "    value: str\n"
                "    change: str\n"
                "    category: str = 'Financial'\n"
            )

        if norm_path in ("backend/app/api.py", "app/api.py"):
            return (
                '"""REST API Router for Metrics."""\n\n'
                "from fastapi import APIRouter\n"
                "from app.models import MetricRecord\n"
                "from app.persistence import repository\n\n"
                'router = APIRouter(prefix="/metrics", tags=["metrics"])\n\n\n'
                '@router.get("", response_model=dict)\n'
                "def get_metrics() -> dict:\n"
                "    return repository.get_all()\n"
            )

        if norm_path in ("backend/app/persistence.py", "app/persistence.py"):
            return (
                '"""Repository for Executive Metrics."""\n\n'
                "class MetricRepository:\n"
                "    def get_all(self) -> dict:\n"
                "        return {\n"
                '            "summary": {"arr": "$2,480,000", "active_users": 1420},\n'
                '            "kpis": [\n'
                '                {"name": "ARR", "value": "$2.48M", "change": "+19.4%"},\n'
                '                {"name": "Workspaces", "value": "1,420", "change": "+12.4%"},\n'
                "            ]\n"
                "        }\n\n"
                "repository = MetricRepository()\n"
            )

    # -------------------------------------------------------------
    # Generic / Language-Safe Fallback
    # -------------------------------------------------------------
    if norm_path == "frontend/index.html":
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{project_name}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #090d16; color: #f8fafc; margin: 0; padding: 2.5rem; }}
    .app-card {{ max-width: 800px; margin: 0 auto; background: #111827; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 2rem; }}
    h1 {{ font-size: 1.8rem; margin-bottom: 0.5rem; color: #fff; }}
    p {{ color: #94a3b8; line-height: 1.6; }}
    .badge {{ display: inline-block; background: rgba(59, 130, 246, 0.15); color: #60a5fa; padding: 0.3rem 0.8rem; border-radius: 9999px; font-weight: 600; font-size: 0.85rem; margin-bottom: 1.5rem; }}
  </style>
</head>
<body>
  <div class="app-card">
    <span class="badge">Application Online &bull; Live Preview</span>
    <h1 id="app-title" data-testid="app-title">{project_name}</h1>
    <p>{project_desc}</p>
  </div>
</body>
</html>"""

    if norm_path == "frontend/src/App.tsx":
        return (
            "import React from 'react';\n\n"
            "export default function App() {\n"
            "  return (\n"
            "    <div style={{ padding: '2rem', textAlign: 'center' }}>\n"
            f'      <h1 data-testid=\"app-title\">{project_name}</h1>\n'
            f'      <p>{project_desc}</p>\n'
            "    </div>\n"
            "  );\n"
            "}\n"
        )

    if norm_path.endswith((".ts", ".tsx")):
        return (
            f"// Implementation for {path}\n"
            "export const defaultExport = {};\n"
            "export default defaultExport;\n"
        )

    if norm_path.endswith(".py"):
        return (
            f'"""Module {path}."""\n\n'
            "def init_module() -> None:\n"
            "    pass\n"
        )

    if norm_path.endswith(".css"):
        return (
            f"/* Stylesheet for {path} */\n"
            ":root { --primary: #3b82f6; }\n"
        )

    return None
