from pathlib import Path

p = Path("backend/app/agents/code_generation/archetypes.py")
content = p.read_text(encoding="utf-8")

# 1. Update ARCHETYPE_TEMPLATES
ARCHETYPE_TEMPLATES_OLD = """    "custom": {"name": "Interactive Application Dashboard", "category": "CUSTOM"},
}"""

ARCHETYPE_TEMPLATES_NEW = """    "sky_strike": {"name": "Sky Strike Dogfight Simulator", "category": "GAME"},
    "inventory": {"name": "Apex Inventory & Warehouse Manager", "category": "BUSINESS"},
    "lms": {"name": "SkillForge Online Academy", "category": "EDUCATIONAL"},
    "custom": {"name": "Interactive Application Dashboard", "category": "CUSTOM"},
}"""

if ARCHETYPE_TEMPLATES_OLD in content:
    content = content.replace(ARCHETYPE_TEMPLATES_OLD, ARCHETYPE_TEMPLATES_NEW, 1)

# 2. Update detect_project_archetype
DETECT_OLD = """    # 1. Specific GAME Archetypes
    if _has_word(combined, "carrom", "carromboard", "carrom board", "striker", "carrom master"):
        return "carrom\""""

DETECT_NEW = """    # 1. Specific GAME Archetypes
    if _has_word(combined, "sky strike", "skystrike", "aerial combat", "dogfight", "fighter jet", "flight simulator", "space battle", "air combat"):
        return "sky_strike"

    if _has_word(combined, "carrom", "carromboard", "carrom board", "striker", "carrom master"):
        return "carrom\""""

if DETECT_OLD in content:
    content = content.replace(DETECT_OLD, DETECT_NEW, 1)

# 3. Add inventory and lms checks in detect_project_archetype
DETECT_BIZ_OLD = """    # 6. EVENTHUB & TASKFLOW
    if _has_word(combined, "eventhub", "event booking", "ticket booking", "conference registration", "summit booking"):
        return "eventhub\""""

DETECT_BIZ_NEW = """    # 5.5 INVENTORY & LMS
    if _has_word(combined, "inventory", "warehouse", "stock", "sku", "supply chain", "stock adjustment", "replenishment"):
        return "inventory"

    if _has_word(combined, "lms", "learning management", "online academy", "course platform", "curriculum", "courses", "lessons", "student progress"):
        return "lms"

    # 6. EVENTHUB & TASKFLOW
    if _has_word(combined, "eventhub", "event booking", "ticket booking", "conference registration", "summit booking"):
        return "eventhub\""""

if DETECT_BIZ_OLD in content:
    content = content.replace(DETECT_BIZ_OLD, DETECT_BIZ_NEW, 1)

p.write_text(content, encoding="utf-8")
print("archetypes.py successfully updated with sky_strike, inventory, and lms!")
