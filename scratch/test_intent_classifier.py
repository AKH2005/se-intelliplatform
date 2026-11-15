import re

def _has_word(text: str, *words: str) -> bool:
    """Check if any of the given words or multi-word phrases appear with word boundaries."""
    for w in words:
        escaped = re.escape(w.lower())
        pattern = r'(?:\b|_)' + escaped + r'(?:\b|_)'
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False

def classify_application_category(name: str = "", desc: str = "", slug: str = "") -> str:
    combined = f"{name} {desc} {slug}".lower()

    # Exclusions first: "production management" is MANAGEMENT, not e-commerce
    # "productivity" is BUSINESS, not e-commerce
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

    # Business / E-commerce / Task detection
    if _has_word(combined, "shop", "store", "storefront", "ecommerce", "e-commerce", "cart",
                 "checkout", "shopping", "merchandise", "catalog", "marketplace", "retail"):
        return "BUSINESS"

    if _has_word(combined, "kanban", "taskflow", "task manager", "tasks", "task", "todo",
                 "to-do", "backlog", "scrum", "sprint", "project tracker", "eventhub",
                 "event booking", "conference", "ticket booking"):
        return "BUSINESS"

    return "CUSTOM"

def detect_project_archetype(name: str = "", desc: str = "", slug: str = "") -> str:
    combined = f"{name} {desc} {slug}".lower()

    # 1. GAMES - Specific game types take precedence over generic 'game'
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

    # 6. TASKFLOW & EVENTHUB
    if _has_word(combined, "eventhub", "event booking", "ticket booking", "conference registration", "summit booking"):
        return "eventhub"

    if _has_word(combined, "kanban", "taskflow", "task manager", "tasks", "todo", "to-do",
                 "backlog", "scrum", "sprint board", "productivity application", "productivity app", "project tracker"):
        return "taskflow"

    # Fallback to general category games if still unclassified
    if classify_application_category(name, desc, slug) == "GAME":
        # Check if generic board game
        if _has_word(combined, "board game"):
            return "chess"  # Default board game archetype
        return "shadow_master"  # Default action game archetype

    return "custom"

# Test suite
test_cases = [
    ("Carrom Master", "Realistic 2D carrom physics", "carrom", "GAME"),
    ("Arcade Snake", "Retro 2D slither arcade", "snake_game", "GAME"),
    ("Chess Master Pro", "Play chess with AI and moves history", "chess", "GAME"),
    ("Shadow Master Skill Builder", "Custom skills combat game", "shadow_master", "GAME"),
    ("Skyline Jump Platformer", "2D side-scrolling platformer with coins", "platformer", "GAME"),
    ("Turbo Nitro Racing", "High speed track circuit time trial", "racing", "GAME"),
    ("Tile Shift Puzzle", "15-puzzle sliding tile game", "puzzle", "GAME"),
    ("StudyDeck Flashcards & Quiz", "Interactive learning flashcard suite", "educational", "EDUCATIONAL"),
    ("Executive Analytics", "Revenue and KPI dashboard", "analytics", "DASHBOARD"),
    ("TeamConnect Directory", "Employee staff roster management", "management", "MANAGEMENT"),
    ("Production Management System", "Factory floor operations management", "management", "MANAGEMENT"),
    ("Productivity Application", "Task tracker and personal todo", "taskflow", "BUSINESS"),
    ("ShopSphere Storefront", "Online e-commerce product catalog with cart", "ecommerce", "BUSINESS"),
    ("EventHub Summit", "Conference ticket booking", "eventhub", "BUSINESS"),
    ("Medical Prescription Vault", "Custom clinical record archive", "custom", "CUSTOM"),
    ("Board Game Arena", "Classic strategic board game", "chess", "GAME"),
    ("Canvas Art Studio", "Drawing canvas tool", "custom", "CUSTOM"),
]

passed = 0
for name, desc, exp_arch, exp_cat in test_cases:
    arch = detect_project_archetype(name, desc)
    cat = classify_application_category(name, desc)
    assert arch == exp_arch, f"FAILED ARCHETYPE for '{name}': Expected {exp_arch}, got {arch}"
    assert cat == exp_cat, f"FAILED CATEGORY for '{name}': Expected {exp_cat}, got {cat}"
    passed += 1
    print(f"PASS: '{name}' -> Category: {cat}, Archetype: {arch}")

print(f"\nALL {passed} INTENT CLASSIFICATION TEST CASES PASSED 100%!")

