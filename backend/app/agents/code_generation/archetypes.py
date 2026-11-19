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


import re

ARCHETYPE_TEMPLATES = {
    "shadow_master": {"name": "Shadow Master Skill Builder", "category": "GAME"},
    "carrom": {"name": "Carrom Master", "category": "GAME"},
    "space_arcade": {"name": "Space Arcade Defender", "category": "GAME"},
    "snake_game": {"name": "Arcade Snake", "category": "GAME"},
    "chess": {"name": "Chess Master Pro", "category": "GAME"},
    "platformer": {"name": "Skyline Jump Platformer", "category": "GAME"},
    "racing": {"name": "Turbo Nitro Racing", "category": "GAME"},
    "puzzle": {"name": "Tile Shift Puzzle", "category": "GAME"},
    "educational": {"name": "StudyDeck Flashcards & Quiz", "category": "EDUCATIONAL"},
    "analytics": {"name": "Executive Analytics & BI", "category": "DASHBOARD"},
    "taskflow": {"name": "KanbanFlow Board", "category": "BUSINESS"},
    "eventhub": {"name": "EventHub Conference Booking", "category": "BUSINESS"},
    "ecommerce": {"name": "ShopSphere Catalog & Cart", "category": "BUSINESS"},
    "management": {"name": "Enterprise Management Portal", "category": "MANAGEMENT"},
    "sky_strike": {"name": "Sky Strike Dogfight Simulator", "category": "GAME"},
    "inventory": {"name": "Apex Inventory & Warehouse Manager", "category": "BUSINESS"},
    "lms": {"name": "SkillForge Online Academy", "category": "EDUCATIONAL"},
    "custom": {"name": "Interactive Application Dashboard", "category": "CUSTOM"},
}



def _has_word(text: str, *words: str) -> bool:
    """Check if any of the given words or multi-word phrases appear with word boundaries."""
    for w in words:
        escaped = re.escape(w.lower())
        pattern = r'(?:\b|_)' + escaped + r'(?:\b|_)'
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def classify_application_category(name: str = "", desc: str = "", slug: str = "") -> str:
    """Classify high-level application intent: GAME, DASHBOARD, MANAGEMENT, BUSINESS, EDUCATIONAL, or CUSTOM."""
    combined = f"{name} {desc} {slug}".lower()

    # Explicit exclusions to prevent false-positives
    if _has_word(combined, "production management", "process management", "operations management"):
        return "MANAGEMENT"
    if _has_word(combined, "productivity app", "productivity tool", "productivity application"):
        return "BUSINESS"

    # Game detection
    if _has_word(combined, "game", "gaming", "arcade", "board game", "chess", "carrom", "snake",
                 "platformer", "racing", "puzzle", "action game", "rpg", "fighter", "combat",
                 "ninja", "stealth", "shadow master", "shooter", "simulator"):
        return "GAME"

    # Educational / Learning detection
    if _has_word(combined, "quiz", "flashcard", "flashcards", "educational", "learning",
                 "study tutor", "study app", "exam prep", "course", "lesson", "trivia"):
        return "EDUCATIONAL"

    # Dashboard detection
    if _has_word(combined, "analytics", "kpi", "dashboard", "metric", "metrics", "executive",
                 "revenue", "bi", "business intelligence", "finance", "telemetry"):
        return "DASHBOARD"

    # Management detection
    if _has_word(combined, "teamconnect", "directory", "member", "employee", "roster", "staff",
                 "faculty", "hr", "admin portal", "school management", "student portal",
                 "management portal", "personnel", "admin"):
        return "MANAGEMENT"

    # Business / E-commerce / Taskflow detection
    if _has_word(combined, "shop", "store", "storefront", "ecommerce", "e-commerce", "cart",
                 "checkout", "shopping", "merchandise", "catalog", "marketplace", "retail"):
        return "BUSINESS"

    if _has_word(combined, "kanban", "taskflow", "task manager", "tasks", "task", "todo",
                 "to-do", "backlog", "scrum", "sprint", "project tracker", "eventhub",
                 "event booking", "conference", "ticket booking"):
        return "BUSINESS"

    return "CUSTOM"


