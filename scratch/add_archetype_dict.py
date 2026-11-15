import ast
from pathlib import Path

p = Path("backend/app/agents/code_generation/archetypes.py")
c = p.read_text(encoding="utf-8")

dict_str = '''
ARCHETYPE_TEMPLATES = {
    "shadow_master": {"name": "Shadow Master Skill Builder", "category": "GAME"},
    "carrom": {"name": "Carrom Master", "category": "GAME"},
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
    "custom": {"name": "Interactive Application Dashboard", "category": "CUSTOM"},
}
'''

idx = c.find("import re")
c = c[:idx + len("import re")] + "\n" + dict_str + "\n" + c[idx + len("import re"):]

ast.parse(c, filename="archetypes.py")
p.write_text(c, encoding="utf-8")
print("SUCCESS: Added ARCHETYPE_TEMPLATES to archetypes.py!")

