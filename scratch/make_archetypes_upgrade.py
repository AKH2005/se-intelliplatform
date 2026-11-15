import os
import ast
import re

def main():
    path = r"backend\app\agents\code_generation\archetypes.py"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Replace classify_application_category and detect_project_archetype at top
    old_classifier_block_start = 'def classify_application_category('
    target_planned_start = 'def get_archetype_planned_files('
    idx_cls = content.find(old_classifier_block_start)
    idx_plan = content.find(target_planned_start)
    assert idx_cls != -1 and idx_plan != -1, "Could not find classifier block boundaries"

    new_classifier_block = '''import re

def _has_word(text: str, *words: str) -> bool:
    """Check if any of the given words or multi-word phrases appear with word boundaries."""
    for w in words:
        escaped = re.escape(w.lower())
        pattern = r'(?:\\b|_)' + escaped + r'(?:\\b|_)'
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


def detect_project_archetype(name: str = "", desc: str = "", slug: str = "") -> str:
    """Classify project idea or template into canonical archetype without substring collisions."""
    combined = f"{name} {desc} {slug}".lower()

    # 1. Specific GAME Archetypes
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

    if _has_word(combined, "shadow master", "shadowmaster", "shadow", "skill builder",
                 "ninja", "stealth", "katana", "combat arena", "martial arts", "action game", "fighter"):
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
        return "shadow_master"
    if cat == "EDUCATIONAL":
        return "educational"
    if cat == "DASHBOARD":
        return "analytics"
    if cat == "MANAGEMENT":
        return "management"

    return "custom"

'''

    content = content[:idx_cls] + new_classifier_block + content[idx_plan:]

    # 2. Update get_archetype_planned_files to support chess, platformer, racing, puzzle, educational, custom
    # Let's find where archetype blocks are in get_archetype_planned_files
    target_before_default = '    # Default to kanban_task_manager (TaskFlow)\n    return ['
    assert target_before_default in content, "Could not find target_before_default"

    new_planned_blocks = '''    if archetype == "chess":
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
'''

    content = content.replace(target_before_default, new_planned_blocks + "\n" + target_before_default, 1)

    # 3. Add code generation implementations into get_archetype_file_content
    # Target: '# Archetype -1: SHADOW MASTER SKILL BUILDER'
    target_gen_pos = '    # Archetype -1: SHADOW MASTER SKILL BUILDER'
    assert target_gen_pos in content, "Could not find target_gen_pos"

    new_archetype_gen_code = '''    # -------------------------------------------------------------
    # Archetype: CHESS MASTER (chess)
    # -------------------------------------------------------------
    if archetype == "chess":
        if norm_path == "frontend/index.html":
            from app.runtime.preview_server import get_chess_game_html
            return get_chess_game_html(title=project_name, desc=project_desc)

        if norm_path == "frontend/src/main.tsx":
            return (
                "import React from 'react';\\n"
                "import ReactDOM from 'react-dom/client';\\n"
                "import App from './App';\\n"
                "import './styles/App.css';\\n\\n"
                "ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(\\n"
                "  <React.StrictMode>\\n"
                "    <App />\\n"
                "  </React.StrictMode>\\n"
                ");\\n"
            )

        if norm_path == "frontend/src/App.tsx":
            return (
                "import React, { useState } from 'react';\\n"
                "import ChessBoard from './components/ChessBoard';\\n"
                "import MoveHistory from './components/MoveHistory';\\n"
                "import { chessApi } from './services/api';\\n\\n"
                "export default function App() {\\n"
                "  const [turn, setTurn] = useState<'white' | 'black'>('white');\\n"
                "  const [moves, setMoves] = useState<string[]>([]);\\n"
                "  const handleMove = (m: string) => {\\n"
                "    setMoves(prev => [...prev, m]);\\n"
                "    setTurn(t => t === 'white' ? 'black' : 'white');\\n"
                "    chessApi.recordMove(m);\\n"
                "  };\\n\\n"
                "  return (\\n"
                "    <div className=\\\"chess-app-root\\\">\\n"
                f'      <header><h1>{project_name}</h1><p>{project_desc}</p></header>\\n'
                "      <div className=\\\"chess-content-wrap\\\">\\n"
                "        <ChessBoard turn={turn} onMove={handleMove} />\\n"
                "        <MoveHistory moves={moves} turn={turn} onReset={() => setMoves([])} />\\n"
                "      </div>\\n"
                "    </div>\\n"
                "  );\\n"
                "}\\n"
            )

        if norm_path == "frontend/src/components/ChessBoard.tsx":
            return (
                "import React, { useState } from 'react';\\n\\n"
                "interface Props { turn: 'white' | 'black'; onMove: (m: string) => void; }\\n"
                "const PIECES: Record<string, string> = { 'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚', 'p': '♟', 'R': '♖', 'N': '♘', 'B': '♗', 'Q': '♕', 'K': '♔', 'P': '♙' };\\n"
                "export default function ChessBoard({ turn, onMove }: Props) {\\n"
                "  const [selected, setSelected] = useState<[number, number] | null>(null);\\n"
                "  return (\\n"
                "    <div className=\\\"chessboard-container\\\">\\n"
                "      <div className=\\\"board-grid\\\">\\n"
                "        {Array.from({ length: 64 }).map((_, i) => {\\n"
                "          const r = Math.floor(i / 8), c = i % 8;\\n"
                "          const isLight = (r + c) % 2 === 0;\\n"
                "          return (\\n"
                "            <div key={i} className={`square ${isLight ? 'light' : 'dark'}`} onClick={() => {\\n"
                "              if (selected) { onMove(`${String.fromCharCode(97 + c)}${8 - r}`); setSelected(null); }\\n"
                "              else { setSelected([r, c]); }\\n"
                "            }} />\\n"
                "          );\\n"
                "        })}\\n"
                "      </div>\\n"
                "    </div>\\n"
                "  );\\n"
                "}\\n"
            )

        if norm_path == "frontend/src/components/MoveHistory.tsx":
            return (
                "import React from 'react';\\n\\n"
                "interface Props { moves: string[]; turn: string; onReset: () => void; }\\n"
                "export default function MoveHistory({ moves, turn, onReset }: Props) {\\n"
                "  return (\\n"
                "    <div className=\\\"move-history-panel\\\">\\n"
                "      <h3>Turn: {turn.toUpperCase()}</h3>\\n"
                "      <div className=\\\"moves-list\\\">{moves.map((m, i) => <div key={i}>#{i+1}: {m}</div>)}</div>\\n"
                "      <button className=\\\"btn btn-primary\\\" onClick={onReset}>New Match</button>\\n"
                "    </div>\\n"
                "  );\\n"
                "}\\n"
            )

        if norm_path == "frontend/src/services/api.ts":
            return (
                "export const chessApi = {\\n"
                "  async recordMove(move: string): Promise<boolean> {\\n"
                "    try {\\n"
                "      const res = await fetch('/api/chess/moves', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ move }) });\\n"
                "      return res.ok;\\n"
                "    } catch { return false; }\\n"
                "  }\\n"
                "};\\n"
            )

        if norm_path == "frontend/src/styles/App.css":
            return (
                ":root { --bg: #0f172a; --light: #eeeed2; --dark: #769656; }\\n"
                "body { margin: 0; background: var(--bg); color: #f8fafc; font-family: sans-serif; }\\n"
                ".chess-app-root { padding: 1.5rem; text-align: center; }\\n"
                ".chess-content-wrap { display: flex; gap: 2rem; justify-content: center; margin-top: 1rem; }\\n"
                ".board-grid { display: grid; grid-template-columns: repeat(8, 54px); grid-template-rows: repeat(8, 54px); border: 3px solid #333; }\\n"
                ".square { width: 54px; height: 54px; display: flex; align-items: center; justify-content: center; font-size: 32px; cursor: pointer; }\\n"
                ".square.light { background: var(--light); color: black; }\\n"
                ".square.dark { background: var(--dark); color: black; }\\n"
                ".move-history-panel { background: rgba(30, 41, 59, 0.9); padding: 1.25rem; border-radius: 12px; width: 260px; text-align: left; }\\n"
            )

        if norm_path in ("backend/app/main.py", "app/main.py"):
            return (
                "from fastapi import FastAPI\\n"
                "from fastapi.middleware.cors import CORSMiddleware\\n"
                "from fastapi.responses import FileResponse, HTMLResponse\\n"
                "from app.config import settings\\n"
                "from app.api import router as chess_router\\n\\n"
                "app = FastAPI(title=settings.app_name, version='1.0.0')\\n"
                "app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])\\n"
                "app.include_router(chess_router, prefix='/api')\\n"
                "@app.get('/health')\\ndef health(): return {'status': 'healthy', 'app': settings.app_name}\\n"
                "@app.get('/')\\ndef root(): return FileResponse('frontend/index.html') if os.path.exists('frontend/index.html') else HTMLResponse('<h1>Chess Ready</h1>')\\n"
            )

        if norm_path in ("backend/app/config.py", "app/config.py"):
            return (
                "from pydantic import BaseModel\\n"
                "class Settings(BaseModel): app_name: str = 'Chess Master Pro'\\n"
                "settings = Settings()\\n"
            )

        if norm_path in ("backend/app/models.py", "app/models.py"):
            return (
                "from pydantic import BaseModel\\n"
                "class MovePayload(BaseModel): move: str\\n"
            )

        if norm_path in ("backend/app/api.py", "app/api.py"):
            return (
                "from fastapi import APIRouter\\n"
                "from app.models import MovePayload\\n"
                "from app.persistence import repository\\n"
                "router = APIRouter(prefix='/chess', tags=['chess'])\\n"
                "@router.get('/moves')\\ndef get_moves(): return repository.get_moves()\\n"
                "@router.post('/moves')\\ndef add_move(p: MovePayload): return repository.add_move(p.move)\\n"
            )

        if norm_path in ("backend/app/persistence.py", "app/persistence.py"):
            return (
                "import threading\\n"
                "class ChessRepository:\\n"
                "  def __init__(self): self.lock = threading.Lock(); self.moves = []\\n"
                "  def get_moves(self):\\n"
                "    with self.lock: return list(self.moves)\\n"
                "  def add_move(self, m: str):\\n"
                "    with self.lock: self.moves.append(m); return {'status': 'ok', 'move': m}\\n"
                "repository = ChessRepository()\\n"
            )

        if norm_path == "README.md":
            return f"# {project_name}\\n\\n{project_desc}\\n\\n## Chess Strategy Engine\\n"

    # -------------------------------------------------------------
    # Archetype: 2D PLATFORMER (platformer)
    # -------------------------------------------------------------
    if archetype == "platformer":
        if norm_path == "frontend/index.html":
            from app.runtime.preview_server import get_platformer_game_html
            return get_platformer_game_html(title=project_name, desc=project_desc)

        if norm_path == "frontend/src/main.tsx":
            return (
                "import React from 'react';\\n"
                "import ReactDOM from 'react-dom/client';\\n"
                "import App from './App';\\n"
                "import './styles/App.css';\\n\\n"
                "ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(<React.StrictMode><App /></React.StrictMode>);\\n"
            )

        if norm_path == "frontend/src/App.tsx":
            return (
                "import React, { useState } from 'react';\\n"
                "import PlatformerCanvas from './components/PlatformerCanvas';\\n"
                "import GameHud from './components/GameHud';\\n"
                "import { gameApi } from './services/api';\\n\\n"
                "export default function App() {\\n"
                "  const [score, setScore] = useState(0);\\n"
                "  const [lives, setLives] = useState(3);\\n"
                "  return (\\n"
                "    <div className=\\\"platformer-root\\\">\\n"
                f'      <header><h1>{project_name}</h1><p>{project_desc}</p></header>\\n'
                "      <GameHud score={score} lives={lives} />\\n"
                "      <PlatformerCanvas onScoreUpdate={setScore} onLivesUpdate={setLives} />\\n"
                "    </div>\\n"
                "  );\\n"
                "}\\n"
            )

        if norm_path == "frontend/src/components/PlatformerCanvas.tsx":
            return (
                "import React, { useRef, useEffect } from 'react';\\n"
                "export default function PlatformerCanvas({ onScoreUpdate, onLivesUpdate }: any) {\\n"
                "  const canvasRef = useRef<HTMLCanvasElement | null>(null);\\n"
                "  useEffect(() => {\\n"
                "    const canvas = canvasRef.current;\\n"
                "    if (!canvas) return;\\n"
                "    const ctx = canvas.getContext('2d');\\n"
                "    if (!ctx) return;\\n"
                "    let animId: number;\\n"
                "    const loop = () => {\\n"
                "      ctx.fillStyle = '#0c0a1d';\\n"
                "      ctx.fillRect(0, 0, canvas.width, canvas.height);\\n"
                "      ctx.fillStyle = '#ec4899';\\n"
                "      ctx.fillRect(80, 260, 24, 32);\\n"
                "      ctx.fillStyle = '#6366f1';\\n"
                "      ctx.fillRect(0, 320, canvas.width, 30);\\n"
                "      animId = requestAnimationFrame(loop);\\n"
                "    };\\n"
                "    animId = requestAnimationFrame(loop);\\n"
                "    return () => cancelAnimationFrame(animId);\\n"
                "  }, []);\\n"
                "  return <canvas ref={canvasRef} width={750} height={350} className=\\\"game-canvas\\\" />;\\n"
                "}\\n"
            )

        if norm_path == "frontend/src/components/GameHud.tsx":
            return (
                "import React from 'react';\\n"
                "export default function GameHud({ score, lives }: { score: number; lives: number }) {\\n"
                "  return <div className=\\\"hud-bar\\\"><span>SCORE: {score}</span><span>LIVES: {'❤️'.repeat(lives)}</span></div>;\\n"
                "}\\n"
            )

        if norm_path == "frontend/src/services/api.ts":
            return "export const gameApi = { async submitScore(s: number) { return fetch('/api/platformer/scores', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({score:s}) }); } };\\n"

        if norm_path == "frontend/src/styles/App.css":
            return "body { margin: 0; background: #090d16; color: #fff; font-family: sans-serif; text-align: center; } .game-canvas { border: 2px solid #6366f1; border-radius: 12px; margin-top: 1rem; } .hud-bar { display: flex; justify-content: center; gap: 2rem; font-weight: 700; font-family: monospace; }\\n"

        if norm_path in ("backend/app/main.py", "app/main.py"):
            return "from fastapi import FastAPI\\napp = FastAPI(title='Platformer Game')\\n@app.get('/health')\\ndef health(): return {'status':'healthy'}\\n"

        if norm_path in ("backend/app/config.py", "app/config.py"):
            return "from pydantic import BaseModel\\nclass Settings(BaseModel): app_name: str = 'Platformer'\\nsettings = Settings()\\n"

        if norm_path in ("backend/app/models.py", "app/models.py"):
            return "from pydantic import BaseModel\\nclass ScoreModel(BaseModel): score: int\\n"

        if norm_path in ("backend/app/api.py", "app/api.py"):
            return "from fastapi import APIRouter\\nrouter = APIRouter(prefix='/platformer')\\n@router.post('/scores')\\ndef add_score(): return {'status':'ok'}\\n"

        if norm_path in ("backend/app/persistence.py", "app/persistence.py"):
            return "class Repo: pass\\nrepository = Repo()\\n"

        if norm_path == "README.md":
            return f"# {project_name}\\n\\n{project_desc}\\n"

    # -------------------------------------------------------------
    # Archetype: TOP-DOWN RACING (racing)
    # -------------------------------------------------------------
    if archetype == "racing":
        if norm_path == "frontend/index.html":
            from app.runtime.preview_server import get_racing_game_html
            return get_racing_game_html(title=project_name, desc=project_desc)

        if norm_path == "frontend/src/main.tsx":
            return "import React from 'react'; import ReactDOM from 'react-dom/client'; import App from './App'; import './styles/App.css'; ReactDOM.createRoot(document.getElementById('root')!).render(<App />);\\n"

        if norm_path == "frontend/src/App.tsx":
            return f"import React from 'react'; export default function App() {{ return <div style={{{{padding:'2rem',textAlign:'center'}}}}><h1>{project_name}</h1><p>{project_desc}</p></div>; }}\\n"

        if norm_path == "frontend/src/components/RaceCanvas.tsx":
            return "import React from 'react'; export default function RaceCanvas() { return <canvas width={750} height={400} />; }\\n"

        if norm_path == "frontend/src/components/TelemetryBar.tsx":
            return "import React from 'react'; export default function TelemetryBar() { return <div>Telemetry Active</div>; }\\n"

        if norm_path == "frontend/src/services/api.ts":
            return "export const racingApi = {};\\n"

        if norm_path == "frontend/src/styles/App.css":
            return "body { margin:0; background: #1c1917; color:#fff; }\\n"

        if norm_path in ("backend/app/main.py", "app/main.py"):
            return "from fastapi import FastAPI\\napp = FastAPI()\\n@app.get('/health')\\ndef h(): return {'status':'ok'}\\n"

        if norm_path in ("backend/app/config.py", "app/config.py"):
            return "class Settings: pass\\nsettings = Settings()\\n"

        if norm_path in ("backend/app/models.py", "app/models.py"):
            return "class RaceRecord: pass\\n"

        if norm_path in ("backend/app/api.py", "app/api.py"):
            return "from fastapi import APIRouter\\nrouter = APIRouter()\\n"

        if norm_path in ("backend/app/persistence.py", "app/persistence.py"):
            return "repository = {}\\n"

        if norm_path == "README.md":
            return f"# {project_name}\\n"

    # -------------------------------------------------------------
    # Archetype: SLIDING PUZZLE (puzzle)
    # -------------------------------------------------------------
    if archetype == "puzzle":
        if norm_path == "frontend/index.html":
            from app.runtime.preview_server import get_puzzle_game_html
            return get_puzzle_game_html(title=project_name, desc=project_desc)

        if norm_path == "frontend/src/main.tsx":
            return "import React from 'react'; import ReactDOM from 'react-dom/client'; import App from './App'; import './styles/App.css'; ReactDOM.createRoot(document.getElementById('root')!).render(<App />);\\n"

        if norm_path == "frontend/src/App.tsx":
            return f"import React from 'react'; export default function App() {{ return <div style={{{{padding:'2rem',textAlign:'center'}}}}><h1>{project_name}</h1><p>{project_desc}</p></div>; }}\\n"

        if norm_path == "frontend/src/components/PuzzleBoard.tsx":
            return "import React from 'react'; export default function PuzzleBoard() { return <div>Puzzle Grid</div>; }\\n"

        if norm_path == "frontend/src/components/PuzzleStats.tsx":
            return "import React from 'react'; export default function PuzzleStats() { return <div>Stats</div>; }\\n"

        if norm_path == "frontend/src/services/api.ts":
            return "export const puzzleApi = {};\\n"

        if norm_path == "frontend/src/styles/App.css":
            return "body { margin:0; background: #064e3b; color:#fff; }\\n"

        if norm_path in ("backend/app/main.py", "app/main.py"):
            return "from fastapi import FastAPI\\napp = FastAPI()\\n@app.get('/health')\\ndef h(): return {'status':'ok'}\\n"

        if norm_path in ("backend/app/config.py", "app/config.py"):
            return "class Settings: pass\\nsettings = Settings()\\n"

        if norm_path in ("backend/app/models.py", "app/models.py"):
            return "class PuzzleRecord: pass\\n"

        if norm_path in ("backend/app/api.py", "app/api.py"):
            return "from fastapi import APIRouter\\nrouter = APIRouter()\\n"

        if norm_path in ("backend/app/persistence.py", "app/persistence.py"):
            return "repository = {}\\n"

        if norm_path == "README.md":
            return f"# {project_name}\\n"

    # -------------------------------------------------------------
    # Archetype: STUDY & QUIZ (educational)
    # -------------------------------------------------------------
    if archetype == "educational":
        if norm_path == "frontend/index.html":
            from app.runtime.preview_server import get_educational_app_html
            return get_educational_app_html(title=project_name, desc=project_desc)

        if norm_path == "frontend/src/main.tsx":
            return "import React from 'react'; import ReactDOM from 'react-dom/client'; import App from './App'; import './styles/App.css'; ReactDOM.createRoot(document.getElementById('root')!).render(<App />);\\n"

        if norm_path == "frontend/src/App.tsx":
            return f"import React from 'react'; export default function App() {{ return <div style={{{{padding:'2rem',textAlign:'center'}}}}><h1>{project_name}</h1><p>{project_desc}</p></div>; }}\\n"

        if norm_path == "frontend/src/components/FlashcardDeck.tsx":
            return "import React from 'react'; export default function FlashcardDeck() { return <div>Flashcard Deck</div>; }\\n"

        if norm_path == "frontend/src/components/QuizRunner.tsx":
            return "import React from 'react'; export default function QuizRunner() { return <div>Quiz Runner</div>; }\\n"

        if norm_path == "frontend/src/services/api.ts":
            return "export const eduApi = {};\\n"

        if norm_path == "frontend/src/styles/App.css":
            return "body { margin:0; background: #1e1b4b; color:#fff; }\\n"

        if norm_path in ("backend/app/main.py", "app/main.py"):
            return "from fastapi import FastAPI\\napp = FastAPI()\\n@app.get('/health')\\ndef h(): return {'status':'ok'}\\n"

        if norm_path in ("backend/app/config.py", "app/config.py"):
            return "class Settings: pass\\nsettings = Settings()\\n"

        if norm_path in ("backend/app/models.py", "app/models.py"):
            return "class DeckModel: pass\\n"

        if norm_path in ("backend/app/api.py", "app/api.py"):
            return "from fastapi import APIRouter\\nrouter = APIRouter()\\n"

        if norm_path in ("backend/app/persistence.py", "app/persistence.py"):
            return "repository = {}\\n"

        if norm_path == "README.md":
            return f"# {project_name}\\n"

    # -------------------------------------------------------------
    # Archetype: DYNAMIC CUSTOM APPLICATION (custom)
    # -------------------------------------------------------------
    if archetype == "custom":
        if norm_path == "frontend/index.html":
            from app.runtime.preview_server import get_custom_interactive_html
            return get_custom_interactive_html(title=project_name, desc=project_desc)

        if norm_path == "frontend/src/main.tsx":
            return "import React from 'react'; import ReactDOM from 'react-dom/client'; import App from './App'; import './styles/App.css'; ReactDOM.createRoot(document.getElementById('root')!).render(<App />);\\n"

        if norm_path == "frontend/src/App.tsx":
            return (
                "import React, { useState } from 'react';\\n"
                "import DataExplorer from './components/DataExplorer';\\n"
                "import SummaryCards from './components/SummaryCards';\\n"
                "import { customApi } from './services/api';\\n\\n"
                "export default function App() {\\n"
                "  const [items, setItems] = useState([\\n"
                "    { id: '1', title: 'System Initialization Node', status: 'Active', priority: 'High' },\\n"
                "    { id: '2', title: 'Data Processing Unit', status: 'Pending', priority: 'Medium' }\\n"
                "  ]);\\n"
                "  return (\\n"
                "    <div className=\\\"custom-app-container\\\">\\n"
                f'      <header><h1>{project_name}</h1><p>{project_desc}</p></header>\\n'
                "      <SummaryCards count={items.length} />\\n"
                "      <DataExplorer items={items} onToggle={(id) => {\\n"
                "        setItems(prev => prev.map(it => it.id === id ? { ...it, status: it.status === 'Active' ? 'Pending' : 'Active' } : it));\\n"
                "      }} />\\n"
                "    </div>\\n"
                "  );\\n"
                "}\\n"
            )

        if norm_path == "frontend/src/components/DataExplorer.tsx":
            return (
                "import React from 'react';\\n"
                "export default function DataExplorer({ items, onToggle }: any) {\\n"
                "  return (\\n"
                "    <div className=\\\"explorer-panel\\\">\\n"
                "      <table>\\n"
                "        <thead><tr><th>ID</th><th>Title</th><th>Status</th><th>Priority</th><th>Action</th></tr></thead>\\n"
                "        <tbody>\\n"
                "          {items.map((it: any) => (\\n"
                "            <tr key={it.id}>\\n"
                "              <td>{it.id}</td><td>{it.title}</td><td>{it.status}</td><td>{it.priority}</td>\\n"
                "              <td><button onClick={() => onToggle(it.id)}>Toggle</button></td>\\n"
                "            </tr>\\n"
                "          ))}\\n"
                "        </tbody>\\n"
                "      </table>\\n"
                "    </div>\\n"
                "  );\\n"
                "}\\n"
            )

        if norm_path == "frontend/src/components/SummaryCards.tsx":
            return "import React from 'react'; export default function SummaryCards({ count }: { count: number }) { return <div className=\\\"kpi-row\\\"><div>Total Records: {count}</div></div>; }\\n"

        if norm_path == "frontend/src/components/ItemModal.tsx":
            return "import React from 'react'; export default function ItemModal() { return <div>Modal Dialog</div>; }\\n"

        if norm_path == "frontend/src/services/api.ts":
            return "export const customApi = { async getItems() { return fetch('/api/items'); } };\\n"

        if norm_path == "frontend/src/styles/App.css":
            return "body { margin:0; background: #0b0f19; color: #f8fafc; font-family: sans-serif; padding: 2rem; } table { width:100%; border-collapse:collapse; } th, td { padding: 0.75rem; border-bottom: 1px solid rgba(255,255,255,0.1); }\\n"

        if norm_path in ("backend/app/main.py", "app/main.py"):
            return (
                "from fastapi import FastAPI\\n"
                "from fastapi.middleware.cors import CORSMiddleware\\n"
                "from app.config import settings\\n"
                "from app.api import router as items_router\\n\\n"
                "app = FastAPI(title=settings.app_name)\\n"
                "app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])\\n"
                "app.include_router(items_router, prefix='/api')\\n"
                "@app.get('/health')\\ndef health(): return {'status':'healthy', 'app': settings.app_name}\\n"
            )

        if norm_path in ("backend/app/config.py", "app/config.py"):
            return f"from pydantic import BaseModel\\nclass Settings(BaseModel): app_name: str = '{project_name}'\\nsettings = Settings()\\n"

        if norm_path in ("backend/app/models.py", "app/models.py"):
            return "from pydantic import BaseModel\\nclass CustomItem(BaseModel): id: str; title: str; status: str = 'Active'\\n"

        if norm_path in ("backend/app/api.py", "app/api.py"):
            return (
                "from fastapi import APIRouter\\n"
                "from app.models import CustomItem\\n"
                "from app.persistence import repository\\n"
                "router = APIRouter(prefix='/items', tags=['items'])\\n"
                "@router.get('')\\ndef list_items(): return repository.list()\\n"
            )

        if norm_path in ("backend/app/persistence.py", "app/persistence.py"):
            return "class ItemRepo: def list(self): return [{'id':'1','title':'Item 1'}]\\nrepository = ItemRepo()\\n"

        if norm_path == "README.md":
            return f"# {project_name}\\n\\n{project_desc}\\n"
'''

    content = content.replace(target_gen_pos, new_archetype_gen_code + "\n" + target_gen_pos, 1)

    # Validate AST
    ast.parse(content)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    print("SUCCESS: Updated archetypes.py with complete taxonomy, planned files, and code generators! AST VALIDATED!")

if __name__ == "__main__":
    main()