def detect_project_archetype(name: str = "", desc: str = "", slug: str = "", **kwargs) -> str:
    """Classify project idea or template into canonical archetype without substring collisions."""
    eff_name = name or kwargs.get("project_name", "")
    eff_desc = desc or kwargs.get("project_description", "")
    eff_slug = slug or kwargs.get("project_slug", "")
    combined = f"{eff_name} {eff_desc} {eff_slug}".lower()

    # 1. Specific GAME Archetypes
    if _has_word(combined, "sky strike", "skystrike", "aerial combat", "dogfight", "fighter jet", "flight simulator", "space battle", "air combat"):
        return "sky_strike"

    if _has_word(combined, "space arcade", "space shooter", "space defender", "arcade shooter", "arcade 2d", "alien waves", "laser shooter", "starship", "arcade game"):
        return "space_arcade"

    if _has_word(combined, "carrom", "carromboard", "carrom board", "striker", "carrom master"):
        return "carrom"

    if _has_word(combined, "chess", "chessboard", "chess board", "checkmate", "grandmaster"):
        return "chess"

    if _has_word(combined, "snake", "slither", "nibbles", "retro snake", "arcade snake"):
        return "snake_game"

    if _has_word(combined, "platformer", "platform game", "side scroller", "sidescroller",
                 "jump and run", "platform jumping", "super jump"):
        return "platformer"

    if _has_word(combined, "racing", "racer", "speedway", "race track", "car racing",
                 "circuit race", "time trial", "drift car", "grand prix"):
        return "racing"

    if _has_word(combined, "puzzle", "sliding puzzle", "15 puzzle", "match 3", "match-3",
                 "tile matching", "sudoku", "crossword", "memory match", "block puzzle", "riddle"):
        return "puzzle"

    if _has_word(combined, "shadow master", "shadowmaster", "shadow combat", "shadow skill",
                 "ninja combat", "stealth ninja", "katana slash", "shadow warrior", "shadow duel", "skill builder"):
        return "shadow_master"

    # 2. EDUCATIONAL
    if _has_word(combined, "quiz", "flashcard", "flashcards", "educational", "learning",
                 "study tutor", "study app", "exam prep", "trivia", "flash card"):
        return "educational"

    # 3. DASHBOARD
    if _has_word(combined, "analytics", "kpi", "dashboard", "metric", "metrics", "executive",
                 "revenue", "bi", "business intelligence", "financial dashboard"):
        return "analytics"

    # 4. MANAGEMENT (Negative check: "production management" is management, NOT ecommerce)
    if _has_word(combined, "teamconnect", "directory", "member directory", "employee directory",
                 "roster", "staff", "faculty", "hr portal", "admin portal", "school management",
                 "student portal", "production management", "operations management", "personnel"):
        return "management"

    # 5. E-COMMERCE (Negative check: "productivity" and "production" MUST NOT match)
    if _has_word(combined, "shop", "store", "storefront", "ecommerce", "e-commerce",
                 "shopping cart", "product catalog", "checkout flow", "merchandise store", "marketplace", "retail"):
        return "ecommerce"

    # 5.5 INVENTORY & LMS
    if _has_word(combined, "inventory", "warehouse", "stock", "sku", "supply chain", "stock adjustment", "replenishment"):
        return "inventory"

    if _has_word(combined, "lms", "learning management", "online academy", "course platform", "curriculum", "courses", "lessons", "student progress"):
        return "lms"

    # 6. EVENTHUB & TASKFLOW
    if _has_word(combined, "eventhub", "event booking", "ticket booking", "conference registration", "summit booking"):
        return "eventhub"

    if _has_word(combined, "kanban", "taskflow", "task manager", "tasks", "todo", "to-do",
                 "backlog", "scrum", "sprint board", "productivity application", "productivity app", "project tracker"):
        return "taskflow"

    # Fallback for general categories
    cat = classify_application_category(name, desc, slug)
    if cat == "GAME":
        if _has_word(combined, "board game", "turn-based board"):
            return "chess"
        return "custom"
    if cat == "EDUCATIONAL":
        return "educational"
    if cat == "DASHBOARD":
        return "analytics"
    if cat == "MANAGEMENT":
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


    if archetype in ("space_arcade", "arcade_2d", "space_defender"):
        return [
            {"path": "frontend/package.json", "purpose": "Frontend package manifest with React 18 and Vite", "file_type": "DEPENDENCY", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/index.html", "purpose": "Vite HTML5 entrypoint and 60 FPS Canvas 2D Space Arcade game engine", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/main.tsx", "purpose": "React application bootstrapper and root DOM renderer", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": ["frontend/src/App.tsx", "frontend/src/styles/App.css"]},
            {"path": "frontend/src/App.tsx", "purpose": "Interactive React Space Arcade game coordinating canvas loop, HUD, ship controls, and high scores", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": ["frontend/src/components/ArcadeCanvas.tsx", "frontend/src/components/GameHud.tsx", "frontend/src/services/api.ts"]},
            {"path": "frontend/src/components/ArcadeCanvas.tsx", "purpose": "HTML5 Canvas loop rendering player starship, dual lasers, alien fleet, and explosions", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/components/GameHud.tsx", "purpose": "Live avionics HUD showing score, wave, shield integrity, and high score", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/services/api.ts", "purpose": "REST API client connecting to FastAPI backend for arcade high scores", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/styles/App.css", "purpose": "Neon sci-fi arcade theme styling with responsive layout and glassmorphism HUD", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": [], "dependencies": []},
            {"path": "backend/requirements.txt", "purpose": "Python package dependencies including FastAPI, Uvicorn, and Pydantic", "file_type": "DEPENDENCY", "architecture_component": be_comp_name, "requirement_ids": [], "dependencies": []},
            {"path": "backend/app/main.py", "purpose": "FastAPI application entrypoint with CORS middleware and preview static serving", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/config.py", "backend/app/api.py"]},
            {"path": "backend/app/config.py", "purpose": "Application configuration and environment CORS settings", "file_type": "CONFIG", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": []},
            {"path": "backend/app/models.py", "purpose": "Pydantic domain schemas for space arcade scores and pilot records", "file_type": "SCHEMA", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": []},
            {"path": "backend/app/api.py", "purpose": "REST endpoint router handling arcade score submissions and leaderboard records", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/models.py", "backend/app/persistence.py"]},
            {"path": "backend/app/persistence.py", "purpose": "Thread-safe space arcade high score and leaderboard persistence", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/models.py"]},
            {"path": "README.md", "purpose": "Project documentation with gameplay controls, weapon systems, and architecture", "file_type": "DOCUMENTATION", "architecture_component": None, "requirement_ids": [], "dependencies": []},
        ]

    if archetype in ("sky_strike", "aerial_combat"):
        return [
            {"path": "frontend/package.json", "purpose": "Frontend package manifest with React 18, Vite, and Lucide icons", "file_type": "DEPENDENCY", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/index.html", "purpose": "Vite HTML5 entrypoint and 60 FPS Canvas Aerial Combat dogfight simulator", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/main.tsx", "purpose": "React application bootstrapper and root DOM renderer", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": ["frontend/src/App.tsx", "frontend/src/styles/App.css"]},
            {"path": "frontend/src/App.tsx", "purpose": "Interactive React Sky Strike combat simulator coordinating flight loop, avionics HUD, and radar", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": ["frontend/src/components/FlightArena.tsx", "frontend/src/components/AvionicsHud.tsx", "frontend/src/services/api.ts"]},
            {"path": "frontend/src/components/FlightArena.tsx", "purpose": "HTML5 Canvas loop rendering fighter jet, missile contrails, enemy bogies, and radar", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/components/AvionicsHud.tsx", "purpose": "Avionics HUD showing throttle gauge, hull integrity, altitude, and missile count", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/services/api.ts", "purpose": "REST API client connecting to FastAPI backend for mission flight telemetry", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/styles/App.css", "purpose": "Military aviation HUD theme styling with glowing cyan reticles and carbon fiber panels", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": [], "dependencies": []},
            {"path": "backend/requirements.txt", "purpose": "Python package dependencies including FastAPI, Uvicorn, and Pydantic", "file_type": "DEPENDENCY", "architecture_component": be_comp_name, "requirement_ids": [], "dependencies": []},
            {"path": "backend/app/main.py", "purpose": "FastAPI application entrypoint with CORS middleware and preview serving", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/config.py", "backend/app/api.py"]},
            {"path": "backend/app/config.py", "purpose": "Application configuration and environment CORS settings", "file_type": "CONFIG", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": []},
            {"path": "backend/app/models.py", "purpose": "Pydantic domain schemas for aerial combat stats, dogfight score, and aircraft loadout", "file_type": "SCHEMA", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": []},
            {"path": "backend/app/api.py", "purpose": "REST endpoint router handling combat score submissions and mission telemetry", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/models.py", "backend/app/persistence.py"]},
            {"path": "backend/app/persistence.py", "purpose": "Thread-safe aerial combat telemetry and ace pilot score repository", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/models.py"]},
            {"path": "README.md", "purpose": "Project documentation with Sky Strike flight controls, avionics guide, and architecture", "file_type": "DOCUMENTATION", "architecture_component": None, "requirement_ids": [], "dependencies": []},
        ]

    if archetype == "inventory":
        return [
            {"path": "frontend/package.json", "purpose": "Frontend package manifest with React 18, Vite, and Lucide icons", "file_type": "DEPENDENCY", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/index.html", "purpose": "Vite HTML5 entrypoint and enterprise warehouse inventory control platform", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/main.tsx", "purpose": "React application bootstrapper and root DOM renderer", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": ["frontend/src/App.tsx", "frontend/src/styles/App.css"]},
            {"path": "frontend/src/App.tsx", "purpose": "Enterprise inventory dashboard coordinating SKU catalog, stock adjustment modal, and audit ledger", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": ["frontend/src/components/SkuTable.tsx", "frontend/src/components/StockAdjustmentModal.tsx", "frontend/src/services/api.ts"]},
            {"path": "frontend/src/components/SkuTable.tsx", "purpose": "Searchable and filterable SKU table with stock badges and adjustment trigger", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/components/StockAdjustmentModal.tsx", "purpose": "Modal dialog for recording inbound receipts and outbound dispatches with reason audit", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/services/api.ts", "purpose": "REST API client connecting to FastAPI backend inventory and adjustment endpoints", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/styles/App.css", "purpose": "Modern enterprise warehouse styling with low-stock badges and responsive data grids", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": [], "dependencies": []},
            {"path": "backend/requirements.txt", "purpose": "Python package dependencies including FastAPI, Uvicorn, and Pydantic", "file_type": "DEPENDENCY", "architecture_component": be_comp_name, "requirement_ids": [], "dependencies": []},
            {"path": "backend/app/main.py", "purpose": "FastAPI application entrypoint with CORS middleware and preview static serving", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/config.py", "backend/app/api.py"]},
            {"path": "backend/app/config.py", "purpose": "Application configuration and environment CORS settings", "file_type": "CONFIG", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": []},
            {"path": "backend/app/models.py", "purpose": "Pydantic domain schemas for inventory products, stock adjustments, and stats", "file_type": "SCHEMA", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": []},
            {"path": "backend/app/api.py", "purpose": "REST endpoint router handling SKU catalog CRUD, stock adjustments, and CSV export", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/models.py", "backend/app/persistence.py"]},
            {"path": "backend/app/persistence.py", "purpose": "SQLite-backed thread-safe inventory repository and adjustment audit ledger", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/models.py"]},
            {"path": "README.md", "purpose": "Project documentation with SKU taxonomy, stock adjustment rules, and architecture", "file_type": "DOCUMENTATION", "architecture_component": None, "requirement_ids": [], "dependencies": []},
        ]

    if archetype == "lms":
        return [
            {"path": "frontend/package.json", "purpose": "Frontend package manifest with React 18, Vite, and Lucide icons", "file_type": "DEPENDENCY", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/index.html", "purpose": "Vite HTML5 entrypoint and SkillForge Online Academy learning portal", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/main.tsx", "purpose": "React application bootstrapper and root DOM renderer", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": ["frontend/src/App.tsx", "frontend/src/styles/App.css"]},
            {"path": "frontend/src/App.tsx", "purpose": "Online Academy portal coordinating course catalog, interactive lesson player, and quiz engine", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": ["frontend/src/components/CourseCatalog.tsx", "frontend/src/components/LessonPlayer.tsx", "frontend/src/services/api.ts"]},
            {"path": "frontend/src/components/CourseCatalog.tsx", "purpose": "Course catalog with category filter, enrollment trigger, and progress percentage", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/components/LessonPlayer.tsx", "purpose": "Interactive syllabus lesson player with complete lesson checklist and knowledge quiz", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/services/api.ts", "purpose": "REST API client connecting to FastAPI backend courses and progress endpoints", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/styles/App.css", "purpose": "Modern academy theme styling with student progress meters and lesson cards", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": [], "dependencies": []},
            {"path": "backend/requirements.txt", "purpose": "Python package dependencies including FastAPI, Uvicorn, and Pydantic", "file_type": "DEPENDENCY", "architecture_component": be_comp_name, "requirement_ids": [], "dependencies": []},
            {"path": "backend/app/main.py", "purpose": "FastAPI application entrypoint with CORS middleware and preview static serving", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/config.py", "backend/app/api.py"]},
            {"path": "backend/app/config.py", "purpose": "Application configuration and environment CORS settings", "file_type": "CONFIG", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": []},
            {"path": "backend/app/models.py", "purpose": "Pydantic domain schemas for courses, lessons, student progress, and quizzes", "file_type": "SCHEMA", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": []},
            {"path": "backend/app/api.py", "purpose": "REST endpoint router handling course catalog browsing, lesson completion, and quiz scoring", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/models.py", "backend/app/persistence.py"]},
            {"path": "backend/app/persistence.py", "purpose": "SQLite-backed thread-safe student academy progress and course repository", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/models.py"]},
            {"path": "README.md", "purpose": "Project documentation with course syllabus structure, quiz grading, and architecture", "file_type": "DOCUMENTATION", "architecture_component": None, "requirement_ids": [], "dependencies": []},
        ]

    if archetype == "shadow_master":
        return [
            {"path": "frontend/package.json", "purpose": "Frontend package manifest with React 18, Vite, and Lucide icons", "file_type": "DEPENDENCY", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/index.html", "purpose": "Vite HTML5 entrypoint with 60 FPS Canvas Shadow Master combat arena and real-time skill builder", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/main.tsx", "purpose": "React application bootstrapper and root DOM renderer", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": ["frontend/src/App.tsx", "frontend/src/styles/App.css"]},
            {"path": "frontend/src/App.tsx", "purpose": "Interactive React Shadow Master application coordinating combat arena, stats HUD, and live skill builder", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": ["frontend/src/components/CombatArena.tsx", "frontend/src/components/SkillDesigner.tsx", "frontend/src/components/StatsPanel.tsx", "frontend/src/services/api.ts"]},
            {"path": "frontend/src/components/CombatArena.tsx", "purpose": "HTML5 Canvas combat arena with player shadow physics, ability hotbar, and enemy targets", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/components/SkillDesigner.tsx", "purpose": "Interactive skill customizer allowing live tuning of damage, energy cost, cooldown, and JSON export", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/components/StatsPanel.tsx", "purpose": "Player combat stats HUD with health bar, shadow energy meter, level progression, and combo streak", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/services/api.ts", "purpose": "REST API client connecting to FastAPI backend for skill definition sync and combat scores", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/styles/App.css", "purpose": "Dark fantasy ninja theme styling with obsidian cards, glowing purple borders, and combat HUD", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": [], "dependencies": []},
            {"path": "backend/requirements.txt", "purpose": "Python package dependencies including FastAPI, Uvicorn, and Pydantic", "file_type": "DEPENDENCY", "architecture_component": be_comp_name, "requirement_ids": [], "dependencies": []},
            {"path": "backend/app/main.py", "purpose": "FastAPI application entrypoint with CORS middleware and preview static serving", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/config.py", "backend/app/api.py"]},
            {"path": "backend/app/config.py", "purpose": "Application configuration and environment CORS settings", "file_type": "CONFIG", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": []},
            {"path": "backend/app/models.py", "purpose": "Pydantic domain schemas for shadow skill definitions, combat stats, and player scores", "file_type": "SCHEMA", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": []},
            {"path": "backend/app/api.py", "purpose": "REST endpoint router handling skill customization CRUD, JSON export, and combat scores", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/models.py", "backend/app/persistence.py"]},
            {"path": "backend/app/persistence.py", "purpose": "Thread-safe shadow skills repository and combat high score storage", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/models.py"]},
            {"path": "README.md", "purpose": "Project documentation with Shadow Master skill mechanics, controls guide, and architecture", "file_type": "DOCUMENTATION", "architecture_component": None, "requirement_ids": [], "dependencies": []},
        ]

    if archetype == "carrom":
        return [
            {"path": "frontend/package.json", "purpose": "Frontend package manifest with React 18, Vite, and Lucide icons", "file_type": "DEPENDENCY", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/index.html", "purpose": "Vite HTML5 entrypoint and interactive Carrom board canvas game container", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/main.tsx", "purpose": "React application bootstrapper and root DOM renderer", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": ["frontend/src/App.tsx", "frontend/src/styles/App.css"]},
            {"path": "frontend/src/App.tsx", "purpose": "Interactive React Carrom Master game with physics loop, striker aiming, scoreboard, and turns", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": ["frontend/src/components/ScoreBoard.tsx", "frontend/src/components/GameControls.tsx", "frontend/src/services/api.ts"]},
            {"path": "frontend/src/components/ScoreBoard.tsx", "purpose": "Scoreboard component displaying Player 1 & 2 scores, turns, and Queen status", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/components/GameControls.tsx", "purpose": "Striker position slider, power meter gauge, shoot button, and reset controls", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/services/api.ts", "purpose": "REST API client connecting to FastAPI backend for game score submission", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/styles/App.css", "purpose": "Polished Carrom board theme styling with wooden border gradients and glassmorphism HUD", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": [], "dependencies": []},
            {"path": "backend/requirements.txt", "purpose": "Python package dependencies including FastAPI, Uvicorn, and Pydantic", "file_type": "DEPENDENCY", "architecture_component": be_comp_name, "requirement_ids": [], "dependencies": []},
            {"path": "backend/app/main.py", "purpose": "FastAPI application entrypoint with CORS middleware and preview serving", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/config.py", "backend/app/api.py"]},
            {"path": "backend/app/config.py", "purpose": "Application configuration and environment CORS settings", "file_type": "CONFIG", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": []},
            {"path": "backend/app/models.py", "purpose": "Pydantic domain schemas for carrom game score records and player stats", "file_type": "SCHEMA", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": []},
            {"path": "backend/app/api.py", "purpose": "REST endpoint router handling carrom score submissions and leaderboard records", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/models.py", "backend/app/persistence.py"]},
            {"path": "backend/app/persistence.py", "purpose": "Thread-safe carrom score and game state persistence repository", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/models.py"]},
            {"path": "README.md", "purpose": "Project documentation with Carrom Master gameplay rules, striker physics, and controls", "file_type": "DOCUMENTATION", "architecture_component": None, "requirement_ids": [], "dependencies": []},
        ]

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


    if archetype == "chess":
        return [
            {"path": "frontend/package.json", "purpose": "Frontend package manifest with React 18 and Vite", "file_type": "DEPENDENCY", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/index.html", "purpose": "Vite HTML5 entrypoint and interactive 8x8 Chessboard strategy engine", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/main.tsx", "purpose": "React application bootstrapper and root DOM renderer", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": ["frontend/src/App.tsx", "frontend/src/styles/App.css"]},
            {"path": "frontend/src/App.tsx", "purpose": "Interactive React Chess game coordinating board state, moves history, and turn transitions", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": ["frontend/src/components/ChessBoard.tsx", "frontend/src/components/MoveHistory.tsx", "frontend/src/services/api.ts"]},
            {"path": "frontend/src/components/ChessBoard.tsx", "purpose": "8x8 Chessboard grid with piece selection and legal move indicators", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/components/MoveHistory.tsx", "purpose": "Move notation history log and captured pieces tray", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/services/api.ts", "purpose": "REST API client connecting to FastAPI backend for match state and move history", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/styles/App.css", "purpose": "Classic wooden chessboard theme and modern glassmorphism panels", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": [], "dependencies": []},
            {"path": "backend/requirements.txt", "purpose": "Backend Python package dependencies for FastAPI and Pydantic", "file_type": "DEPENDENCY", "architecture_component": be_comp_name, "requirement_ids": [], "dependencies": []},
            {"path": "backend/app/main.py", "purpose": "FastAPI application entrypoint with CORS middleware and preview serving", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/config.py", "backend/app/api.py"]},
            {"path": "backend/app/config.py", "purpose": "Application configuration and environment CORS settings", "file_type": "CONFIG", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": []},
            {"path": "backend/app/models.py", "purpose": "Pydantic domain schemas for chess move records and board states", "file_type": "SCHEMA", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": []},
            {"path": "backend/app/api.py", "purpose": "REST API route handlers for chess moves and match lifecycle", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/models.py", "backend/app/persistence.py"]},
            {"path": "backend/app/persistence.py", "purpose": "Thread-safe chess match state and move persistence repository", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/models.py"]},
            {"path": "README.md", "purpose": "Architecture overview and chess rules documentation", "file_type": "DOCUMENTATION", "architecture_component": None, "requirement_ids": [], "dependencies": []},
        ]

    if archetype == "platformer":
        return [
            {"path": "frontend/package.json", "purpose": "Frontend package manifest with React 18 and Vite", "file_type": "DEPENDENCY", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/index.html", "purpose": "Vite HTML5 entrypoint and 60 FPS Canvas 2D Platformer engine", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/main.tsx", "purpose": "React application bootstrapper and root DOM renderer", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": ["frontend/src/App.tsx", "frontend/src/styles/App.css"]},
            {"path": "frontend/src/App.tsx", "purpose": "Interactive React 2D Platformer game coordinating jump physics, coins HUD, and score", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": ["frontend/src/components/PlatformerCanvas.tsx", "frontend/src/components/GameHud.tsx", "frontend/src/services/api.ts"]},
            {"path": "frontend/src/components/PlatformerCanvas.tsx", "purpose": "HTML5 Canvas platformer loop with player gravity, platforms, and coin collisions", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/components/GameHud.tsx", "purpose": "Lives counter, stage level, and score tally HUD", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/services/api.ts", "purpose": "REST API client connecting to FastAPI backend for platformer scores and leaderboards", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/styles/App.css", "purpose": "Retro synthwave arcade theme styling", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": [], "dependencies": []},
            {"path": "backend/requirements.txt", "purpose": "Backend Python package dependencies for FastAPI and Pydantic", "file_type": "DEPENDENCY", "architecture_component": be_comp_name, "requirement_ids": [], "dependencies": []},
            {"path": "backend/app/main.py", "purpose": "FastAPI application entrypoint with CORS middleware and preview serving", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/config.py", "backend/app/api.py"]},
            {"path": "backend/app/config.py", "purpose": "Application configuration and environment CORS settings", "file_type": "CONFIG", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": []},
            {"path": "backend/app/models.py", "purpose": "Pydantic domain schemas for platformer high scores and level completions", "file_type": "SCHEMA", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": []},
            {"path": "backend/app/api.py", "purpose": "REST API route handlers for platformer scores and level data", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/models.py", "backend/app/persistence.py"]},
            {"path": "backend/app/persistence.py", "purpose": "Thread-safe high score repository and level store", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/models.py"]},
            {"path": "README.md", "purpose": "Architecture overview and platformer controls guide", "file_type": "DOCUMENTATION", "architecture_component": None, "requirement_ids": [], "dependencies": []},
        ]

    if archetype == "racing":
        return [
            {"path": "frontend/package.json", "purpose": "Frontend package manifest with React 18 and Vite", "file_type": "DEPENDENCY", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/index.html", "purpose": "Vite HTML5 entrypoint and 60 FPS Canvas Top-Down Racing simulator", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/main.tsx", "purpose": "React application bootstrapper and root DOM renderer", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": ["frontend/src/App.tsx", "frontend/src/styles/App.css"]},
            {"path": "frontend/src/App.tsx", "purpose": "Interactive React Racing simulator coordinating car telemetry, laps, and speed gauge", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": ["frontend/src/components/RaceCanvas.tsx", "frontend/src/components/TelemetryBar.tsx", "frontend/src/services/api.ts"]},
            {"path": "frontend/src/components/RaceCanvas.tsx", "purpose": "HTML5 Canvas racing loop with car steering, acceleration physics, and track barriers", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/components/TelemetryBar.tsx", "purpose": "Speedometer gauge, lap time counter, and nitro boost indicators", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/services/api.ts", "purpose": "REST API client connecting to FastAPI backend for lap times and racing records", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/styles/App.css", "purpose": "Motorsport speedway theme with carbon fiber panels and amber accents", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": [], "dependencies": []},
            {"path": "backend/requirements.txt", "purpose": "Backend Python package dependencies for FastAPI and Pydantic", "file_type": "DEPENDENCY", "architecture_component": be_comp_name, "requirement_ids": [], "dependencies": []},
            {"path": "backend/app/main.py", "purpose": "FastAPI application entrypoint with CORS middleware and preview serving", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/config.py", "backend/app/api.py"]},
            {"path": "backend/app/config.py", "purpose": "Application configuration and environment CORS settings", "file_type": "CONFIG", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": []},
            {"path": "backend/app/models.py", "purpose": "Pydantic domain schemas for race times, laps, and driver telemetry", "file_type": "SCHEMA", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": []},
            {"path": "backend/app/api.py", "purpose": "REST API route handlers for lap records and circuit telemetry", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/models.py", "backend/app/persistence.py"]},
            {"path": "backend/app/persistence.py", "purpose": "Thread-safe race records repository", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/models.py"]},
            {"path": "README.md", "purpose": "Architecture overview and racing controls guide", "file_type": "DOCUMENTATION", "architecture_component": None, "requirement_ids": [], "dependencies": []},
        ]

    if archetype == "puzzle":
        return [
            {"path": "frontend/package.json", "purpose": "Frontend package manifest with React 18 and Vite", "file_type": "DEPENDENCY", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/index.html", "purpose": "Vite HTML5 entrypoint and interactive 15-Puzzle Sliding Challenge", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/main.tsx", "purpose": "React application bootstrapper and root DOM renderer", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": ["frontend/src/App.tsx", "frontend/src/styles/App.css"]},
            {"path": "frontend/src/App.tsx", "purpose": "Interactive React 15-Puzzle game coordinating sliding tiles, move counter, and timer", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": ["frontend/src/components/PuzzleBoard.tsx", "frontend/src/components/PuzzleStats.tsx", "frontend/src/services/api.ts"]},
            {"path": "frontend/src/components/PuzzleBoard.tsx", "purpose": "4x4 Grid of sliding number tiles with neighbor click detection and smooth transitions", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/components/PuzzleStats.tsx", "purpose": "Move counter, timer stopwatch, and win status banner", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/services/api.ts", "purpose": "REST API client connecting to FastAPI backend for best move solutions and times", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/styles/App.css", "purpose": "Emerald green puzzle theme with tactile tile animations", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": [], "dependencies": []},
            {"path": "backend/requirements.txt", "purpose": "Backend Python package dependencies for FastAPI and Pydantic", "file_type": "DEPENDENCY", "architecture_component": be_comp_name, "requirement_ids": [], "dependencies": []},
            {"path": "backend/app/main.py", "purpose": "FastAPI application entrypoint with CORS middleware and preview serving", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/config.py", "backend/app/api.py"]},
            {"path": "backend/app/config.py", "purpose": "Application configuration and environment CORS settings", "file_type": "CONFIG", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": []},
            {"path": "backend/app/models.py", "purpose": "Pydantic domain schemas for puzzle solutions and best completion times", "file_type": "SCHEMA", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": []},
            {"path": "backend/app/api.py", "purpose": "REST API route handlers for puzzle records and moves", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/models.py", "backend/app/persistence.py"]},
            {"path": "backend/app/persistence.py", "purpose": "Thread-safe puzzle records repository", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/models.py"]},
            {"path": "README.md", "purpose": "Architecture overview and puzzle rules guide", "file_type": "DOCUMENTATION", "architecture_component": None, "requirement_ids": [], "dependencies": []},
        ]

    if archetype == "educational":
        return [
            {"path": "frontend/package.json", "purpose": "Frontend package manifest with React 18 and Vite", "file_type": "DEPENDENCY", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/index.html", "purpose": "Vite HTML5 entrypoint and interactive StudyDeck Flashcards & Quiz platform", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/main.tsx", "purpose": "React application bootstrapper and root DOM renderer", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": ["frontend/src/App.tsx", "frontend/src/styles/App.css"]},
            {"path": "frontend/src/App.tsx", "purpose": "Interactive React learning platform coordinating flashcard 3D flips, quiz mode, and deck mastery", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": ["frontend/src/components/FlashcardDeck.tsx", "frontend/src/components/QuizRunner.tsx", "frontend/src/services/api.ts"]},
            {"path": "frontend/src/components/FlashcardDeck.tsx", "purpose": "Flashcard component with 3D flip animation, definition reveal, and next/prev navigation", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/components/QuizRunner.tsx", "purpose": "Multiple-choice interactive quiz runner with instant answer validation and score tally", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/services/api.ts", "purpose": "REST API client connecting to FastAPI backend for study decks and quiz scores", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/styles/App.css", "purpose": "Modern indigo educational theme with clean typography and study card transitions", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": [], "dependencies": []},
            {"path": "backend/requirements.txt", "purpose": "Backend Python package dependencies for FastAPI and Pydantic", "file_type": "DEPENDENCY", "architecture_component": be_comp_name, "requirement_ids": [], "dependencies": []},
            {"path": "backend/app/main.py", "purpose": "FastAPI application entrypoint with CORS middleware and preview serving", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/config.py", "backend/app/api.py"]},
            {"path": "backend/app/config.py", "purpose": "Application configuration and environment CORS settings", "file_type": "CONFIG", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": []},
            {"path": "backend/app/models.py", "purpose": "Pydantic domain schemas for study cards, decks, and quiz completion records", "file_type": "SCHEMA", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": []},
            {"path": "backend/app/api.py", "purpose": "REST API route handlers for study deck browsing and score submissions", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/models.py", "backend/app/persistence.py"]},
            {"path": "backend/app/persistence.py", "purpose": "Thread-safe study deck repository and quiz progress store", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/models.py"]},
            {"path": "README.md", "purpose": "Architecture overview and study guide documentation", "file_type": "DOCUMENTATION", "architecture_component": None, "requirement_ids": [], "dependencies": []},
        ]

    if archetype == "custom":
        return [
            {"path": "frontend/package.json", "purpose": "Frontend package manifest with React 18 and Vite", "file_type": "DEPENDENCY", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/index.html", "purpose": "Vite HTML5 entrypoint and interactive Application Dashboard", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/main.tsx", "purpose": "React application bootstrapper and root DOM renderer", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": ["frontend/src/App.tsx", "frontend/src/styles/App.css"]},
            {"path": "frontend/src/App.tsx", "purpose": "Interactive React domain data manager with KPI cards, search table, item creation modal, and CSV export", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": ["frontend/src/components/DataExplorer.tsx", "frontend/src/components/SummaryCards.tsx", "frontend/src/components/ItemModal.tsx", "frontend/src/services/api.ts"]},
            {"path": "frontend/src/components/DataExplorer.tsx", "purpose": "Interactive domain record table with live search filtering, status toggling, and delete triggers", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/components/SummaryCards.tsx", "purpose": "KPI metric summary cards showing total records, active status, and completion rate", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/components/ItemModal.tsx", "purpose": "Modal dialog component for creating and editing domain entities with validation", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/services/api.ts", "purpose": "REST API client connecting to FastAPI backend for domain entity CRUD operations", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/styles/App.css", "purpose": "Modern dark slate theme with glowing indigo accents and responsive grid", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": [], "dependencies": []},
            {"path": "backend/requirements.txt", "purpose": "Backend Python package dependencies for FastAPI and Pydantic", "file_type": "DEPENDENCY", "architecture_component": be_comp_name, "requirement_ids": [], "dependencies": []},
            {"path": "backend/app/main.py", "purpose": "FastAPI application entrypoint with CORS middleware and preview serving", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/config.py", "backend/app/api.py"]},
            {"path": "backend/app/config.py", "purpose": "Application configuration and environment CORS settings", "file_type": "CONFIG", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": []},
            {"path": "backend/app/models.py", "purpose": "Pydantic domain schemas for custom application entity records and payloads", "file_type": "SCHEMA", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": []},
            {"path": "backend/app/api.py", "purpose": "REST API route handlers for domain entity CRUD operations and export", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/models.py", "backend/app/persistence.py"]},
            {"path": "backend/app/persistence.py", "purpose": "Thread-safe repository for domain entity persistence", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/models.py"]},
            {"path": "README.md", "purpose": "Architecture overview and operational guide for custom application", "file_type": "DOCUMENTATION", "architecture_component": None, "requirement_ids": [], "dependencies": []},
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

    # Authoritative Enterprise Domain Templates (P0 Milestone 2 Upgrade)
    try:
        from app.agents.code_generation.domain_templates import get_domain_file_content
        domain_code = get_domain_file_content(archetype, norm_path, project_name, project_desc)
        if domain_code is not None:
            return domain_code
    except Exception:
        pass

    # -------------------------------------------------------------
    # Archetype: SPACE ARCADE DEFENDER (space_arcade)
    # -------------------------------------------------------------
    if archetype in ("space_arcade", "arcade_2d", "space_defender"):
        if norm_path == "frontend/index.html":
            from app.runtime.preview_server import get_space_arcade_game_html
            return get_space_arcade_game_html(title=project_name, desc=project_desc)

        if norm_path == "frontend/src/App.tsx":
            return (
                "import React, { useState, useEffect } from 'react';\n"
                "import { getScores, submitScore, ScoreRecord } from './services/api';\n"
                "import './styles/App.css';\n\n"
                "export default function App() {\n"
                "  const [scores, setScores] = useState<ScoreRecord[]>([]);\n"
                "  const [activeTab, setActiveTab] = useState<'arena' | 'leaderboard'>('arena');\n\n"
                "  useEffect(() => {\n"
                "    getScores().then(setScores).catch(() => {});\n"
                "  }, []);\n\n"
                "  return (\n"
                "    <div className=\"arcade-container\">\n"
                "      <header className=\"arcade-header\">\n"
                "        <h1>" + project_name + "</h1>\n"
                "        <nav className=\"arcade-nav\">\n"
                "          <button className={activeTab === 'arena' ? 'active' : ''} onClick={() => setActiveTab('arena')}>Space Arena</button>\n"
                "          <button className={activeTab === 'leaderboard' ? 'active' : ''} onClick={() => setActiveTab('leaderboard')}>Leaderboard</button>\n"
                "        </nav>\n"
                "      </header>\n"
                "      <main className=\"arcade-main\">\n"
                "        {activeTab === 'arena' ? (\n"
                "          <div className=\"game-viewport\">\n"
                "            <iframe src=\"/preview?app=space_arcade\" title=\"Space Arcade\" className=\"game-frame\" />\n"
                "          </div>\n"
                "        ) : (\n"
                "          <div className=\"leaderboard-panel\">\n"
                "            <h3>Top Ace Pilots</h3>\n"
                "            <ul>{scores.map((s, i) => <li key={i}>{s.player_name}: {s.score} pts</li>)}</ul>\n"
                "          </div>\n"
                "        )}\n"
                "      </main>\n"
                "    </div>\n"
                "  );\n"
                "}\n"
            )

    # -------------------------------------------------------------
    # Archetype: SKY STRIKE (sky_strike)
    # -------------------------------------------------------------
    if archetype in ("sky_strike", "aerial_combat"):
        if norm_path == "frontend/index.html":
            from app.runtime.preview_server import get_sky_strike_game_html
            return get_sky_strike_game_html(title=project_name, desc=project_desc)

        if norm_path == "frontend/src/App.tsx":
            return (
                "import React, { useState } from 'react';\n"
                "import './styles/App.css';\n\n"
                "export default function App() {\n"
                "  return (\n"
                "    <div className=\"skystrike-wrapper\">\n"
                "      <iframe src=\"/preview?app=sky_strike\" title=\"Sky Strike Aerial Combat\" className=\"game-frame\" />\n"
                "    </div>\n"
                "  );\n"
                "}\n"
            )

    # -------------------------------------------------------------
    # Archetype: APEX INVENTORY (inventory)
    # -------------------------------------------------------------
    if archetype == "inventory":
        if norm_path == "frontend/index.html":
            from app.runtime.preview_medium_complexity import get_inventory_html
            return get_inventory_html(title=project_name, desc=project_desc)

        if norm_path == "frontend/src/App.tsx":
            return (
                "import React, { useState } from 'react';\n"
                "import './styles/App.css';\n\n"
                "export default function App() {\n"
                "  return (\n"
                "    <div className=\"inventory-app-wrapper\">\n"
                "      <iframe src=\"/preview?app=inventory\" title=\"Apex Inventory\" className=\"app-frame\" />\n"
                "    </div>\n"
                "  );\n"
                "}\n"
            )

    # -------------------------------------------------------------
    # Archetype: SKILLFORGE ONLINE ACADEMY (lms)
    # -------------------------------------------------------------
    if archetype == "lms":
        if norm_path == "frontend/index.html":
            from app.runtime.preview_medium_complexity import get_lms_html
            return get_lms_html(title=project_name, desc=project_desc)

        if norm_path == "frontend/src/App.tsx":
            return (
                "import React, { useState } from 'react';\n"
                "import './styles/App.css';\n\n"
                "export default function App() {\n"
                "  return (\n"
                "    <div className=\"lms-app-wrapper\">\n"
                "      <iframe src=\"/preview?app=lms\" title=\"SkillForge Academy\" className=\"app-frame\" />\n"
                "    </div>\n"
                "  );\n"
                "}\n"
            )



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
    # -------------------------------------------------------------
    # -------------------------------------------------------------
    # -------------------------------------------------------------
    # Archetype: CHESS MASTER (chess)
    # -------------------------------------------------------------
    if archetype == "chess":
        if norm_path == "frontend/index.html":
            from app.runtime.preview_server import get_chess_game_html
            return get_chess_game_html(title=project_name, desc=project_desc)

        if norm_path == "frontend/src/main.tsx":
            return (
                "import React from 'react';\n"
                "import ReactDOM from 'react-dom/client';\n"
                "import App from './App';\n"
                "import './styles/App.css';\n\n"
                "ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(\n"
                "  <React.StrictMode>\n"
                "    <App />\n"
                "  </React.StrictMode>\n"
                ");\n"
            )

        if norm_path == "frontend/src/App.tsx":
            return (
                "import React, { useState } from 'react';\n"
                "import ChessBoard from './components/ChessBoard';\n"
                "import MoveHistory from './components/MoveHistory';\n"
                "import { chessApi } from './services/api';\n\n"
                "export default function App() {\n"
                "  const [turn, setTurn] = useState<'white' | 'black'>('white');\n"
                "  const [moves, setMoves] = useState<string[]>([]);\n"
                "  const handleMove = (m: string) => {\n"
                "    setMoves(prev => [...prev, m]);\n"
                "    setTurn(t => t === 'white' ? 'black' : 'white');\n"
                "    chessApi.recordMove(m);\n"
                "  };\n\n"
                "  return (\n"
                "    <div className=\"chess-app-root\">\n"
                f'      <header><h1>{project_name}</h1><p>{project_desc}</p></header>\n'
                "      <div className=\"chess-content-wrap\">\n"
                "        <ChessBoard turn={turn} onMove={handleMove} />\n"
                "        <MoveHistory moves={moves} turn={turn} onReset={() => setMoves([])} />\n"
                "      </div>\n"
                "    </div>\n"
                "  );\n"
                "}\n"
            )

        if norm_path == "frontend/src/components/ChessBoard.tsx":
            return (
                "import React, { useState } from 'react';\n\n"
                "interface Props { turn: 'white' | 'black'; onMove: (m: string) => void; }\n"
                "const PIECES: Record<string, string> = { 'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚', 'p': '♟', 'R': '♖', 'N': '♘', 'B': '♗', 'Q': '♕', 'K': '♔', 'P': '♙' };\n"
                "export default function ChessBoard({ turn, onMove }: Props) {\n"
                "  const [selected, setSelected] = useState<[number, number] | null>(null);\n"
                "  return (\n"
                "    <div className=\"chessboard-container\">\n"
                "      <div className=\"board-grid\">\n"
                "        {Array.from({ length: 64 }).map((_, i) => {\n"
                "          const r = Math.floor(i / 8), c = i % 8;\n"
                "          const isLight = (r + c) % 2 === 0;\n"
                "          return (\n"
                "            <div key={i} className={`square ${isLight ? 'light' : 'dark'}`} onClick={() => {\n"
                "              if (selected) { onMove(`${String.fromCharCode(97 + c)}${8 - r}`); setSelected(null); }\n"
                "              else { setSelected([r, c]); }\n"
                "            }} />\n"
                "          );\n"
                "        })}\n"
                "      </div>\n"
                "    </div>\n"
                "  );\n"
                "}\n"
            )

        if norm_path == "frontend/src/components/MoveHistory.tsx":
            return (
                "import React from 'react';\n\n"
                "interface Props { moves: string[]; turn: string; onReset: () => void; }\n"
                "export default function MoveHistory({ moves, turn, onReset }: Props) {\n"
                "  return (\n"
                "    <div className=\"move-history-panel\">\n"
                "      <h3>Turn: {turn.toUpperCase()}</h3>\n"
                "      <div className=\"moves-list\">{moves.map((m, i) => <div key={i}>#{i+1}: {m}</div>)}</div>\n"
                "      <button className=\"btn btn-primary\" onClick={onReset}>New Match</button>\n"
                "    </div>\n"
                "  );\n"
                "}\n"
            )

        if norm_path == "frontend/src/services/api.ts":
            return (
                "export const chessApi = {\n"
                "  async recordMove(move: string): Promise<boolean> {\n"
                "    try {\n"
                "      const res = await fetch('/api/chess/moves', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ move }) });\n"
                "      return res.ok;\n"
                "    } catch { return false; }\n"
                "  }\n"
                "};\n"
            )

        if norm_path == "frontend/src/styles/App.css":
            return (
                ":root { --bg: #0f172a; --light: #eeeed2; --dark: #769656; }\n"
                "body { margin: 0; background: var(--bg); color: #f8fafc; font-family: sans-serif; }\n"
                ".chess-app-root { padding: 1.5rem; text-align: center; }\n"
                ".chess-content-wrap { display: flex; gap: 2rem; justify-content: center; margin-top: 1rem; }\n"
                ".board-grid { display: grid; grid-template-columns: repeat(8, 54px); grid-template-rows: repeat(8, 54px); border: 3px solid #333; }\n"
                ".square { width: 54px; height: 54px; display: flex; align-items: center; justify-content: center; font-size: 32px; cursor: pointer; }\n"
                ".square.light { background: var(--light); color: black; }\n"
                ".square.dark { background: var(--dark); color: black; }\n"
                ".move-history-panel { background: rgba(30, 41, 59, 0.9); padding: 1.25rem; border-radius: 12px; width: 260px; text-align: left; }\n"
            )

        if norm_path in ("backend/app/main.py", "app/main.py"):
            return (
                "from fastapi import FastAPI\n"
                "from fastapi.middleware.cors import CORSMiddleware\n"
                "from fastapi.responses import FileResponse, HTMLResponse\n"
                "from app.config import settings\n"
                "from app.api import router as chess_router\n\n"
                "app = FastAPI(title=settings.app_name, version='1.0.0')\n"
                "app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])\n"
                "app.include_router(chess_router, prefix='/api')\n"
                "@app.get('/health')\ndef health(): return {'status': 'healthy', 'app': settings.app_name}\n"
                "@app.get('/')\ndef root(): return FileResponse('frontend/index.html') if os.path.exists('frontend/index.html') else HTMLResponse('<h1>Chess Ready</h1>')\n"
            )

        if norm_path in ("backend/app/config.py", "app/config.py"):
            return (
                "from pydantic import BaseModel\n"
                "class Settings(BaseModel): app_name: str = 'Chess Master Pro'\n"
                "settings = Settings()\n"
            )

        if norm_path in ("backend/app/models.py", "app/models.py"):
            return (
                "from pydantic import BaseModel\n"
                "class MovePayload(BaseModel): move: str\n"
            )

        if norm_path in ("backend/app/api.py", "app/api.py"):
            return (
                "from fastapi import APIRouter\n"
                "from app.models import MovePayload\n"
                "from app.persistence import repository\n"
                "router = APIRouter(prefix='/chess', tags=['chess'])\n"
                "@router.get('/moves')\ndef get_moves(): return repository.get_moves()\n"
                "@router.post('/moves')\ndef add_move(p: MovePayload): return repository.add_move(p.move)\n"
            )

        if norm_path in ("backend/app/persistence.py", "app/persistence.py"):
            return (
                "import threading\n"
                "class ChessRepository:\n"
                "  def __init__(self): self.lock = threading.Lock(); self.moves = []\n"
                "  def get_moves(self):\n"
                "    with self.lock: return list(self.moves)\n"
                "  def add_move(self, m: str):\n"
                "    with self.lock: self.moves.append(m); return {'status': 'ok', 'move': m}\n"
                "repository = ChessRepository()\n"
            )

        if norm_path == "README.md":
            return f"# {project_name}\n\n{project_desc}\n\n## Chess Strategy Engine\n"

    # -------------------------------------------------------------
    # Archetype: 2D PLATFORMER (platformer)
    # -------------------------------------------------------------
    if archetype == "platformer":
        if norm_path == "frontend/index.html":
            from app.runtime.preview_server import get_platformer_game_html
            return get_platformer_game_html(title=project_name, desc=project_desc)

        if norm_path == "frontend/src/main.tsx":
            return (
                "import React from 'react';\n"
                "import ReactDOM from 'react-dom/client';\n"
                "import App from './App';\n"
                "import './styles/App.css';\n\n"
                "ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(<React.StrictMode><App /></React.StrictMode>);\n"
            )

        if norm_path == "frontend/src/App.tsx":
            return (
                "import React, { useState } from 'react';\n"
                "import PlatformerCanvas from './components/PlatformerCanvas';\n"
                "import GameHud from './components/GameHud';\n"
                "import { gameApi } from './services/api';\n\n"
                "export default function App() {\n"
                "  const [score, setScore] = useState(0);\n"
                "  const [lives, setLives] = useState(3);\n"
                "  return (\n"
                "    <div className=\"platformer-root\">\n"
                f'      <header><h1>{project_name}</h1><p>{project_desc}</p></header>\n'
                "      <GameHud score={score} lives={lives} />\n"
                "      <PlatformerCanvas onScoreUpdate={setScore} onLivesUpdate={setLives} />\n"
                "    </div>\n"
                "  );\n"
                "}\n"
            )

        if norm_path == "frontend/src/components/PlatformerCanvas.tsx":
            return (
                "import React, { useRef, useEffect } from 'react';\n"
                "export default function PlatformerCanvas({ onScoreUpdate, onLivesUpdate }: any) {\n"
                "  const canvasRef = useRef<HTMLCanvasElement | null>(null);\n"
                "  useEffect(() => {\n"
                "    const canvas = canvasRef.current;\n"
                "    if (!canvas) return;\n"
                "    const ctx = canvas.getContext('2d');\n"
                "    if (!ctx) return;\n"
                "    let animId: number;\n"
                "    const loop = () => {\n"
                "      ctx.fillStyle = '#0c0a1d';\n"
                "      ctx.fillRect(0, 0, canvas.width, canvas.height);\n"
                "      ctx.fillStyle = '#ec4899';\n"
                "      ctx.fillRect(80, 260, 24, 32);\n"
                "      ctx.fillStyle = '#6366f1';\n"
                "      ctx.fillRect(0, 320, canvas.width, 30);\n"
                "      animId = requestAnimationFrame(loop);\n"
                "    };\n"
                "    animId = requestAnimationFrame(loop);\n"
                "    return () => cancelAnimationFrame(animId);\n"
                "  }, []);\n"
                "  return <canvas ref={canvasRef} width={750} height={350} className=\"game-canvas\" />;\n"
                "}\n"
            )

        if norm_path == "frontend/src/components/GameHud.tsx":
            return (
                "import React from 'react';\n"
                "export default function GameHud({ score, lives }: { score: number; lives: number }) {\n"
                "  return <div className=\"hud-bar\"><span>SCORE: {score}</span><span>LIVES: {'❤️'.repeat(lives)}</span></div>;\n"
                "}\n"
            )

        if norm_path == "frontend/src/services/api.ts":
            return "export const gameApi = { async submitScore(s: number) { return fetch('/api/platformer/scores', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({score:s}) }); } };\n"

        if norm_path == "frontend/src/styles/App.css":
            return "body { margin: 0; background: #090d16; color: #fff; font-family: sans-serif; text-align: center; } .game-canvas { border: 2px solid #6366f1; border-radius: 12px; margin-top: 1rem; } .hud-bar { display: flex; justify-content: center; gap: 2rem; font-weight: 700; font-family: monospace; }\n"

        if norm_path in ("backend/app/main.py", "app/main.py"):
            return "from fastapi import FastAPI\napp = FastAPI(title='Platformer Game')\n@app.get('/health')\ndef health(): return {'status':'healthy'}\n"

        if norm_path in ("backend/app/config.py", "app/config.py"):
            return "from pydantic import BaseModel\nclass Settings(BaseModel): app_name: str = 'Platformer'\nsettings = Settings()\n"

        if norm_path in ("backend/app/models.py", "app/models.py"):
            return "from pydantic import BaseModel\nclass ScoreModel(BaseModel): score: int\n"

        if norm_path in ("backend/app/api.py", "app/api.py"):
            return "from fastapi import APIRouter\nrouter = APIRouter(prefix='/platformer')\n@router.post('/scores')\ndef add_score(): return {'status':'ok'}\n"

        if norm_path in ("backend/app/persistence.py", "app/persistence.py"):
            return "class Repo: pass\nrepository = Repo()\n"

        if norm_path == "README.md":
            return f"# {project_name}\n\n{project_desc}\n"

    # -------------------------------------------------------------
    # Archetype: TOP-DOWN RACING (racing)
    # -------------------------------------------------------------
    if archetype == "racing":
        if norm_path == "frontend/index.html":
            from app.runtime.preview_server import get_racing_game_html
            return get_racing_game_html(title=project_name, desc=project_desc)

        if norm_path == "frontend/src/main.tsx":
            return "import React from 'react'; import ReactDOM from 'react-dom/client'; import App from './App'; import './styles/App.css'; ReactDOM.createRoot(document.getElementById('root')!).render(<App />);\n"

        if norm_path == "frontend/src/App.tsx":
            return f"import React from 'react'; export default function App() {{ return <div style={{{{padding:'2rem',textAlign:'center'}}}}><h1>{project_name}</h1><p>{project_desc}</p></div>; }}\n"

        if norm_path == "frontend/src/components/RaceCanvas.tsx":
            return "import React from 'react'; export default function RaceCanvas() { return <canvas width={750} height={400} />; }\n"

        if norm_path == "frontend/src/components/TelemetryBar.tsx":
            return "import React from 'react'; export default function TelemetryBar() { return <div>Telemetry Active</div>; }\n"

        if norm_path == "frontend/src/services/api.ts":
            return "export const racingApi = {};\n"

        if norm_path == "frontend/src/styles/App.css":
            return "body { margin:0; background: #1c1917; color:#fff; }\n"

        if norm_path in ("backend/app/main.py", "app/main.py"):
            return "from fastapi import FastAPI\napp = FastAPI()\n@app.get('/health')\ndef h(): return {'status':'ok'}\n"

        if norm_path in ("backend/app/config.py", "app/config.py"):
            return "class Settings: pass\nsettings = Settings()\n"

        if norm_path in ("backend/app/models.py", "app/models.py"):
            return "class RaceRecord: pass\n"

        if norm_path in ("backend/app/api.py", "app/api.py"):
            return "from fastapi import APIRouter\nrouter = APIRouter()\n"

        if norm_path in ("backend/app/persistence.py", "app/persistence.py"):
            return "repository = {}\n"

        if norm_path == "README.md":
            return f"# {project_name}\n"

    # -------------------------------------------------------------
    # Archetype: SLIDING PUZZLE (puzzle)
    # -------------------------------------------------------------
    if archetype == "puzzle":
        if norm_path == "frontend/index.html":
            from app.runtime.preview_server import get_puzzle_game_html
            return get_puzzle_game_html(title=project_name, desc=project_desc)

        if norm_path == "frontend/src/main.tsx":
            return "import React from 'react'; import ReactDOM from 'react-dom/client'; import App from './App'; import './styles/App.css'; ReactDOM.createRoot(document.getElementById('root')!).render(<App />);\n"

        if norm_path == "frontend/src/App.tsx":
            return f"import React from 'react'; export default function App() {{ return <div style={{{{padding:'2rem',textAlign:'center'}}}}><h1>{project_name}</h1><p>{project_desc}</p></div>; }}\n"

        if norm_path == "frontend/src/components/PuzzleBoard.tsx":
            return "import React from 'react'; export default function PuzzleBoard() { return <div>Puzzle Grid</div>; }\n"

        if norm_path == "frontend/src/components/PuzzleStats.tsx":
            return "import React from 'react'; export default function PuzzleStats() { return <div>Stats</div>; }\n"

        if norm_path == "frontend/src/services/api.ts":
            return "export const puzzleApi = {};\n"

        if norm_path == "frontend/src/styles/App.css":
            return "body { margin:0; background: #064e3b; color:#fff; }\n"

        if norm_path in ("backend/app/main.py", "app/main.py"):
            return "from fastapi import FastAPI\napp = FastAPI()\n@app.get('/health')\ndef h(): return {'status':'ok'}\n"

        if norm_path in ("backend/app/config.py", "app/config.py"):
            return "class Settings: pass\nsettings = Settings()\n"

        if norm_path in ("backend/app/models.py", "app/models.py"):
            return "class PuzzleRecord: pass\n"

        if norm_path in ("backend/app/api.py", "app/api.py"):
            return "from fastapi import APIRouter\nrouter = APIRouter()\n"

        if norm_path in ("backend/app/persistence.py", "app/persistence.py"):
            return "repository = {}\n"

        if norm_path == "README.md":
            return f"# {project_name}\n"

    # -------------------------------------------------------------
    # Archetype: STUDY & QUIZ (educational)
    # -------------------------------------------------------------
    if archetype == "educational":
        if norm_path == "frontend/index.html":
            from app.runtime.preview_server import get_educational_app_html
            return get_educational_app_html(title=project_name, desc=project_desc)

        if norm_path == "frontend/src/main.tsx":
            return "import React from 'react'; import ReactDOM from 'react-dom/client'; import App from './App'; import './styles/App.css'; ReactDOM.createRoot(document.getElementById('root')!).render(<App />);\n"

        if norm_path == "frontend/src/App.tsx":
            return f"import React from 'react'; export default function App() {{ return <div style={{{{padding:'2rem',textAlign:'center'}}}}><h1>{project_name}</h1><p>{project_desc}</p></div>; }}\n"

        if norm_path == "frontend/src/components/FlashcardDeck.tsx":
            return "import React from 'react'; export default function FlashcardDeck() { return <div>Flashcard Deck</div>; }\n"

        if norm_path == "frontend/src/components/QuizRunner.tsx":
            return "import React from 'react'; export default function QuizRunner() { return <div>Quiz Runner</div>; }\n"

        if norm_path == "frontend/src/services/api.ts":
            return "export const eduApi = {};\n"

        if norm_path == "frontend/src/styles/App.css":
            return "body { margin:0; background: #1e1b4b; color:#fff; }\n"

        if norm_path in ("backend/app/main.py", "app/main.py"):
            return "from fastapi import FastAPI\napp = FastAPI()\n@app.get('/health')\ndef h(): return {'status':'ok'}\n"

        if norm_path in ("backend/app/config.py", "app/config.py"):
            return "class Settings: pass\nsettings = Settings()\n"

        if norm_path in ("backend/app/models.py", "app/models.py"):
            return "class DeckModel: pass\n"

        if norm_path in ("backend/app/api.py", "app/api.py"):
            return "from fastapi import APIRouter\nrouter = APIRouter()\n"

        if norm_path in ("backend/app/persistence.py", "app/persistence.py"):
            return "repository = {}\n"

        if norm_path == "README.md":
            return f"# {project_name}\n"

    # -------------------------------------------------------------
    # Archetype: DYNAMIC CUSTOM APPLICATION (custom)
    # -------------------------------------------------------------
    if archetype == "custom":
        if norm_path == "frontend/index.html":
            from app.runtime.preview_server import get_custom_interactive_html
            return get_custom_interactive_html(title=project_name, desc=project_desc)

        if norm_path == "frontend/src/main.tsx":
            return "import React from 'react'; import ReactDOM from 'react-dom/client'; import App from './App'; import './styles/App.css'; ReactDOM.createRoot(document.getElementById('root')!).render(<App />);\n"

        if norm_path == "frontend/src/App.tsx":
            return (
                "import React, { useState } from 'react';\n"
                "import DataExplorer from './components/DataExplorer';\n"
                "import SummaryCards from './components/SummaryCards';\n"
                "import { customApi } from './services/api';\n\n"
                "export default function App() {\n"
                "  const [items, setItems] = useState([\n"
                "    { id: '1', title: 'System Initialization Node', status: 'Active', priority: 'High' },\n"
                "    { id: '2', title: 'Data Processing Unit', status: 'Pending', priority: 'Medium' }\n"
                "  ]);\n"
                "  return (\n"
                "    <div className=\"custom-app-container\">\n"
                f'      <header><h1>{project_name}</h1><p>{project_desc}</p></header>\n'
                "      <SummaryCards count={items.length} />\n"
                "      <DataExplorer items={items} onToggle={(id) => {\n"
                "        setItems(prev => prev.map(it => it.id === id ? { ...it, status: it.status === 'Active' ? 'Pending' : 'Active' } : it));\n"
                "      }} />\n"
                "    </div>\n"
                "  );\n"
                "}\n"
            )

        if norm_path == "frontend/src/components/DataExplorer.tsx":
            return (
                "import React from 'react';\n"
                "export default function DataExplorer({ items, onToggle }: any) {\n"
                "  return (\n"
                "    <div className=\"explorer-panel\">\n"
                "      <table>\n"
                "        <thead><tr><th>ID</th><th>Title</th><th>Status</th><th>Priority</th><th>Action</th></tr></thead>\n"
                "        <tbody>\n"
                "          {items.map((it: any) => (\n"
                "            <tr key={it.id}>\n"
                "              <td>{it.id}</td><td>{it.title}</td><td>{it.status}</td><td>{it.priority}</td>\n"
                "              <td><button onClick={() => onToggle(it.id)}>Toggle</button></td>\n"
                "            </tr>\n"
                "          ))}\n"
                "        </tbody>\n"
                "      </table>\n"
                "    </div>\n"
                "  );\n"
                "}\n"
            )

        if norm_path == "frontend/src/components/SummaryCards.tsx":
            return "import React from 'react'; export default function SummaryCards({ count }: { count: number }) { return <div className=\"kpi-row\"><div>Total Records: {count}</div></div>; }\n"

        if norm_path == "frontend/src/components/ItemModal.tsx":
            return "import React from 'react'; export default function ItemModal() { return <div>Modal Dialog</div>; }\n"

        if norm_path == "frontend/src/services/api.ts":
            return "export const customApi = { async getItems() { return fetch('/api/items'); } };\n"

        if norm_path == "frontend/src/styles/App.css":
            return "body { margin:0; background: #0b0f19; color: #f8fafc; font-family: sans-serif; padding: 2rem; } table { width:100%; border-collapse:collapse; } th, td { padding: 0.75rem; border-bottom: 1px solid rgba(255,255,255,0.1); }\n"

        if norm_path in ("backend/app/main.py", "app/main.py"):
            return (
                "from fastapi import FastAPI\n"
                "from fastapi.middleware.cors import CORSMiddleware\n"
                "from app.config import settings\n"
                "from app.api import router as items_router\n\n"
                "app = FastAPI(title=settings.app_name)\n"
                "app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])\n"
                "app.include_router(items_router, prefix='/api')\n"
                "@app.get('/health')\ndef health(): return {'status':'healthy', 'app': settings.app_name}\n"
            )

        if norm_path in ("backend/app/config.py", "app/config.py"):
            return f"from pydantic import BaseModel\nclass Settings(BaseModel): app_name: str = '{project_name}'\nsettings = Settings()\n"

        if norm_path in ("backend/app/models.py", "app/models.py"):
            return "from pydantic import BaseModel\nclass CustomItem(BaseModel): id: str; title: str; status: str = 'Active'\n"

        if norm_path in ("backend/app/api.py", "app/api.py"):
            return (
                "from fastapi import APIRouter\n"
                "from app.models import CustomItem\n"
                "from app.persistence import repository\n"
                "router = APIRouter(prefix='/items', tags=['items'])\n"
                "@router.get('')\ndef list_items(): return repository.list()\n"
            )

        if norm_path in ("backend/app/persistence.py", "app/persistence.py"):
            return "class ItemRepo: def list(self): return [{'id':'1','title':'Item 1'}]\nrepository = ItemRepo()\n"

        if norm_path == "README.md":
            return f"# {project_name}\n\n{project_desc}\n"

    # Archetype -1: SHADOW MASTER SKILL BUILDER (shadow_combat_game)
    # -------------------------------------------------------------
    if archetype == "shadow_master":
        if norm_path == "frontend/index.html":
            from app.runtime.preview_server import get_shadow_master_game_html
            return get_shadow_master_game_html(title=project_name, desc=project_desc)

        if norm_path == "frontend/src/main.tsx":
            return (
                "import React from 'react';\n"
                "import ReactDOM from 'react-dom/client';\n"
                "import App from './App';\n"
                "import './styles/App.css';\n\n"
                "ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(\n"
                "  <React.StrictMode>\n"
                "    <App />\n"
                "  </React.StrictMode>\n"
                ");\n"
            )

        if norm_path == "frontend/src/App.tsx":
            return (
                "import React, { useState } from 'react';\n"
                "import CombatArena from './components/CombatArena';\n"
                "import SkillDesigner from './components/SkillDesigner';\n"
                "import StatsPanel from './components/StatsPanel';\n"
                "import { shadowApi, SkillConfig } from './services/api';\n\n"
                "const DEFAULT_SKILLS: SkillConfig[] = [\n"
                "  { id: 'slash', name: 'Katana Slash', key: 'Q', damage: 45, energyCost: 15, cooldown: 0.6, radius: 65, color: '#c084fc', element: 'VOID', desc: 'Rapid crescent slash that strikes nearby foes in an arc.' },\n"
                "  { id: 'dash', name: 'Shadow Dash', key: 'W', damage: 25, energyCost: 25, cooldown: 1.5, radius: 120, color: '#06b6d4', element: 'SHADOW', desc: 'Phases through enemies dealing damage and granting brief invulnerability.' },\n"
                "  { id: 'shuriken', name: 'Shuriken Volley', key: 'E', damage: 30, energyCost: 20, cooldown: 1.0, radius: 240, color: '#eab308', element: 'LIGHTNING', desc: 'Fires three piercing void shurikens in a spreading fan.' },\n"
                "  { id: 'cloak', name: 'Shadow Cloak', key: 'R', damage: 0, energyCost: 35, cooldown: 4.0, radius: 0, color: '#a855f7', element: 'VOID', desc: 'Enters stealth mode; next attack deals 250% critical ambush damage.' },\n"
                "  { id: 'decoy', name: 'Shadow Decoy', key: 'Space', damage: 55, energyCost: 40, cooldown: 3.5, radius: 90, color: '#ec4899', element: 'FIRE', desc: 'Summons a mirror duplicate that taunts enemies then detonates.' }\n"
                "];\n\n"
                "export default function App() {\n"
                "  const [skills, setSkills] = useState<SkillConfig[]>(DEFAULT_SKILLS);\n"
                "  const [stats, setStats] = useState({ health: 100, energy: 100, score: 0, combo: 1, level: 1, xp: 0 });\n\n"
                "  const handleUpdateSkill = (updated: SkillConfig) => {\n"
                "    setSkills(prev => prev.map(s => s.id === updated.id ? updated : s));\n"
                "    shadowApi.saveSkill(updated);\n"
                "  };\n\n"
                "  return (\n"
                "    <div className=\"shadow-master-root\">\n"
                f"      <header className=\"shadow-header\"><h1>{project_name}</h1><p>{project_desc}</p></header>\n"
                "      <StatsPanel stats={stats} />\n"
                "      <div className=\"shadow-workspace-grid\">\n"
                "        <CombatArena skills={skills} onStatsChange={setStats} />\n"
                "        <SkillDesigner skills={skills} onUpdateSkill={handleUpdateSkill} />\n"
                "      </div>\n"
                "    </div>\n"
                "  );\n"
                "}\n"
            )

        if norm_path == "frontend/src/components/StatsPanel.tsx":
            return (
                "import React from 'react';\n\n"
                "interface Stats { health: number; energy: number; score: number; combo: number; level: number; xp: number; }\n\n"
                "export default function StatsPanel({ stats }: { stats: Stats }) {\n"
                "  return (\n"
                "    <div className=\"stats-hud-bar\">\n"
                "      <div className=\"hud-stat\"><label>HP</label><div className=\"bar-bg\"><div className=\"bar-fill hp\" style={{ width: `${stats.health}%` }}></div></div><span>{Math.round(stats.health)}/100</span></div>\n"
                "      <div className=\"hud-stat\"><label>ENERGY</label><div className=\"bar-bg\"><div className=\"bar-fill nrg\" style={{ width: `${stats.energy}%` }}></div></div><span>{Math.round(stats.energy)}/100</span></div>\n"
                "      <div className=\"hud-pill\">LVL <strong>{stats.level}</strong> (XP: {stats.xp}/100)</div>\n"
                "      <div className=\"hud-pill combo\">COMBO <strong>{stats.combo.toFixed(1)}x</strong></div>\n"
                "      <div className=\"hud-pill score\">SCORE <strong>{stats.score}</strong></div>\n"
                "    </div>\n"
                "  );\n"
                "}\n"
            )

        if norm_path == "frontend/src/components/CombatArena.tsx":
            return (
                "import React, { useRef, useEffect } from 'react';\n"
                "import { SkillConfig } from '../services/api';\n\n"
                "interface Props { skills: SkillConfig[]; onStatsChange: (s: any) => void; }\n\n"
                "export default function CombatArena({ skills, onStatsChange }: Props) {\n"
                "  const canvasRef = useRef<HTMLCanvasElement | null>(null);\n"
                "  useEffect(() => {\n"
                "    const canvas = canvasRef.current;\n"
                "    if (!canvas) return;\n"
                "    const ctx = canvas.getContext('2d');\n"
                "    if (!ctx) return;\n"
                "    let animId: number;\n"
                "    let pX = 350, pY = 210, hp = 100, energy = 100, score = 0, combo = 1, lvl = 1, xp = 0;\n"
                "    const loop = () => {\n"
                "      ctx.fillStyle = '#07090e';\n"
                "      ctx.fillRect(0, 0, canvas.width, canvas.height);\n"
                "      // Draw grid\n"
                "      ctx.strokeStyle = 'rgba(168, 85, 247, 0.1)';\n"
                "      for (let x = 0; x < canvas.width; x += 35) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvas.height); ctx.stroke(); }\n"
                "      for (let y = 0; y < canvas.height; y += 35) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(canvas.width, y); ctx.stroke(); }\n"
                "      // Player\n"
                "      ctx.shadowBlur = 15; ctx.shadowColor = '#a855f7';\n"
                "      ctx.fillStyle = '#c084fc';\n"
                "      ctx.beginPath(); ctx.arc(pX, pY, 18, 0, Math.PI * 2); ctx.fill();\n"
                "      ctx.shadowBlur = 0;\n"
                "      animId = requestAnimationFrame(loop);\n"
                "    };\n"
                "    animId = requestAnimationFrame(loop);\n"
                "    return () => cancelAnimationFrame(animId);\n"
                "  }, [skills]);\n\n"
                "  return (\n"
                "    <div className=\"combat-arena-container\">\n"
                "      <canvas ref={canvasRef} width={700} height={420} className=\"arena-canvas\" />\n"
                "      <div className=\"ability-bar\">\n"
                "        {skills.map(s => (\n"
                "          <div key={s.id} className=\"skill-slot\" style={{ borderColor: s.color }}>\n"
                "            <span className=\"key-badge\">{s.key}</span>\n"
                "            <div className=\"skill-name\">{s.name}</div>\n"
                "            <div className=\"skill-meta\">{s.energyCost} NRG</div>\n"
                "          </div>\n"
                "        ))}\n"
                "      </div>\n"
                "    </div>\n"
                "  );\n"
                "}\n"
            )

        if norm_path == "frontend/src/components/SkillDesigner.tsx":
            return (
                "import React, { useState } from 'react';\n"
                "import { SkillConfig } from '../services/api';\n\n"
                "interface Props { skills: SkillConfig[]; onUpdateSkill: (s: SkillConfig) => void; }\n\n"
                "export default function SkillDesigner({ skills, onUpdateSkill }: Props) {\n"
                "  const [selectedId, setSelectedId] = useState<string>(skills[0]?.id || 'slash');\n"
                "  const active = skills.find(s => s.id === selectedId) || skills[0];\n"
                "  const [exported, setExported] = useState<string>('');\n\n"
                "  const handleExport = () => {\n"
                "    setExported(JSON.stringify({ game: 'Shadow Master', skills }, null, 2));\n"
                "  };\n\n"
                "  return (\n"
                "    <div className=\"skill-designer-panel\">\n"
                "      <h3>Skill Customizer & Builder</h3>\n"
                "      <div className=\"skill-tabs\">\n"
                "        {skills.map(s => (\n"
                "          <button key={s.id} className={`tab-btn ${s.id === selectedId ? 'active' : ''}`} onClick={() => setSelectedId(s.id)}>{s.name}</button>\n"
                "        ))}\n"
                "      </div>\n"
                "      {active && (\n"
                "        <div className=\"editor-controls\">\n"
                "          <div className=\"control-row\">\n"
                "            <label>Damage: {active.damage}</label>\n"
                "            <input type=\"range\" min={10} max={150} value={active.damage} onChange={e => onUpdateSkill({ ...active, damage: Number(e.target.value) })} />\n"
                "          </div>\n"
                "          <div className=\"control-row\">\n"
                "            <label>Energy Cost: {active.energyCost}</label>\n"
                "            <input type=\"range\" min={5} max={80} value={active.energyCost} onChange={e => onUpdateSkill({ ...active, energyCost: Number(e.target.value) })} />\n"
                "          </div>\n"
                "          <div className=\"control-row\">\n"
                "            <label>Cooldown: {active.cooldown.toFixed(1)}s</label>\n"
                "            <input type=\"range\" min={2} max={60} value={Math.round(active.cooldown * 10)} onChange={e => onUpdateSkill({ ...active, cooldown: Number(e.target.value) / 10 })} />\n"
                "          </div>\n"
                "        </div>\n"
                "      )}\n"
                "      <button className=\"export-btn\" onClick={handleExport}>Export Skill Tree JSON</button>\n"
                "      {exported && <pre className=\"json-view\">{exported}</pre>}\n"
                "    </div>\n"
                "  );\n"
                "}\n"
            )

        if norm_path == "frontend/src/services/api.ts":
            return (
                "export interface SkillConfig {\n"
                "  id: string;\n"
                "  name: string;\n"
                "  key: string;\n"
                "  damage: number;\n"
                "  energyCost: number;\n"
                "  cooldown: number;\n"
                "  radius: number;\n"
                "  color: string;\n"
                "  element: string;\n"
                "  desc: string;\n"
                "}\n\n"
                "export const shadowApi = {\n"
                "  async getSkills(): Promise<SkillConfig[]> {\n"
                "    try {\n"
                "      const res = await fetch('/api/skills');\n"
                "      return res.ok ? await res.json() : [];\n"
                "    } catch { return []; }\n"
                "  },\n"
                "  async saveSkill(skill: SkillConfig): Promise<boolean> {\n"
                "    try {\n"
                "      const res = await fetch('/api/skills', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(skill) });\n"
                "      return res.ok;\n"
                "    } catch { return false; }\n"
                "  },\n"
                "  async recordScore(score: number): Promise<boolean> {\n"
                "    try {\n"
                "      const res = await fetch('/api/scores', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ score }) });\n"
                "      return res.ok;\n"
                "    } catch { return false; }\n"
                "  }\n"
                "};\n"
            )

        if norm_path == "frontend/src/styles/App.css":
            return (
                ":root { --bg: #07090e; --purple: #a855f7; --purple-light: #c084fc; --text: #f8fafc; }\n"
                "body { margin: 0; background: var(--bg); color: var(--text); font-family: 'Plus Jakarta Sans', sans-serif; }\n"
                ".shadow-master-root { padding: 1.5rem; max-width: 1200px; margin: 0 auto; }\n"
                ".shadow-header h1 { font-size: 2rem; color: var(--purple-light); margin: 0 0 0.5rem; }\n"
                ".stats-hud-bar { display: flex; gap: 1rem; align-items: center; background: rgba(15, 23, 42, 0.8); padding: 0.75rem 1.25rem; border-radius: 12px; margin-bottom: 1rem; border: 1px solid rgba(168, 85, 247, 0.2); }\n"
                ".bar-bg { width: 120px; height: 10px; background: #1e293b; border-radius: 9999px; overflow: hidden; display: inline-block; margin: 0 0.5rem; }\n"
                ".bar-fill.hp { height: 100%; background: #ef4444; }\n"
                ".bar-fill.nrg { height: 100%; background: #06b6d4; }\n"
                ".hud-pill { background: rgba(168, 85, 247, 0.15); padding: 0.3rem 0.8rem; border-radius: 8px; border: 1px solid rgba(168, 85, 247, 0.3); font-weight: 700; }\n"
                ".shadow-workspace-grid { display: grid; grid-template-columns: 700px 1fr; gap: 1.5rem; }\n"
                ".arena-canvas { border: 2px solid rgba(168, 85, 247, 0.3); border-radius: 12px; box-shadow: 0 0 25px rgba(168, 85, 247, 0.15); }\n"
                ".ability-bar { display: flex; gap: 0.75rem; margin-top: 0.75rem; }\n"
                ".skill-slot { background: rgba(15, 23, 42, 0.9); border: 2px solid; border-radius: 8px; padding: 0.5rem; width: 110px; text-align: center; }\n"
                ".key-badge { background: #3b82f6; color: white; padding: 0.1rem 0.4rem; border-radius: 4px; font-weight: 800; font-size: 0.75rem; }\n"
                ".skill-designer-panel { background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(168, 85, 247, 0.25); border-radius: 12px; padding: 1.25rem; }\n"
                ".skill-tabs { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-bottom: 1rem; }\n"
                ".tab-btn { background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); color: #cbd5e1; padding: 0.4rem 0.8rem; border-radius: 6px; cursor: pointer; }\n"
                ".tab-btn.active { background: var(--purple); color: #07090e; font-weight: 700; }\n"
                ".control-row { margin-bottom: 0.75rem; }\n"
                ".control-row label { display: block; font-size: 0.85rem; margin-bottom: 0.25rem; }\n"
                ".control-row input { width: 100%; }\n"
                ".export-btn { width: 100%; margin-top: 1rem; padding: 0.6rem; background: linear-gradient(135deg, #a855f7, #6b21a8); color: white; border: none; border-radius: 8px; font-weight: 700; cursor: pointer; }\n"
                ".json-view { margin-top: 0.75rem; background: #07090e; padding: 0.75rem; border-radius: 8px; font-size: 0.75rem; max-height: 180px; overflow-y: auto; color: #a5f3fc; }\n"
            )

        if norm_path in ("backend/app/main.py", "app/main.py"):
            return (
                "from fastapi import FastAPI\n"
                "from fastapi.middleware.cors import CORSMiddleware\n"
                "from fastapi.staticfiles import StaticFiles\n"
                "from fastapi.responses import FileResponse, HTMLResponse\n"
                "import os\n\n"
                "from app.config import settings\n"
                "from app.api import router as shadow_router\n\n"
                "app = FastAPI(\n"
                f'    title="{project_name}",\n'
                f'    description="{project_desc}",\n'
                "    version=\"2.0.0\",\n"
                ")\n\n"
                "app.add_middleware(\n"
                "    CORSMiddleware,\n"
                "    allow_origins=[\"*\"],\n"
                "    allow_credentials=True,\n"
                "    allow_methods=[\"*\"],\n"
                "    allow_headers=[\"*\"],\n"
                ")\n\n"
                "app.include_router(shadow_router, prefix=\"/api\")\n"
                "app.include_router(shadow_router)\n\n"
                "@app.get(\"/health\")\n"
                "def health_check():\n"
                "    return {\"status\": \"healthy\", \"app\": settings.app_name}\n\n"
                "for s_dir in ['frontend', '../frontend', 'static']:\n"
                "    if os.path.exists(s_dir):\n"
                "        try:\n"
                "            app.mount('/static', StaticFiles(directory=s_dir), name='static')\n"
                "            break\n"
                "        except Exception:\n"
                "            pass\n\n"
                "@app.get(\"/\")\n"
                "def serve_root():\n"
                "    for p in ['frontend/index.html', '../frontend/index.html', 'index.html']:\n"
                "        if os.path.exists(p):\n"
                "            return FileResponse(p)\n"
                f'    return HTMLResponse(\"<h1>{project_name} Ready</h1>\")\n'
            )

        if norm_path in ("backend/app/config.py", "app/config.py"):
            return (
                "from pydantic import BaseModel\n\n"
                "class Settings(BaseModel):\n"
                f'    app_name: str = "{project_name}"\n'
                "    debug: bool = True\n\n"
                "settings = Settings()\n"
            )

        if norm_path in ("backend/app/models.py", "app/models.py"):
            return (
                "from pydantic import BaseModel, Field\n"
                "from typing import Optional, List\n"
                "import uuid\n"
                "from datetime import datetime, timezone\n\n"
                "class SkillModel(BaseModel):\n"
                "    id: str = Field(..., max_length=50)\n"
                "    name: str = Field(..., max_length=100)\n"
                "    key: str = Field(..., max_length=10)\n"
                "    damage: int = Field(50, ge=0, le=500)\n"
                "    energy_cost: int = Field(20, ge=0, le=100)\n"
                "    cooldown: float = Field(1.0, ge=0.1, le=60.0)\n"
                "    radius: int = Field(60, ge=10, le=500)\n"
                "    color: str = Field(\"#a855f7\", max_length=30)\n"
                "    element: str = Field(\"VOID\", max_length=30)\n"
                "    desc: Optional[str] = \"\"\n\n"
                "class CombatScoreRecord(BaseModel):\n"
                "    id: str = Field(default_factory=lambda: str(uuid.uuid4()))\n"
                "    player_name: str = Field(\"Shadow Master\", max_length=100)\n"
                "    score: int = Field(0, ge=0)\n"
                "    combo_max: float = Field(1.0, ge=1.0)\n"
                "    level_reached: int = Field(1, ge=1)\n"
                "    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())\n"
            )

        if norm_path in ("backend/app/api.py", "app/api.py"):
            return (
                "from fastapi import APIRouter, HTTPException\n"
                "from app.models import SkillModel, CombatScoreRecord\n"
                "from app.persistence import repository\n\n"
                "router = APIRouter(tags=[\"shadow_master\"])\n\n"
                "@router.get(\"/skills\", response_model=list[SkillModel])\n"
                "def list_skills():\n"
                "    return repository.list_skills()\n\n"
                "@router.post(\"/skills\", response_model=SkillModel)\n"
                "def save_skill(skill: SkillModel):\n"
                "    return repository.save_skill(skill)\n\n"
                "@router.get(\"/scores\", response_model=list[CombatScoreRecord])\n"
                "def list_scores():\n"
                "    return repository.list_scores()\n\n"
                "@router.post(\"/scores\", response_model=CombatScoreRecord)\n"
                "def record_score(record: CombatScoreRecord):\n"
                "    return repository.add_score(record)\n"
            )

        if norm_path in ("backend/app/persistence.py", "app/persistence.py"):
            return (
                "import threading\n"
                "from app.models import SkillModel, CombatScoreRecord\n\n"
                "class ShadowMasterRepository:\n"
                "    def __init__(self):\n"
                "        self._lock = threading.Lock()\n"
                "        self._skills = {\n"
                "            'slash': SkillModel(id='slash', name='Katana Slash', key='Q', damage=45, energy_cost=15, cooldown=0.6, radius=65, color='#c084fc', element='VOID', desc='Rapid crescent slash'),\n"
                "            'dash': SkillModel(id='dash', name='Shadow Dash', key='W', damage=25, energy_cost=25, cooldown=1.5, radius=120, color='#06b6d4', element='SHADOW', desc='Phases through enemies'),\n"
                "            'shuriken': SkillModel(id='shuriken', name='Shuriken Volley', key='E', damage=30, energy_cost=20, cooldown=1.0, radius=240, color='#eab308', element='LIGHTNING', desc='Piercing shurikens'),\n"
                "            'cloak': SkillModel(id='cloak', name='Shadow Cloak', key='R', damage=0, energy_cost=35, cooldown=4.0, radius=0, color='#a855f7', element='VOID', desc='Stealth crit stance'),\n"
                "            'decoy': SkillModel(id='decoy', name='Shadow Decoy', key='Space', damage=55, energy_cost=40, cooldown=3.5, radius=90, color='#ec4899', element='FIRE', desc='Taunt mirror duplicate'),\n"
                "        }\n"
                "        self._scores = []\n\n"
                "    def list_skills(self):\n"
                "        with self._lock:\n"
                "            return list(self._skills.values())\n\n"
                "    def save_skill(self, skill: SkillModel):\n"
                "        with self._lock:\n"
                "            self._skills[skill.id] = skill\n"
                "            return skill\n\n"
                "    def list_scores(self):\n"
                "        with self._lock:\n"
                "            return list(self._scores)\n\n"
                "    def add_score(self, record: CombatScoreRecord):\n"
                "        with self._lock:\n"
                "            self._scores.insert(0, record)\n"
                "            return record\n\n"
                "repository = ShadowMasterRepository()\n"
            )

        if norm_path == "README.md":
            return (
                f"# {project_name}\n\n"
                f"{project_desc}\n\n"
                "## Shadow Master Combat Arena & Skill Builder\n\n"
                "A web-based tool that lets game designers create, preview, and export custom skills for the Shadow Master game.\n\n"
                "### Combat Controls\n"
                "- **Move**: W/A/S/D or Arrow Keys\n"
                "- **Aim**: Mouse pointer\n"
                "- **Katana Slash**: Q key (or Primary Button)\n"
                "- **Shadow Dash**: W key\n"
                "- **Shuriken Volley**: E key\n"
                "- **Shadow Cloak**: R key\n"
                "- **Shadow Decoy**: Spacebar\n\n"
                "### Skill Customizer\n"
                "- Real-time damage, energy cost, and cooldown parameter tuning.\n"
                "- Export validated JSON configurations for game engine consumption.\n"
            )

    # Archetype 0: CARROM MASTER (interactive_board_game)
    # -------------------------------------------------------------
    if archetype == "carrom":
        if norm_path == "frontend/index.html":
            from app.runtime.preview_server import get_carrom_game_html
            return get_carrom_game_html(title=project_name, desc=project_desc)

        if norm_path == "frontend/src/App.tsx":
            return (
                "import React, { useState, useEffect, useRef, useCallback } from 'react';\n"
                "import { ScoreBoard } from './components/ScoreBoard';\n"
                "import { GameControls } from './components/GameControls';\n"
                "import { scoreApi } from './services/api';\n\n"
                "interface Piece {\n"
                "  id: string;\n"
                "  type: 'queen' | 'white' | 'black';\n"
                "  x: number;\n"
                "  y: number;\n"
                "  vx: number;\n"
                "  vy: number;\n"
                "  r: number;\n"
                "  mass: number;\n"
                "  active: boolean;\n"
                "}\n\n"
                "const BOARD_SIZE = 600;\n"
                "const POCKET_RADIUS = 28;\n"
                "const CUSHION = 38;\n"
                "const FRICTION = 0.986;\n"
                "const RESTITUTION = 0.88;\n"
                "const BASELINE_Y = 482;\n\n"
                "export default function App() {\n"
                "  const [p1Score, setP1Score] = useState<number>(0);\n"
                "  const [p2Score, setP2Score] = useState<number>(0);\n"
                "  const [currentTurn, setCurrentTurn] = useState<number>(1);\n"
                "  const [soloMode, setSoloMode] = useState<boolean>(false);\n"
                "  const [queenPocketed, setQueenPocketed] = useState<boolean>(false);\n"
                "  const [strikerPos, setStrikerPos] = useState<number>(300);\n"
                "  const [statusMsg, setStatusMsg] = useState<string>('Drag striker back to aim and shoot!');\n"
                "  const [coinsLeft, setCoinsLeft] = useState<number>(18);\n"
                "  const canvasRef = useRef<HTMLCanvasElement | null>(null);\n\n"
                "  const piecesRef = useRef<Piece[]>([]);\n"
                "  const strikerRef = useRef<any>({\n"
                "    x: 300, y: BASELINE_Y, vx: 0, vy: 0, r: 21, mass: 3.2, active: true, inPocket: false\n"
                "  });\n\n"
                "  const initBoard = useCallback(() => {\n"
                "    const list: Piece[] = [];\n"
                "    const CX = 300, CY = 300, R = 14;\n"
                "    list.push({ id: 'queen', type: 'queen', x: CX, y: CY, vx: 0, vy: 0, r: R, mass: 1.0, active: true });\n"
                "    const r1 = R * 2 + 1;\n"
                "    for (let i = 0; i < 6; i++) {\n"
                "      const a = (i * Math.PI) / 3;\n"
                "      list.push({\n"
                "        id: `inner_${i}`,\n"
                "        type: i % 2 === 0 ? 'white' : 'black',\n"
                "        x: CX + r1 * Math.cos(a),\n"
                "        y: CY + r1 * Math.sin(a),\n"
                "        vx: 0, vy: 0, r: R, mass: 1.0, active: true\n"
                "      });\n"
                "    }\n"
                "    const r2 = R * 4 + 2;\n"
                "    for (let i = 0; i < 12; i++) {\n"
                "      const a = (i * Math.PI) / 6 + Math.PI / 12;\n"
                "      list.push({\n"
                "        id: `outer_${i}`,\n"
                "        type: i % 2 === 0 ? 'white' : 'black',\n"
                "        x: CX + r2 * Math.cos(a),\n"
                "        y: CY + r2 * Math.sin(a),\n"
                "        vx: 0, vy: 0, r: R, mass: 1.0, active: true\n"
                "      });\n"
                "    }\n"
                "    piecesRef.current = list;\n"
                "    strikerRef.current = { x: 300, y: BASELINE_Y, vx: 0, vy: 0, r: 21, mass: 3.2, active: true, inPocket: false };\n"
                "    setStrikerPos(300);\n"
                "    setCoinsLeft(18);\n"
                "    setQueenPocketed(false);\n"
                "  }, []);\n\n"
                "  useEffect(() => {\n"
                "    initBoard();\n"
                "  }, [initBoard]);\n\n"
                "  const handleReset = () => {\n"
                "    setP1Score(0);\n"
                "    setP2Score(0);\n"
                "    setCurrentTurn(1);\n"
                "    initBoard();\n"
                "    setStatusMsg('Board reset! Player 1 takes the break shot.');\n"
                "  };\n\n"
                "  const handleShoot = (vx: number, vy: number) => {\n"
                "    strikerRef.current.vx = vx;\n"
                "    strikerRef.current.vy = vy;\n"
                "    setStatusMsg('Shot in motion...');\n"
                "  };\n\n"
                "  return (\n"
                "    <div className=\"carrom-wrapper\">\n"
                f'      <h1 data-testid=\"app-title\">{project_name}</h1>\n'
                f'      <p className=\"subtitle\">{project_desc}</p>\n'
                "      <ScoreBoard\n"
                "        p1Score={p1Score}\n"
                "        p2Score={p2Score}\n"
                "        currentTurn={currentTurn}\n"
                "        queenPocketed={queenPocketed}\n"
                "        coinsLeft={coinsLeft}\n"
                "        soloMode={soloMode}\n"
                "      />\n"
                "      <div className=\"canvas-container\">\n"
                "        <canvas ref={canvasRef} width={600} height={600} />\n"
                "      </div>\n"
                "      <div className=\"status-banner\">{statusMsg}</div>\n"
                "      <GameControls\n"
                "        strikerPos={strikerPos}\n"
                "        onStrikerPosChange={(pos) => {\n"
                "          setStrikerPos(pos);\n"
                "          strikerRef.current.x = pos;\n"
                "        }}\n"
                "        onShoot={() => handleShoot((Math.random() - 0.5) * 4, -18)}\n"
                "        onReset={handleReset}\n"
                "        soloMode={soloMode}\n"
                "        onToggleSolo={() => setSoloMode(!soloMode)}\n"
                "      />\n"
                "    </div>\n"
                "  );\n"
                "}\n"
            )

        if norm_path == "frontend/src/components/ScoreBoard.tsx":
            return (
                "import React from 'react';\n\n"
                "interface ScoreBoardProps {\n"
                "  p1Score: number;\n"
                "  p2Score: number;\n"
                "  currentTurn: number;\n"
                "  queenPocketed: boolean;\n"
                "  coinsLeft: number;\n"
                "  soloMode: boolean;\n"
                "}\n\n"
                "export const ScoreBoard: React.FC<ScoreBoardProps> = ({\n"
                "  p1Score, p2Score, currentTurn, queenPocketed, coinsLeft, soloMode\n"
                "}) => (\n"
                "  <div className=\"scoreboard\">\n"
                "    <div className=\"score-pill\">P1 (White): <span>{p1Score}</span></div>\n"
                "    <div className=\"score-pill\">P2 (Black): <span>{p2Score}</span></div>\n"
                "    {!soloMode && (\n"
                "      <div className=\"turn-pill\">\n"
                "        {currentTurn === 1 ? 'Player 1 Turn (White)' : 'Player 2 Turn (Black)'}\n"
                "      </div>\n"
                "    )}\n"
                "    <div className={`queen-pill ${queenPocketed ? 'pocketed' : 'on-board'}`}>\n"
                "      Queen: {queenPocketed ? 'Pocketed' : 'On Board'}\n"
                "    </div>\n"
                "    <div className=\"score-pill\">Coins: <span>{coinsLeft}</span></div>\n"
                "  </div>\n"
                ");\n"
            )

        if norm_path == "frontend/src/components/GameControls.tsx":
            return (
                "import React from 'react';\n\n"
                "interface GameControlsProps {\n"
                "  strikerPos: number;\n"
                "  onStrikerPosChange: (pos: number) => void;\n"
                "  onShoot: () => void;\n"
                "  onReset: () => void;\n"
                "  soloMode: boolean;\n"
                "  onToggleSolo: () => void;\n"
                "}\n\n"
                "export const GameControls: React.FC<GameControlsProps> = ({\n"
                "  strikerPos, onStrikerPosChange, onShoot, onReset, soloMode, onToggleSolo\n"
                "}) => (\n"
                "  <div className=\"controls-panel\">\n"
                "    <div className=\"control-item\">\n"
                "      <label htmlFor=\"striker-slider\">Striker Pos:</label>\n"
                "      <input\n"
                "        id=\"striker-slider\"\n"
                "        type=\"range\"\n"
                "        min={175}\n"
                "        max={425}\n"
                "        value={strikerPos}\n"
                "        onChange={(e) => onStrikerPosChange(parseFloat(e.target.value))}\n"
                "      />\n"
                "    </div>\n"
                "    <button className=\"btn btn-primary\" onClick={onShoot}>Shoot Striker</button>\n"
                "    <button className=\"btn btn-secondary\" onClick={onReset}>Reset Board</button>\n"
                "    <button className=\"btn\" onClick={onToggleSolo}>\n"
                "      {soloMode ? 'Mode: Solo Practice' : 'Mode: 2 Players'}\n"
                "    </button>\n"
                "  </div>\n"
                ");\n"
            )

        if norm_path == "frontend/src/services/api.ts":
            return (
                "export interface CarromScore {\n"
                "  id?: string;\n"
                "  player_name: string;\n"
                "  score: number;\n"
                "  game?: string;\n"
                "  created_at?: string;\n"
                "}\n\n"
                "export const scoreApi = {\n"
                "  async getScores(): Promise<CarromScore[]> {\n"
                "    try {\n"
                "      const res = await fetch('/api/scores');\n"
                "      if (!res.ok) return [];\n"
                "      return await res.json();\n"
                "    } catch {\n"
                "      return [];\n"
                "    }\n"
                "  },\n"
                "  async submitScore(data: CarromScore): Promise<CarromScore | null> {\n"
                "    try {\n"
                "      const res = await fetch('/api/scores', {\n"
                "        method: 'POST',\n"
                "        headers: { 'Content-Type': 'application/json' },\n"
                "        body: JSON.stringify(data)\n"
                "      });\n"
                "      if (!res.ok) return null;\n"
                "      return await res.json();\n"
                "    } catch {\n"
                "      return null;\n"
                "    }\n"
                "  }\n"
                "};\n"
            )

        if norm_path == "frontend/src/styles/App.css":
            return (
                ":root {\n"
                "  --wood-border: #45210e;\n"
                "  --wood-surface: #e8c89b;\n"
                "  --accent-gold: #fbbf24;\n"
                "}\n\n"
                ".carrom-wrapper {\n"
                "  display: flex;\n"
                "  flex-direction: column;\n"
                "  align-items: center;\n"
                "  padding: 1.5rem;\n"
                "  font-family: 'Plus Jakarta Sans', sans-serif;\n"
                "  color: #f8fafc;\n"
                "  min-height: 100vh;\n"
                "}\n\n"
                ".scoreboard {\n"
                "  display: flex;\n"
                "  gap: 1.25rem;\n"
                "  background: rgba(255, 255, 255, 0.05);\n"
                "  border: 1px solid rgba(255, 255, 255, 0.1);\n"
                "  padding: 0.6rem 1.75rem;\n"
                "  border-radius: 9999px;\n"
                "  margin-bottom: 1rem;\n"
                "  font-family: 'JetBrains Mono', monospace;\n"
                "}\n\n"
                ".score-pill span { color: var(--accent-gold); font-weight: 700; }\n"
                ".turn-pill { color: #fbbf24; font-weight: 700; }\n"
                ".queen-pill.pocketed { color: #10b981; }\n"
                ".queen-pill.on-board { color: #ef4444; }\n\n"
                ".canvas-container {\n"
                "  padding: 12px;\n"
                "  border-radius: 20px;\n"
                "  background: linear-gradient(135deg, #45210e, #2b1407, #45210e);\n"
                "  box-shadow: 0 25px 50px rgba(0,0,0,0.8), 0 0 30px rgba(245,158,11,0.15);\n"
                "}\n\n"
                ".canvas-container canvas {\n"
                "  border-radius: 12px;\n"
                "  display: block;\n"
                "}\n\n"
                ".status-banner {\n"
                "  margin-top: 0.75rem;\n"
                "  background: rgba(15, 23, 42, 0.7);\n"
                "  padding: 0.4rem 1.25rem;\n"
                "  border-radius: 8px;\n"
                "  font-size: 0.85rem;\n"
                "  color: #cbd5e1;\n"
                "}\n\n"
                ".controls-panel {\n"
                "  margin-top: 0.85rem;\n"
                "  display: flex;\n"
                "  gap: 0.75rem;\n"
                "  align-items: center;\n"
                "  flex-wrap: wrap;\n"
                "}\n\n"
                ".btn {\n"
                "  padding: 0.45rem 1rem;\n"
                "  border-radius: 8px;\n"
                "  border: 1px solid rgba(255,255,255,0.15);\n"
                "  background: rgba(255,255,255,0.08);\n"
                "  color: #fff;\n"
                "  font-weight: 600;\n"
                "  cursor: pointer;\n"
                "}\n\n"
                ".btn-primary {\n"
                "  background: linear-gradient(135deg, #f59e0b, #d97706);\n"
                "  border: none;\n"
                "  color: #0f172a;\n"
                "}\n"
            )

        if norm_path in ("backend/app/main.py", "app/main.py"):
            return (
                "from fastapi import FastAPI\n"
                "from fastapi.middleware.cors import CORSMiddleware\n"
                "from fastapi.staticfiles import StaticFiles\n"
                "from fastapi.responses import FileResponse, HTMLResponse\n"
                "import os\n\n"
                "from app.config import settings\n"
                "from app.api import router as scores_router\n\n"
                "app = FastAPI(\n"
                f'    title="{project_name}",\n'
                f'    description="{project_desc}",\n'
                "    version=\"1.0.0\",\n"
                ")\n\n"
                "app.add_middleware(\n"
                "    CORSMiddleware,\n"
                "    allow_origins=[\"*\"],\n"
                "    allow_credentials=True,\n"
                "    allow_methods=[\"*\"],\n"
                "    allow_headers=[\"*\"],\n"
                ")\n\n"
                "app.include_router(scores_router, prefix=\"/api\")\n"
                "app.include_router(scores_router)\n\n"
                "@app.get(\"/health\")\n"
                "def health_check():\n"
                "    return {\"status\": \"healthy\", \"app\": settings.app_name}\n\n"
                "for s_dir in ['frontend', '../frontend', 'static']:\n"
                "    if os.path.exists(s_dir):\n"
                "        try:\n"
                "            app.mount('/static', StaticFiles(directory=s_dir), name='static')\n"
                "            break\n"
                "        except Exception:\n"
                "            pass\n\n"
                "@app.get(\"/\")\n"
                "def serve_root():\n"
                "    for p in ['frontend/index.html', '../frontend/index.html', 'index.html']:\n"
                "        if os.path.exists(p):\n"
                "            return FileResponse(p)\n"
                f'    return HTMLResponse(\"<h1>{project_name} Ready</h1>\")\n'
            )

        if norm_path in ("backend/app/config.py", "app/config.py"):
            return (
                "from pydantic import BaseModel\n\n"
                "class Settings(BaseModel):\n"
                f'    app_name: str = "{project_name}"\n'
                "    debug: bool = True\n\n"
                "settings = Settings()\n"
            )

        if norm_path in ("backend/app/models.py", "app/models.py"):
            return (
                "from pydantic import BaseModel, Field\n"
                "from typing import Optional\n"
                "import uuid\n"
                "from datetime import datetime, timezone\n\n"
                "class CarromScoreBase(BaseModel):\n"
                "    player_name: str = Field(..., max_length=100)\n"
                "    score: int = Field(0, ge=0)\n"
                "    game: Optional[str] = \"carrom\"\n\n"
                "class CarromScoreCreate(CarromScoreBase):\n"
                "    pass\n\n"
                "class CarromScore(CarromScoreBase):\n"
                "    id: str = Field(default_factory=lambda: str(uuid.uuid4()))\n"
                "    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())\n"
            )

        if norm_path in ("backend/app/api.py", "app/api.py"):
            return (
                "from fastapi import APIRouter, HTTPException, status\n"
                "from app.models import CarromScore, CarromScoreCreate\n"
                "from app.persistence import repository\n\n"
                "router = APIRouter(prefix=\"/scores\", tags=[\"scores\"])\n\n"
                "@router.get(\"\", response_model=list[CarromScore])\n"
                "def list_scores():\n"
                "    return repository.list_scores()\n\n"
                "@router.post(\"\", response_model=CarromScore, status_code=status.HTTP_201_CREATED)\n"
                "def submit_score(payload: CarromScoreCreate):\n"
                "    return repository.add_score(payload)\n"
            )

        if norm_path in ("backend/app/persistence.py", "app/persistence.py"):
            return (
                "import threading\n"
                "from app.models import CarromScore, CarromScoreCreate\n\n"
                "class CarromScoreRepository:\n"
                "    def __init__(self):\n"
                "        self._lock = threading.Lock()\n"
                "        self._scores: list[CarromScore] = []\n\n"
                "    def list_scores(self) -> list[CarromScore]:\n"
                "        with self._lock:\n"
                "            return sorted(self._scores, key=lambda s: s.score, reverse=True)\n\n"
                "    def add_score(self, payload: CarromScoreCreate) -> CarromScore:\n"
                "        with self._lock:\n"
                "            item = CarromScore(**payload.model_dump())\n"
                "            self._scores.append(item)\n"
                "            return item\n\n"
                "repository = CarromScoreRepository()\n"
            )

        if norm_path in ("README.md",):
            return (
                f"# {project_name}\n\n"
                f"{project_desc}\n\n"
                "## Features\n"
                "- Full 60 FPS HTML5 Canvas physics simulation with striker, coins, and queen.\n"
                "- Corner pocketing with foul detection for striker.\n"
                "- Realistic 2D momentum and collision dynamics.\n"
                "- Player 1 vs Player 2 turn-based match and Solo practice modes.\n"
                "- FastAPI backend for score tracking and leaderboards.\n\n"
                "## Gameplay Controls\n"
                "- **Aim & Shoot**: Click and drag on/near striker to aim and set power, release to fire.\n"
                "- **Positioning**: Use the Striker Pos slider to slide across the baseline.\n"
                "- **Reset Board**: Click Reset Board to re-rack all pieces.\n"
            )


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
